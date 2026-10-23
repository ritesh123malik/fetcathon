"""Readable Markdown fallbacks for ASI:One's conversation renderer."""

from datetime import datetime
from zoneinfo import ZoneInfo

from uagents_core.contrib.protocols.chat import ChatMessage, TextContent

from agents.cards import money
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


def catalogue_message(suppliers):
    active = [s for s in suppliers if s["active"]]
    if not active:
        return message(
            "### Supplier catalogue\n\nNo active supplier inventories are available right now. Please retry shortly.\n\n*Demo suppliers; no real purchases.*"
        )
    sections = [
        "### Demo supplier catalogue",
        f"**{len(active)} available suppliers** · Prices per unit · Fulfilment estimates, not delivery guarantees",
    ]
    for supplier in active:
        rows = [
            f"#### {safe(supplier['name'])}",
            f"📍 {safe(supplier['area'])} · ⏱ **{supplier['eta_hours']} hours**",
            "| Product | Unit price | Availability |\n| --- | ---: | --- |",
        ]
        products = sorted(
            supplier["inventory"], key=lambda item: (item["stock"] == 0, item["product"])
        )
        rows[-1] += "\n" + "\n".join(
            f"| {i['product'].title()} | {money(i['unit_paise'])} | {str(i['stock']) + ' in stock' if i['stock'] else '**Out of stock**'} |"
            for i in products
        )
        sections.append("\n\n".join(rows))
    sections += [
        "### Try a request",
        "\n\n".join(f"**{name.title()}**\n\n> {prompt}" for name, prompt in SCENARIOS.items()),
        "**Next:** send quantities, budget and deadline—or `start` for the form.\n\n*Demo supplier catalogue: no real merchants or payments. Stock is rechecked when you confirm.*",
    ]
    return message("\n\n".join(sections))


def orders_message(orders):
    if not orders:
        return message(
            "### Your orders\n\nNo orders in this conversation yet.\n\n**Next:** send `start` to create a request."
        )
    sections = ["### Your orders", "*Demo reservations belonging to this conversation.*"]
    for order in orders[:10]:
        sections.append(
            f"**{order['id']}** · {order['status'].title()}\n\n{safe(order['payload']['title'])} · **{money(order['payload']['total_paise'])}**\n\nTrack: `track {order['id']}`"
        )
    if len(orders) > 10:
        sections.append(
            f"Showing the latest 10 of {len(orders)} orders. Track an older order using its receipt ID."
        )
    return message("\n\n---\n\n".join(sections))


def tracking_message(report):
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
        section.append(
            "| Update | Time | Details |\n| --- | --- | --- |\n"
            + "\n".join(
                f"| {h['status'].title()} | {local_time(h['created_at'])} | {safe(h['note'])} |"
                for h in shipment["history"]
            )
        )
        sections.append("\n\n".join(section))
    sections.append(
        f"**Refresh:** send `track {report['order_id']}` again.\n\n*Updates change when the demo operator reports progress; they are not automatic courier events.*"
    )
    return message("\n\n".join(sections))
