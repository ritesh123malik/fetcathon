from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import pytest

from backend.service import DomainError


def snapshot(service):
    return {
        (s["id"], i["product"]): i["stock"] for s in service.suppliers() for i in s["inventory"]
    }


def test_split_order_and_idempotency(service, requirements):
    before = snapshot(service)
    quote = service.quote(requirements, "user")
    option = quote["options"][0]
    assert option["total_paise"] == 272000
    assert option["supplier_count"] == 2
    order = service.confirm(quote["id"], option["id"], "user")
    again = service.confirm(quote["id"], option["id"], "user")
    assert order["order"]["id"] == again["order"]["id"]
    assert again["replayed"]
    after = snapshot(service)
    for line in option["lines"]:
        key = (line["supplier_id"], line["product"])
        assert after[key] == before[key] - line["quantity"]


def test_supplier_failure_replans_without_partial_commit(service, requirements):
    quote = service.quote(requirements, "user")
    service.availability("campus", False)
    before = snapshot(service)
    result = service.confirm(quote["id"], quote["options"][0]["id"], "user")
    assert result["status"] == "reapproval_required"
    assert snapshot(service) == before
    assert result["quote"]["parent_id"] == quote["id"]
    assert result["quote"]["options"][0]["total_paise"] == 312000
    assert service.orders("user") == []
    replacement = result["quote"]
    assert (
        service.confirm(replacement["id"], replacement["options"][0]["id"], "user")["status"]
        == "confirmed"
    )


def test_expiry_requires_new_approval(service, requirements):
    quote = service.quote(requirements, "user")
    with service.db.transaction() as conn:
        conn.execute(
            "UPDATE quotes SET expires_at=? WHERE id=?",
            ((datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(), quote["id"]),
        )
    result = service.confirm(quote["id"], "option-1", "user")
    assert result["status"] == "reapproval_required"
    assert service.orders("user") == []


def test_concurrent_confirmations_commit_once(service, requirements):
    quote = service.quote(requirements, "user")
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(
            pool.map(lambda _: service.confirm(quote["id"], "option-1", "user"), range(6))
        )
    assert len({r["order"]["id"] for r in results}) == 1
    assert sum(not r["replayed"] for r in results) == 1


def test_competing_quotes_do_not_oversell(service, requirements):
    requirements.items[0].quantity = 100
    requirements.items = requirements.items[:1]
    requirements.budget_paise = 1000000
    quotes = [service.quote(requirements, f"user-{i}") for i in range(4)]
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(
            pool.map(
                lambda pair: service.confirm(pair[1]["id"], "option-1", f"user-{pair[0]}"),
                enumerate(quotes),
            )
        )
    assert sum(r["status"] == "confirmed" for r in results) == 1
    assert all(stock >= 0 for stock in snapshot(service).values())


def test_cancel_restores_once(service, requirements):
    before = snapshot(service)
    quote = service.quote(requirements, "user")
    order = service.confirm(quote["id"], "option-1", "user")["order"]
    service.cancel_order(order["id"], "user")
    service.cancel_order(order["id"], "user")
    assert snapshot(service) == before


def test_owner_cannot_access_other_quotes_or_orders(service, requirements):
    quote = service.quote(requirements, "alice")
    with pytest.raises(DomainError, match="not found"):
        service.confirm(quote["id"], "option-1", "bob")
    order = service.confirm(quote["id"], "option-1", "alice")["order"]
    with pytest.raises(DomainError, match="not found"):
        service.cancel_order(order["id"], "bob")


def test_unavailable_does_not_exceed_budget(service, requirements):
    requirements.budget_paise = 100
    quote = service.quote(requirements, "user")
    assert quote["status"] == "unavailable"
    assert quote["options"] == []


def test_invalid_option_and_deadline(service, requirements):
    quote = service.quote(requirements, "user")
    with pytest.raises(DomainError, match="valid plan"):
        service.confirm(quote["id"], "invented-option", "user")
    requirements.deadline_hours = 1
    assert service.quote(requirements, "user")["options"] == []
