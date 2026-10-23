"""Readable Markdown fallbacks for ASI:One's conversation renderer."""

from datetime import datetime
from zoneinfo import ZoneInfo

from uagents_core.contrib.protocols.chat import ChatMessage, TextContent

from agents.cards import card, money
from backend.catalogue import SCENARIOS


def safe(value):
    return str(value).replace("|", "/").replace("\n", " ").replace("\r", " ")


def message(text):
    return ChatMessage(content=[TextContent(type="text", text=text)])


def local_time(value):
    return (
        datetime.fromisoformat(value)
        .astimezone(ZoneInfo("Asia/Kolkata"))
        .strftime("%d %b, %I:%M %p IST")
    )


def examples_message():
    return message(
        "### What are you organising?\n\n"
        + "\n\n".join(f"**{name.title()}**\n\n> {prompt}" for name, prompt in SCENARIOS.items())
        + "\n\n**Next:** copy a request and adjust quantities, budget or deadline.\n\n*Demo suppliers · Nothing reserved until approval.*"
    )


def supplier_message(supplier):
    rows = "\n".join(
        f"| {i['product'].title()} | {money(i['unit_paise'])} | {str(i['stock']) + ' available' if i['stock'] else '**Sold out**'} |"
        for i in supplier["inventory"]
    )
    return message(
        f"### {safe(supplier['name'])}\n\n"
        f"**{'Accepting orders' if supplier['active'] else 'Paused'}** · {safe(supplier['area'])} · Estimated {supplier['eta_hours']}h\n\n"
        f"| Product | Each | Stock |\n| --- | ---: | --- |\n{rows}\n\n"
        "**Next:** tell me the products, quantities, total budget and deadline. The planner compares all active suppliers.\n\n"
        "`catalogue` → all suppliers · `examples` → request ideas\n\n"
        "*Demo inventory; no real purchase. Availability is rechecked at confirmation.*"
    )


def catalogue_message(suppliers):
    active = [s for s in suppliers if s["active"]]
    if not active:
        return message(
            "### Supplier catalogue\n\nNo active supplier inventories are available right now. Please retry shortly.\n\n*Demo suppliers; no real purchases.*"
        )
    rows, items = [], []
    for supplier in active:
        available = [i for i in supplier["inventory"] if i["stock"] > 0]
        products = ", ".join(i["product"] for i in available) or "Out of stock"
        price = min((i["unit_paise"] for i in available), default=None)
        rows.append(f"| {safe(supplier['name'])} | {supplier['eta_hours']}h | {products} |")
        items.append(
            {
                "id": supplier["id"],
                "title": supplier["name"],
                "subtitle": f"{supplier['area']} · {supplier['eta_hours']}h estimate",
                "secondary_text": f"From {money(price)} / unit"
                if price is not None
                else "Out of stock",
                "badges": [
                    {
                        "label": f"{len(available)} products in stock",
                        "variant": "success" if available else "warning",
                    }
                ],
                "primary_cta": {
                    "label": "View stock & prices",
                    "selection": {"action": "supplier", "supplier_id": supplier["id"]},
                },
            }
        )
    text = (
        f"### Demo supplier catalogue\n\n**{len(active)} suppliers** · Compare stock and prices before reserving.\n\n"
        "| Supplier | ETA | In-stock products |\n| --- | --- | --- |\n"
        + "\n".join(rows)
        + "\n\n**Explore:** select a supplier card for prices and quantities.\n\n"
        + "**Text shortcuts:** "
        + " · ".join(f"`supplier {s['id']}`" for s in active)
        + "\n\n**Ready to source?** Send quantities + budget + deadline, or `start` for a form. Send `examples` for ideas.\n\n"
        "*Demo supplier catalogue: no real merchants or payments. Estimates are not delivery guarantees.*"
    )
    return card(
        text,
        "carousel",
        {"title": "Choose a supplier to explore", "items": items},
        interaction=False,
    )


def orders_message(orders):
    if not orders:
        return message(
            "### Your orders\n\nNo orders in this conversation yet.\n\n**Next:** send `start` to create a request."
        )
    sections = ["### Your orders", "*Demo reservations belonging to this conversation.*"]
    for order in orders[:10]:
        sections.append(
            f"**{order['id']}** · {order.get('fulfilment_status', order['status']).replace('_', ' ').title()}\n\n{safe(order['payload']['title'])} · **{money(order['payload']['total_paise'])}**\n\nTrack: `track {order['id']}`"
        )
    if len(orders) > 10:
        sections.append(
            f"Showing the latest 10 of {len(orders)} orders. Track an older order using its receipt ID."
        )
    return message("\n\n---\n\n".join(sections))


def tracking_message(report, *, detailed=False):
    sections = [
        f"### Tracking · {report['order_id']}",
        f"**{report['status'].replace('_', ' ').title()}** · 📍 {safe(report['location'])}",
        "*Demo operator-reported fulfilment; not live courier GPS.*",
    ]
    for shipment in report["shipments"]:
        section = [
            f"#### {safe(shipment['supplier_name'])}",
            f"**{shipment['status'].title()}** · Reservation `{shipment['reservation_id']}`",
        ]
        if shipment["status"] not in {"delivered", "cancelled"}:
            section.append(f"Estimated arrival: **{local_time(shipment['estimated_delivery'])}**")
        if shipment["overdue"]:
            section.append("⚠️ **Estimate overdue** — an operator update is needed.")
        history = shipment["history"] if detailed else shipment["history"][-1:]
        stages = ["reserved", "packing", "dispatched", "delivered"]
        if shipment["status"] in stages:
            index = stages.index(shipment["status"])
            section.append(
                " → ".join(
                    f"**{stage.title()}**" if i == index else stage.title()
                    for i, stage in enumerate(stages)
                )
            )
        section.append(
            "| Update | Time | Details |\n| --- | --- | --- |\n"
            + "\n".join(
                f"| {h['status'].title()} | {local_time(h['created_at'])} | {safe(h['note'])} |"
                for h in history
            )
        )
        sections.append("\n\n".join(section))
    sections.append(
        f"**Refresh:** `track {report['order_id']}` · **Full timeline:** `history {report['order_id']}`.\n\n*Updates change when the demo operator reports progress; they are not automatic courier events.*"
    )
    return message("\n\n".join(sections))
