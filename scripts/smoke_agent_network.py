"""Real uAgent messages and card round trips on isolated demo data.

This test does not register agents or perform blockchain transactions.
"""

import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
)
from uagents_core.registration import BatchRegistrationPolicy

from agents.runtime import create_network
from backend.config import Settings


class NoRegistration(BatchRegistrationPolicy):
    async def register(self):
        pass

    def add_agent(self, agent_info, identity):
        pass


async def main():
    with tempfile.TemporaryDirectory(prefix="supplyrescue-agent-test-") as directory:
        config = Settings(
            _env_file=None,
            agent_seed=uuid4().hex,
            database_path=str(Path(directory) / "test.sqlite3"),
            agent_mailbox=False,
            agent_endpoint="http://127.0.0.1:8199/submit",
        )
        bureau, coordinator, suppliers = create_network(config, port=8199)
        probe = Agent(
            name="SupplyRescue test client", seed=uuid4().hex, publish_agent_details=False
        )
        done = asyncio.Event()
        errors = []
        phases = []
        protocol = Protocol(spec=chat_protocol_spec)

        @probe.on_event("startup")
        async def start(ctx: Context):
            await ctx.send(
                coordinator.address,
                ChatMessage(
                    content=[
                        TextContent(
                            type="text",
                            text="60 notebooks and 60 pens under INR 4500 within 24 hours",
                        )
                    ]
                ),
            )

        @protocol.on_message(ChatAcknowledgement)
        async def ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
            pass

        @protocol.on_message(ChatMessage)
        async def chat(ctx: Context, sender: str, msg: ChatMessage):
            await ctx.send(sender, ChatAcknowledgement(acknowledged_msg_id=msg.msg_id))
            metadata = next((c.metadata for c in msg.content if c.type == "metadata"), None)
            try:
                if metadata:
                    payload = json.loads(metadata["card_payload"])
                    kind = metadata["card_kind"]
                    phases.append(kind)
                    if kind == "carousel":
                        selection = payload["items"][0]["primary_cta"]["selection"]
                    elif kind == "review":
                        selection = payload["approve_cta"]["selection"]
                    else:
                        raise AssertionError(f"Unexpected card: {kind}")
                    await ctx.send(
                        sender,
                        ChatMessage(content=[TextContent(type="text", text=json.dumps(selection))]),
                    )
                else:
                    assert "Reservation IDs:" in msg.text(), msg.text()
                    phases.append("receipt")
                    done.set()
            except Exception as error:
                errors.append(str(error))
                done.set()

        probe.include(protocol, publish_manifest=False)
        bureau.add(probe)
        bureau._registration_policy = NoRegistration()
        for agent in [coordinator, *suppliers, probe]:
            agent._registration_policy = None
            agent._publish_agent_details = False
        main_task = asyncio.current_task()

        async def stop_when_complete():
            try:
                await asyncio.wait_for(done.wait(), timeout=45)
            except TimeoutError:
                errors.append("The agent round trip timed out.")
            finally:
                main_task.cancel()

        asyncio.create_task(stop_when_complete())
        # Run on the main task: Bureau shutdown cancels remaining tasks, so awaiting a
        # child Bureau from another task would create a cancellation cycle in uAgents.
        await bureau.run_async()
        if errors:
            raise AssertionError(errors)
        assert phases == ["carousel", "review", "receipt"], phases
        print("PASS: coordinator → six supplier uAgents → carousel → review → confirmed receipt")


if __name__ == "__main__":
    with (
        patch.object(Agent, "_update_agent_status", new=AsyncMock()),
        patch.object(Agent, "publish_manifest", new=AsyncMock()),
    ):
        asyncio.run(main())
