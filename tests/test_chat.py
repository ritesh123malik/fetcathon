import asyncio
import json

from agents.workflow import ChatWorkflow, parse_action
from backend.config import Settings


def metadata(message):
    return next(c.metadata for c in message.content if c.type == "metadata")


def test_native_chat_request_review_confirm_cancel(service):
    workflow = ChatWorkflow(service, Settings(_env_file=None))

    async def suppliers():
        return service.suppliers()

    async def run(text):
        return await workflow.handle(text, "chat-owner", suppliers)

    welcome = asyncio.run(run("start"))
    assert metadata(welcome)["card_kind"] == "form"
    plans = asyncio.run(run("60 notebooks and 60 pens under INR 4500 within 24 hours"))
    assert metadata(plans)["card_kind"] == "carousel"
    selection = json.loads(metadata(plans)["card_payload"])["items"][0]["primary_cta"]["selection"]
    review = asyncio.run(run(json.dumps(selection)))
    assert metadata(review)["card_kind"] == "review"
    confirm = json.loads(metadata(review)["card_payload"])["approve_cta"]["selection"]
    receipt = asyncio.run(run(json.dumps(confirm)))
    assert "Reservation IDs:" in receipt.text()
    order = service.orders("chat-owner")[0]
    result = asyncio.run(run(f"cancel {order['id']}"))
    assert "cancelled" in result.text()


def test_selection_does_not_confirm_negated_prose():
    assert parse_action("Do not confirm RQ-0123456789 option-1")["action"] is None
    assert parse_action("User chose confirm RQ-0123456789 option-1")["action"] == "confirm"


def test_missing_agents_does_not_fake_a_quote(service):
    workflow = ChatWorkflow(service, Settings(_env_file=None))

    async def missing():
        return []

    reply = asyncio.run(
        workflow.handle("60 notebooks under INR 4500 within 24 hours", "user", missing)
    )
    assert "did not respond" in reply.text()
    assert service.dashboard("user")["quotes"] == []


def test_mentions_and_read_commands_bypass_llm(service):
    from unittest.mock import AsyncMock, patch

    address = "@agent1qvftq6nwwq7wpl9wd3g70mtyflktwy73afld2tjmqv0uvynrg0d0jcyfg4t"
    workflow = ChatWorkflow(service, Settings(_env_file=None))

    async def suppliers():
        return service.suppliers()

    async def run():
        with patch("agents.workflow.extract_intent", new_callable=AsyncMock) as llm:
            for message in [
                f"{address} catalogue",
                f"{address}\nPlease show me the catalogue.",
                "@SupplyRescue Campus Recovery catalogue",
                "show vendors",
            ]:
                response = await workflow.handle(message, "user", suppliers)
                assert "Demo supplier catalogue" in response.text()
                assert "Event Essentials" in response.text()
            response = await workflow.handle(f"{address} orders", "user", suppliers)
            assert "No orders" in response.text()
            response = await workflow.handle(f"{address} start", "user", suppliers)
            assert metadata(response)["card_kind"] == "form"
            llm.assert_not_awaited()

    asyncio.run(run())


def test_normalization_preserves_transaction_intent():
    from agents.workflow import normalize_message

    payload = '{"action":"confirm","quote_id":"RQ-0123456789","option_id":"option-1"}'
    assert normalize_message(payload) == payload
    assert (
        parse_action(normalize_message("@agent1abcdef Do not confirm RQ-0123456789 option-1"))[
            "action"
        ]
        is None
    )
