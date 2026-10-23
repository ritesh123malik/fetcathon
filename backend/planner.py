"""Bounded deterministic allocation. Money is integer paise, never model arithmetic."""

from itertools import combinations

from backend.models import Requirements


def build_options(requirements: Requirements, suppliers: list[dict]) -> list[dict]:
    eligible = [
        s for s in suppliers if s["active"] and s["eta_hours"] <= requirements.deadline_hours
    ]
    candidates = []
    seen = set()
    for count in range(1, len(eligible) + 1):
        for group in combinations(eligible, count):
            lines = []
            for item in requirements.items:
                remaining = item.quantity
                offers = []
                for supplier in group:
                    inventory = next(
                        (i for i in supplier["inventory"] if i["product"] == item.product), None
                    )
                    if inventory:
                        offers.append((inventory["unit_paise"], supplier, inventory))
                for price, supplier, inventory in sorted(offers, key=lambda x: (x[0], x[1]["id"])):
                    amount = min(remaining, inventory["stock"])
                    if amount:
                        lines.append(
                            {
                                "supplier_id": supplier["id"],
                                "supplier_name": supplier["name"],
                                "product": item.product,
                                "quantity": amount,
                                "unit_paise": price,
                                "eta_hours": supplier["eta_hours"],
                            }
                        )
                        remaining -= amount
                if remaining:
                    break
            else:
                total = sum(line["quantity"] * line["unit_paise"] for line in lines)
                signature = tuple(
                    sorted(
                        (line["supplier_id"], line["product"], line["quantity"]) for line in lines
                    )
                )
                if total <= requirements.budget_paise and signature not in seen:
                    seen.add(signature)
                    candidates.append(
                        {
                            "total_paise": total,
                            "lines": lines,
                            "eta_hours": max(line["eta_hours"] for line in lines),
                            "supplier_count": len({line["supplier_id"] for line in lines}),
                        }
                    )
    if not candidates:
        return []
    cheapest = min(candidates, key=lambda x: (x["total_paise"], x["eta_hours"]))
    fastest = min(candidates, key=lambda x: (x["eta_hours"], x["total_paise"]))
    simplest = min(candidates, key=lambda x: (x["supplier_count"], x["total_paise"]))
    chosen = []
    for label, candidate in [
        ("Best value", cheapest),
        ("Fastest fulfilment", fastest),
        ("Fewer suppliers", simplest),
    ]:
        if candidate not in [c[1] for c in chosen]:
            chosen.append((label, candidate))
    return [
        {**candidate, "id": f"option-{index + 1}", "label": label}
        for index, (label, candidate) in enumerate(chosen)
    ]
