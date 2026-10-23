import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from agents.workflow import ChatWorkflow
from backend.api import create_app
from backend.catalogue import SCENARIOS
from backend.config import Settings
from backend.intent import extract_intent
from backend.models import Requirements
from backend.service import DomainError, SupplyService


def test_memory_survives_restart_and_is_private(service):
    async def suppliers():
        return service.suppliers()

    async def run():
        workflow = ChatWorkflow(service, Settings(_env_file=None))
        with patch("agents.workflow.extract_intent", new_callable=AsyncMock) as extract:
            extract.side_effect = DomainError("What is your budget and deadline?")
            await workflow.handle("I need three pens", "alice", suppliers)
        workflow = ChatWorkflow(SupplyService(service.db), Settings(_env_file=None))
        with patch("agents.workflow.extract_intent", new_callable=AsyncMock) as extract:
            extract.return_value = (
                Requirements(
                    items=[{"product": "pen", "quantity": 3}],
                    budget_paise=2000,
                    deadline_hours=1 / 3,
                ),
                "asi1",
            )
            reply = await workflow.handle("20 INR in 20 minutes", "alice", suppliers)
            assert extract.call_args.args[2][0]["content"] == "I need three pens"
            assert "No complete plan" in reply.text()
        assert service.conversation("bob") == []
        await workflow.handle("start", "alice", suppliers)
        assert service.conversation("alice") == []

    asyncio.run(run())


def test_expanded_scenarios_and_minutes(service):
    assert len(service.suppliers()) == 6
    for prompt in SCENARIOS.values():
        requirements, _ = asyncio.run(extract_intent(prompt, Settings(_env_file=None)))
        assert service.quote(requirements, "alice")["options"]
    requirements, _ = asyncio.run(
        extract_intent("2 pens under INR 20 within 20 minutes", Settings(_env_file=None))
    )
    assert requirements.deadline_hours == pytest.approx(1 / 3)
    assert service.quote(requirements, "alice")["options"] == []


def test_tracking_transitions_ownership_and_inventory(service, requirements):
    quote = service.quote(requirements, "alice")
    order = service.confirm(quote["id"], "option-1", "alice")["order"]
    oid = order["id"]
    supplier = order["payload"]["reservations"][0]["supplier_id"]
    with pytest.raises(DomainError):
        service.tracking(oid, "bob")
    with pytest.raises(DomainError):
        service.advance_shipment(oid, "alice", supplier, "delivered")
    service.advance_shipment(oid, "alice", supplier, "packing", "Packed by operator")
    service.advance_shipment(oid, "alice", supplier, "packing", "Duplicate")
    report = service.tracking(oid, "alice")
    shipment = next(s for s in report["shipments"] if s["supplier_id"] == supplier)
    assert len(shipment["history"]) == 2
    before = service.suppliers()
    service.advance_shipment(oid, "alice", supplier, "dispatched")
    with pytest.raises(DomainError, match="dispatched"):
        service.cancel_order(oid, "alice")
    assert service.suppliers() == before
    for shipment in service.tracking(oid, "alice")["shipments"]:
        for stage in (
            ["delivered"]
            if shipment["status"] == "dispatched"
            else ["packing", "dispatched", "delivered"]
        ):
            service.advance_shipment(oid, "alice", shipment["supplier_id"], stage)
    assert service.tracking(oid, "alice")["status"] == "delivered"
    service.db.initialize(seed=True)
    assert service.tracking(oid, "alice")["status"] == "delivered"
    assert service.suppliers() == before


def test_cancelled_tracking_cannot_advance(service, requirements):
    q = service.quote(requirements, "alice")
    o = service.confirm(q["id"], "option-1", "alice")["order"]
    service.cancel_order(o["id"], "alice")
    assert service.tracking(o["id"], "alice")["status"] == "cancelled"
    with pytest.raises(DomainError):
        service.advance_shipment(
            o["id"], "alice", o["payload"]["reservations"][0]["supplier_id"], "packing"
        )


def test_tracking_api_and_chat(tmp_path, requirements):
    app = create_app(
        Settings(_env_file=None, database_path=str(tmp_path / "api.db"), admin_api_key="key")
    )
    with TestClient(app) as client:
        service = app.state.service
        q = service.quote(requirements, "chat-owner")
        o = service.confirm(q["id"], "option-1", "chat-owner")["order"]
        route = f"/api/orders/{o['id']}/tracking"
        assert client.get(route).status_code == 401
        headers = {"Authorization": "Bearer key"}
        report = client.get(route, headers=headers).json()
        supplier = report["shipments"][0]["supplier_id"]
        assert (
            client.post(
                f"/api/orders/{o['id']}/shipments/{supplier}",
                headers=headers,
                json={"status": "packing"},
            ).status_code
            == 200
        )
        workflow = ChatWorkflow(service, Settings(_env_file=None))

        async def suppliers():
            return service.suppliers()

        reply = asyncio.run(workflow.handle(f"track {o['id']}", "chat-owner", suppliers))
        assert "packing" in reply.text()
        assert "not live courier GPS" in reply.text()
        private = asyncio.run(workflow.handle(f"track {o['id']}", "other", suppliers))
        assert "not found" in private.text()
        catalogue = asyncio.run(workflow.handle("catalogue", "chat-owner", suppliers))
        assert "Event Essentials" in catalogue.text()


def test_llm_receives_prior_turns_and_fractional_deadline():
    response = AsyncMock()
    response.raise_for_status = lambda: None
    response.json = lambda: {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "items": [{"product": "pen", "quantity": 2}],
                            "budget_paise": 2000,
                            "deadline_hours": 1 / 3,
                        }
                    )
                }
            }
        ]
    }
    history = [{"role": "user", "content": "two pens"}]
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=response) as post:
        result, _ = asyncio.run(
            extract_intent(
                "20 INR in 20 minutes", Settings(_env_file=None, asi_one_api_key="test"), history
            )
        )
        assert result.deadline_hours == pytest.approx(1 / 3)
        assert post.call_args.kwargs["json"]["messages"][1] == history[0]
