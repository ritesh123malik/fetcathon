"""One process, seven distinct uAgent identities, shared transactional inventory authority."""

import asyncio
import hashlib
import json
from pathlib import Path
from uuid import uuid4

from uagents import Agent, Bureau, Context, Model, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    StartSessionContent,
    TextContent,
    chat_protocol_spec,
)

from agents.workflow import ChatWorkflow
from backend.config import settings
from backend.db import Database
from backend.service import SupplyService


class InventoryRequest(Model):
    request_id: str


class InventoryResponse(Model):
    request_id: str
    supplier_id: str
    snapshot_json: str


def create_network(config=settings, port=8100):
    if not config.agent_seed:
        raise RuntimeError("Set a private AGENT_SEED in .env before starting the network.")
    db = Database(config.database_path)
    db.initialize(seed=config.demo_mode)
    service = SupplyService(db)
    coordinator = Agent(
        name="SupplyRescue",
        seed=config.agent_seed,
        mailbox=config.agent_mailbox,
        endpoint=None if config.agent_mailbox else config.agent_endpoint,
        readme_path=str(Path(__file__).with_name("README.md")),
        description="Emergency campus supplies: compare demo supplier quotes, approve and reserve inventory, recover from shortages inside ASI:One.",
        handle_messages_concurrently=True,
    )
    workflow = ChatWorkflow(service, config)
    agents = []
    for supplier in service.suppliers():
        supplier_agent = Agent(
            name=f"SupplyRescue {supplier['name']}",
            seed=f"{config.agent_seed}:{supplier['id']}",
            publish_agent_details=False,
            enable_agent_inspector=False,
        )

        def bind_supplier(agent, supplier_id):
            @agent.on_message(model=InventoryRequest, replies={InventoryResponse})
            async def inventory(ctx: Context, sender: str, msg: InventoryRequest):
                if sender != coordinator.address:
                    ctx.logger.warning("Rejected inventory request from an unknown coordinator")
                    return
                snapshot = next(s for s in service.suppliers() if s["id"] == supplier_id)
                await ctx.send(
                    sender,
                    InventoryResponse(
                        request_id=msg.request_id,
                        supplier_id=supplier_id,
                        snapshot_json=json.dumps(snapshot),
                    ),
                )

        bind_supplier(supplier_agent, supplier["id"])
        agents.append(supplier_agent)
    protocol = Protocol(spec=chat_protocol_spec)

    @protocol.on_message(ChatAcknowledgement)
    async def acknowledge(ctx: Context, sender: str, msg: ChatAcknowledgement):
        pass

    @protocol.on_message(ChatMessage)
    async def chat(ctx: Context, sender: str, msg: ChatMessage):
        await ctx.send(sender, ChatAcknowledgement(acknowledged_msg_id=msg.msg_id))
        text = "\n".join(item.text for item in msg.content if isinstance(item, TextContent))
        if not text and not any(isinstance(item, StartSessionContent) for item in msg.content):
            return
        owner = hashlib.sha256(f"{sender}:{ctx.session}".encode()).hexdigest()

        async def get_suppliers():
            async def fetch(agent):
                correlation = uuid4().hex
                response, _ = await ctx.send_and_receive(
                    agent.address,
                    InventoryRequest(request_id=correlation),
                    response_type=InventoryResponse,
                    timeout=12,
                )
                if isinstance(response, InventoryResponse) and response.request_id == correlation:
                    return json.loads(response.snapshot_json)
                return None

            results = await asyncio.gather(
                *(fetch(agent) for agent in agents), return_exceptions=True
            )
            return [r for r in results if isinstance(r, dict)]

        try:
            response = await workflow.handle(text, owner, get_suppliers)
            await ctx.send(sender, response)
        except Exception:
            ctx.logger.exception("Chat workflow failed")
            await ctx.send(
                sender,
                ChatMessage(
                    content=[
                        TextContent(
                            type="text",
                            text="The request could not complete. Check 'orders' before retrying a confirmation; retries will not create duplicate orders.",
                        )
                    ]
                ),
            )

    coordinator.include(protocol, publish_manifest=True)
    bureau = Bureau(port=port, endpoint=config.agent_endpoint)
    for agent in [coordinator, *agents]:
        bureau.add(agent)
    return bureau, coordinator, agents


if __name__ == "__main__":
    bureau, coordinator, suppliers = create_network()
    print(f"Coordinator address: {coordinator.address}")
    for supplier in suppliers:
        print(f"Supplier identity: {supplier.name} {supplier.address}")
    bureau.run()
