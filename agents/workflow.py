import json
import re
from collections.abc import Awaitable, Callable
from decimal import Decimal

from pydantic import ValidationError
from uagents_core.contrib.protocols.chat import ChatMessage, TextContent

from agents.cards import options_card, receipt_message, request_form, review_card
from backend.catalogue import PRODUCTS, SCENARIOS
from backend.config import Settings
from backend.intent import extract_intent
from backend.models import Requirements
from backend.service import DomainError, SupplyService


def normalize_message(text: str) -> str:
    """Remove routing mentions, not command arguments or card JSON."""
    text = re.sub(r"^\s*(?:@agent1[a-z0-9]+[\s,:;]*)+", "", text, flags=re.I)
    text = re.sub(r"^\s*@SupplyRescue Campus Recovery[\s,:;]*", "", text, flags=re.I)
    return text.strip()


def read_command(text: str) -> str:
    # Exact allowlisted read commands; never infer confirmations or cancellations.
    command = text.lower().strip().rstrip(".!?")
    command = re.sub(r"^(?:please\s+)?(?:show(?:\s+me)?|list|view|open)\s+", "", command)
    command = re.sub(r"^(?:the|your|my)\s+", "", command)
    return command.removesuffix(" please").strip()


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
            return await self._handle(normalize_message(text), owner, get_suppliers)
        except (DomainError, ValidationError, ValueError, TypeError, KeyError) as exc:
            message = (
                exc.message
                if isinstance(exc, DomainError)
                else "Please check the card values and try again."
            )
            return ChatMessage(content=[TextContent(type="text", text=message)])

    async def _handle(self, text, owner, get_suppliers):
        command = read_command(text)
        if not text.strip() or command in {"start", "hi", "hello", "help"}:
            self.service.conversation(owner, [])
            return request_form()
        if command in {
            "catalogue",
            "catalog",
            "use cases",
            "examples",
            "suppliers",
            "vendors",
            "products",
        }:
            suppliers = await get_suppliers()
            lines = [
                f"{s['name']} · {s['eta_hours']}h · "
                + ", ".join(
                    f"{i['product']} {i['stock']} available @ INR {i['unit_paise'] / 100:.2f}"
                    for i in s["inventory"]
                )
                for s in suppliers
                if s["active"]
            ]
            return ChatMessage(
                content=[
                    TextContent(
                        type="text",
                        text="Demo supplier catalogue (no real merchants):\n"
                        + "\n".join(lines)
                        + "\nExamples:\n"
                        + "\n".join(SCENARIOS.values()),
                    )
                ]
            )
        tracking_id = re.search(r"\bSR-[A-F0-9]{8}\b", text, re.I)
        if re.search(r"\b(track|tracking|where)\b", text, re.I):
            orders = self.service.orders(owner)
            if not tracking_id and not orders:
                raise DomainError("No orders in this conversation to track yet.")
            report = self.service.tracking(
                tracking_id.group().upper() if tracking_id else orders[0]["id"], owner
            )
            lines = [
                f"{s['supplier_name']}: {s['status']} · estimated delivery {s['estimated_delivery']}"
                + (" · ETA overdue; operator update needed" if s["overdue"] else "")
                + "\n"
                + "\n".join(
                    f"  {h['created_at']}: {h['status']} — {h['note']}" for h in s["history"]
                )
                for s in report["shipments"]
            ]
            return ChatMessage(
                content=[
                    TextContent(
                        type="text",
                        text=f"Tracking {report['order_id']} · {report['status']}\nDemo operator-reported fulfilment; not live courier GPS.\n"
                        + "\n".join(lines),
                    )
                ]
            )
        if command in {"orders", "status"}:
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
                    {"product": p, "quantity": int(action.get(field) or 0)}
                    for p, field in [(p, p + "s") for p in PRODUCTS]
                    if int(action.get(field) or 0) > 0
                ],
                budget_paise=int(Decimal(str(action["budget_rupees"])) * 100),
                deadline_hours=action["deadline_hours"],
                location=action["location"],
            )
        else:
            # Prose source submissions are interpreted by ASI:One then schema-validated.
            history = self.service.conversation(owner)
            turns = [*history, {"role": "user", "content": text[:4000]}]
            self.service.conversation(owner, turns)
            try:
                requirements, _ = await extract_intent(text, self.config, history)
            except DomainError as exc:
                self.service.conversation(
                    owner, [*turns, {"role": "assistant", "content": exc.message}]
                )
                raise
        suppliers = await get_suppliers()
        if not suppliers:
            raise DomainError(
                "Supplier agents did not respond. No order was placed. Please retry shortly."
            )
        quote = self.service.quote(requirements, owner, snapshots=suppliers)
        self.service.conversation(
            owner, [{"role": "user", "content": json.dumps(requirements.model_dump())}]
        )
        self.service.session_quote(owner, quote["id"])
        return options_card(quote)
