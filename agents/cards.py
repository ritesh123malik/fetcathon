"""Native ASI:One cards; no external frontend is needed to complete an order."""

import json

from uagents_core.contrib.protocols.chat import ChatMessage, MetadataContent, TextContent

from backend.catalogue import PRODUCTS


def money(paise):
    return f"INR {paise / 100:,.2f}"


def card(text: str, kind: str, payload: dict):
    return ChatMessage(
        content=[
            TextContent(type="text", text=text),
            MetadataContent(
                type="metadata",
                metadata={
                    "card_protocol_version": "1",
                    "requires_card_interaction": "true",
                    "card_kind": kind,
                    "card_payload": json.dumps(payload),
                },
            ),
        ]
    )


def request_form():
    return card(
        "SupplyRescue coordinates demo workshop, conference, classroom and onboarding supplies. "
        "Say catalogue for products and examples, track ORDER-ID for fulfilment, or start to reset a request. "
        "Enter quantities, budget and deadline. "
        "All confirmations reserve demo inventory; no real purchases or payments occur.",
        "form",
        {
            "title": "Rescue your supply run",
            "fields": [
                *[
                    {
                        "name": p + "s",
                        "kind": "number",
                        "label": p.title() + " quantity (0 if not needed)",
                        "required": False,
                    }
                    for p in PRODUCTS
                ],
                {
                    "name": "budget_rupees",
                    "kind": "number",
                    "label": "Maximum budget in INR",
                    "required": True,
                },
                {
                    "name": "deadline_hours",
                    "kind": "number",
                    "label": "Needed within how many hours?",
                    "required": True,
                },
                {
                    "name": "location",
                    "kind": "text",
                    "label": "Fulfilment location",
                    "required": True,
                },
            ],
            "submit_cta": {"label": "Find supply plans", "selection": {"action": "source"}},
        },
    )


def options_card(quote, preamble=""):
    if not quote["options"]:
        return ChatMessage(
            content=[
                TextContent(
                    type="text",
                    text=preamble
                    + " No complete plan meets your stock, budget and deadline constraints. No items were reserved. "
                    + next(
                        (
                            e["message"]
                            for e in reversed(quote.get("events", []))
                            if e["kind"] == "unavailable"
                        ),
                        "",
                    )
                    + " "
                    "Send a revised request, or say 'start' for a new form.",
                )
            ]
        )
    items = [
        {
            "id": option["id"],
            "title": option["label"],
            "subtitle": f"{option['supplier_count']} suppliers · {option['eta_hours']} hours · Demo inventory",
            "secondary_text": money(option["total_paise"]),
            "badges": [{"label": "Within budget", "variant": "success"}],
            "primary_cta": {
                "label": "Review plan",
                "selection": {
                    "action": "review",
                    "quote_id": quote["id"],
                    "option_id": option["id"],
                },
            },
        }
        for option in quote["options"]
    ]
    return card(
        preamble
        + f" Compared supplier availability for {quote['id']}. Quotes expire in 10 minutes. "
        "Select a plan to review before anything is reserved.",
        "carousel",
        {"title": "Your rescue plans", "items": items},
    )


def review_card(quote, option):
    rows = [
        {"label": "Request", "value": quote["id"]},
        {"label": "Total", "value": money(option["total_paise"])},
        {"label": "Fulfilment estimate", "value": f"{option['eta_hours']} hours"},
        {"label": "Location", "value": quote["requirements"]["location"]},
    ]
    rows += [
        {
            "label": line["supplier_name"],
            "value": f"{line['quantity']} {line['product']}s · {money(line['quantity'] * line['unit_paise'])}",
        }
        for line in option["lines"]
    ]
    selection = {"quote_id": quote["id"], "option_id": option["id"]}
    return card(
        "Review this demo order. Stock is rechecked at confirmation; a changed plan needs new approval. "
        f"Text alternative: confirm {quote['id']} {option['id']}.",
        "review",
        {
            "title": "Confirm your rescue plan",
            "summary_rows": rows,
            "approve_cta": {
                "label": "Confirm reservations",
                "selection": {**selection, "action": "confirm"},
            },
            "reject_cta": {"label": "Back to plans", "selection": {**selection, "action": "back"}},
        },
    )


def receipt_message(order):
    payload = order["payload"]
    details = "\n".join(
        f"• {line['quantity']} {line['product']}s — {line['supplier_name']}"
        for line in payload["lines"]
    )
    reservations = ", ".join(r["id"] for r in payload["reservations"])
    return ChatMessage(
        content=[
            TextContent(
                type="text",
                text=(
                    f"Order {order['id']}: {order['status']}.\n{details}\nTotal: {money(payload['total_paise'])}. "
                    f"Estimated fulfilment: {payload['eta_hours']} hours.\nReservation IDs: {reservations}.\n"
                    "This is demo inventory; no real purchase or payment has occurred. "
                    f"To release inventory, send: cancel {order['id']}. Send track {order['id']} for shipment updates. Say 'orders' to check status."
                ),
            )
        ]
    )
