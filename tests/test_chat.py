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
