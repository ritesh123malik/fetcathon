"""Safe connectivity diagnostics: never prints keys or response bodies."""

import asyncio

import httpx

from backend.config import settings
from backend.intent import extract_intent
from backend.service import DomainError


async def main():
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            "https://agentverse.ai/v1/search/agents",
            headers={"Authorization": f"Bearer {settings.agentverse_api_key}"},
            json={"search_text": "supplyrescue", "limit": 1},
        )
        print(f"Agentverse Search API: HTTP {response.status_code}")
    try:
        result, source = await extract_intent(
            "60 notebooks and 60 pens under INR 4500 within 24 hours", settings
        )
        print(
            f"ASI:One extraction: {source}, {len(result.items)} products, budget {result.budget_paise} paise"
        )
    except DomainError as error:
        print(f"ASI:One extraction failed: {error.message}")
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
