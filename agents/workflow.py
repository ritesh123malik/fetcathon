import json
import re
from collections.abc import Awaitable, Callable
from decimal import Decimal

from pydantic import ValidationError
from uagents_core.contrib.protocols.chat import ChatMessage, TextContent

from agents.cards import options_card, receipt_message, request_form, review_card
from backend.config import Settings
from backend.intent import extract_intent
from backend.models import Requirements
from backend.service import DomainError, SupplyService


def parse_action(text):
    try:
        result = json.loads(text)
        if isinstance(result, dict):
            return result
    except (ValueError, TypeError):
        pass
    # Planner-mediated selections must preserve identifiers and an unambiguous action.
    quote = re.search(r"\bRQ-[A-F0-9]{10}\b", text, re.I)
    option = re.search(r"\boption-[1-3]\b", text, re.I)
    order = re.search(r"\bSR-[A-F0-9]{8}\b", text, re.I)
    negative = re.search(r"\b(?:not|don't|do not|never)\b", text, re.I)
    action = None
    if not negative:
        if re.search(r"\bcancel\b", text, re.I) and order:
            action = "cancel"
        elif re.search(r"\bconfirm\b", text, re.I) and quote and option:
            action = "confirm"
        elif re.search(r"\b(?:review|selected|picked)\b", text, re.I) and quote and option:
            action = "review"
        elif re.search(r"\bback\b", text, re.I) and quote:
            action = "back"
    return {
        "action": action,
        "quote_id": quote.group().upper() if quote else None,
        "option_id": option.group().lower() if option else None,
        "order_id": order.group().upper() if order else None,
    }


class ChatWorkflow:
    def __init__(self, service: SupplyService, config: Settings):
        self.service, self.config = service, config

    async def handle(
        self, text: str, owner: str, get_suppliers: Callable[[], Awaitable[list[dict]]]
    ):
        try:
            return await self._handle(text, owner, get_suppliers)
        except (DomainError, ValidationError, ValueError, TypeError, KeyError) as exc:
            message = (
                exc.message
                if isinstance(exc, DomainError)
                else "Please check the card values and try again."
            )
            return ChatMessage(content=[TextContent(type="text", text=message)])

    async def _handle(self, text, owner, get_suppliers):
        if not text.strip() or text.strip().lower() in {"start", "hi", "hello", "help"}:
            return request_form()
        if text.strip().lower() in {"orders", "status"}:
            orders = self.service.orders(owner)
            if orders:
                return ChatMessage(
                    content=[
                        TextContent(
                            type="text",
                            text="\n".join(
                                f"{o['id']}: {o['status']} · INR {o['payload']['total_paise'] / 100:.2f}"
                                for o in orders
                            ),
                        )
                    ]
                )
            return ChatMessage(
                content=[
                    TextContent(
                        type="text",
                        text="No orders in this conversation yet. Say 'start' to begin.",
                    )
                ]
            )
        action = parse_action(text)
        kind = action.get("action")
        if kind == "cancel" and action.get("order_id"):
            return receipt_message(self.service.cancel_order(action["order_id"], owner))
        if kind in {"review", "confirm", "back"}:
            quote = self.service.get_quote(action.get("quote_id"), owner)
            if kind == "back":
                return options_card(quote)
            option = next((o for o in quote["options"] if o["id"] == action.get("option_id")), None)
            if not option:
                raise DomainError("Choose one of this quote's plans.")
            if kind == "review":
                return review_card(quote, option)
            result = self.service.confirm(quote["id"], option["id"], owner)
            if result["status"] == "confirmed":
                return receipt_message(result["order"])
            self.service.session_quote(owner, result["quote"]["id"])
            return options_card(result["quote"], result["reason"] + " A new approval is required.")
        if kind == "source":
            requirements = Requirements(
                items=[
                    {"product": p, "quantity": int(action.get(field, 0))}
                    for p, field in [
                        ("notebook", "notebooks"),
                        ("pen", "pens"),
                        ("lanyard", "lanyards"),
                    ]
                    if int(action.get(field, 0)) > 0
                ],
                budget_paise=int(Decimal(str(action["budget_rupees"])) * 100),
                deadline_hours=action["deadline_hours"],
                location=action["location"],
            )
        else:
            # Prose source submissions are interpreted by ASI:One then schema-validated.
            requirements, _ = await extract_intent(text, self.config)
        suppliers = await get_suppliers()
        if not suppliers:
            raise DomainError(
                "Supplier agents did not respond. No order was placed. Please retry shortly."
            )
        quote = self.service.quote(requirements, owner, snapshots=suppliers)
        self.service.session_quote(owner, quote["id"])
        return options_card(quote)
