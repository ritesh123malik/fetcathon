"""Register the existing coordinator identity; never print credentials."""

from pathlib import Path

from dotenv import set_key
from uagents_core.identity import Identity
from uagents_core.utils.registration import RegistrationRequestCredentials, register_chat_agent

from backend.config import settings


def main():
    if not settings.agent_seed or not settings.agentverse_api_key:
        raise SystemExit("Set AGENT_SEED and AGENTVERSE_API_KEY in .env first.")
    address = Identity.from_seed(settings.agent_seed, 0).address
    endpoint = (
        "https://agentverse.ai/v1/submit" if settings.agent_mailbox else settings.agent_endpoint
    )
    if not endpoint.startswith("https://"):
        raise SystemExit("Use mailbox mode or a publicly reachable HTTPS endpoint.")
    success = register_chat_agent(
        name="SupplyRescue Campus Recovery",
        endpoint=endpoint,
        active=True,
        credentials=RegistrationRequestCredentials(
            agentverse_api_key=settings.agentverse_api_key, agent_seed_phrase=settings.agent_seed
        ),
        description="Source workshop, conference, classroom and onboarding supplies with six demo vendors. Compare, reserve, recover and track fulfilment in ASI:One.",
        readme=Path("agents/README.md").read_text(),
        starter_prompts=[
            "Find 60 notebooks and 60 pens under INR 4500 within 24 hours.",
            "start",
            "catalogue",
            "track my latest order",
        ],
        metadata={
            "is_public": "True",
            "tags": ["innovationlab", "hackathon", "supplyrescue", "procurement"],
        },
    )
    if not success:
        raise SystemExit("Registration did not succeed.")
    profile = f"https://agentverse.ai/agents/details/{address}/profile"
    set_key(".env", "AGENT_PROFILE_URL", profile)
    print(f"Registered coordinator: {address}")
    print(f"Profile: {profile}")
    print(
        "Keep the worker online; verify mailbox connectivity and ASI:One discovery before submission."
    )


if __name__ == "__main__":
    main()
