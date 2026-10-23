"""Native ASI:One cards; no external frontend is needed to complete an order."""

import json

from uagents_core.contrib.protocols.chat import ChatMessage, MetadataContent, TextContent

from backend.catalogue import PRODUCTS


def money(paise):
    return f"INR {paise / 100:,.2f}"


def card(text: str, kind: str, payload: dict, *, interaction=True):
    return ChatMessage(
        content=[
            TextContent(type="text", text=text),
            MetadataContent(
                type="metadata",
                metadata={
                    "card_protocol_version": "1",
                    "requires_card_interaction": "true" if interaction else "false",
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
        + f"### Your supply plans\n\nRequest `{quote['id']}` · Valid for **10 minutes**\n\n"
        + "\n\n".join(
            f"**{o['label']} — {money(o['total_paise'])}** · {o['eta_hours']} hours · {o['supplier_count']} supplier(s)\n\nReview: `review {quote['id']} {o['id']}`"
            for o in quote["options"]
        )
        + "\n\n**Next:** choose a plan to review. Nothing is reserved yet.",
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
        "### Review your reservation\n\n"
        + "| Detail | Value |\n| --- | --- |\n"
        + "\n".join(
            f"| {row['label']} | {str(row['value']).replace('|', '/').replace(chr(10), ' ')} |"
            for row in rows
        )
        + f"\n\n**Approve:** `confirm {quote['id']} {option['id']}`\n\n"
        "*Demo order. Stock is rechecked; any replacement requires fresh approval.*",
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
        f"| {line['product'].title()} | {line['quantity']} | {line['supplier_name']} | {money(line['quantity'] * line['unit_paise'])} |"
        for line in payload["lines"]
    )
    reservations = ", ".join(f"`{r['id']}`" for r in payload["reservations"])
    title = "Reservation cancelled" if order["status"] == "cancelled" else "Reservation confirmed"
    next_step = (
        "Send `start` to create a new request."
        if order["status"] == "cancelled"
        else (
            f"**Track:** `track {order['id']}`\n\n"
            f"**Cancel before dispatch:** `cancel {order['id']}`"
        )
    )
    return ChatMessage(
        content=[
            TextContent(
                type="text",
                text=(
                    f"### {title}\n\n**Order `{order['id']}`** · {order['status']}\n\n"
                    f"| Product | Quantity | Supplier | Subtotal |\n| --- | ---: | --- | ---: |\n{details}\n\n"
                    f"**Total: {money(payload['total_paise'])}**\n\n"
                    + (
                        "Inventory has been released.\n\n"
                        if order["status"] == "cancelled"
                        else f"Estimated fulfilment: **{payload['eta_hours']} hours** from confirmation.\n\n"
                    )
                    + f"Reservation IDs: {reservations}\n\n{next_step}\n\n"
                    "*Demo inventory only. No real purchase or payment has occurred.*"
                ),
            )
        ]
    )
