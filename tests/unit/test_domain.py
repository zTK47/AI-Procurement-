from decimal import Decimal

import pytest

from app.domain.entities import (
    CatalogItem,
    CostCenter,
    InvalidTransition,
    ParsedRequest,
    ProcurementRequest,
    RequestStatus,
)
from app.domain.rules import approval_level, find_matching_items, select_cheapest
from app.domain.value_objects import Money, Quantity, Sku


def item(sku, name, category, price, stock=10, supplier="SUP-001"):
    return CatalogItem(Sku(sku), name, category, supplier, Money(Decimal(price)), stock)


CATALOG = [
    item("LEN-T14-G3", "Lenovo ThinkPad T14 Gen 3", "Laptop", "1200", stock=3),
    item("LEN-X1-C11", "Lenovo ThinkPad X1 Carbon Gen 11", "Laptop", "1350"),
    item("DEL-LAT-5440", "Dell Latitude 5440", "Laptop", "1150"),
    item("HP-E24-G5", "HP EliteDisplay E24 Monitor", "Monitor", "210"),
]


def test_money_multiplies_and_compares():
    total = Money(Decimal("1200")) * Quantity(5)

    assert total == Money(Decimal("6000"))
    assert total > Money(Decimal("1000"))
    assert (Money(Decimal("10")) - Money(Decimal("4"))).amount == Decimal("6")


def test_money_rejects_negative_amounts_and_mixed_currencies():
    with pytest.raises(ValueError):
        Money(Decimal("-1"))
    with pytest.raises(ValueError):
        Money(Decimal("1"), "CHF") + Money(Decimal("1"), "EUR")


def test_quantity_and_sku_must_be_valid():
    with pytest.raises(ValueError):
        Quantity(0)
    with pytest.raises(ValueError):
        Sku(" ")


def test_matching_uses_all_product_tokens_and_ignores_plural():
    parsed = ParsedRequest(5, "Lenovo Laptops", "Laptop", 0.9)

    assert {i.sku.value for i in find_matching_items(CATALOG, parsed)} == {"LEN-T14-G3", "LEN-X1-C11"}


def test_matching_returns_nothing_for_unknown_product():
    assert find_matching_items(CATALOG, ParsedRequest(1, "Commodore 64", None, 0.5)) == []


def test_sourcing_rule_selects_cheapest_item():
    parsed = ParsedRequest(1, "laptop", "Laptop", 0.9)

    assert select_cheapest(find_matching_items(CATALOG, parsed)).sku.value == "DEL-LAT-5440"


@pytest.mark.parametrize(
    ("total", "stock_ok", "expected"),
    [("1000", True, None), ("1000", False, "MANAGER"), ("1000.05", True, "MANAGER"),
     ("25000", True, "MANAGER"), ("25000.01", True, "DIRECTOR")],
)
def test_approval_level(total, stock_ok, expected):
    assert approval_level(Money(Decimal(total)), stock_ok) == expected


def test_cost_center_consumes_budget_and_refuses_overspend():
    center = CostCenter("CC-1", "IT", Money(Decimal("100")))

    center.consume(Money(Decimal("60")))

    assert center.budget_remaining == Money(Decimal("40"))
    with pytest.raises(ValueError):
        center.consume(Money(Decimal("41")))


def test_request_follows_workflow_and_records_history():
    request = ProcurementRequest.create("req-1", "I need 5 laptops", "CC-100")
    request.mark_parsed(ParsedRequest(5, "laptop", "Laptop", 0.9))
    request.mark_resolved(CATALOG[0])
    request.mark_validated(budget_ok=True, stock_ok=False)

    assert request.status is RequestStatus.PENDING_APPROVAL
    assert request.total == Money(Decimal("6000"))
    assert request.approval_level == "MANAGER"

    request.approve()

    assert request.history == ["CREATED", "PARSED", "RESOLVED", "VALIDATED", "PENDING_APPROVAL", "APPROVED"]


def test_request_rejects_invalid_transitions():
    request = ProcurementRequest.create("req-1", "x", "CC-100")

    with pytest.raises(InvalidTransition):
        request.approve()

    request.reject("PARSE_FAILED")
    with pytest.raises(InvalidTransition):
        request.reject("again")


def test_budget_failure_waits_for_procurement_approval():
    request = ProcurementRequest.create("req-1", "x", "CC-100")
    request.mark_parsed(ParsedRequest(5, "laptop", "Laptop", 0.9))
    request.mark_resolved(CATALOG[1])
    request.mark_validated(budget_ok=False, stock_ok=True)

    assert request.status is RequestStatus.PENDING_APPROVAL
    assert request.budget_check == "FAILED"
    assert request.history[-2:] == ["VALIDATED", "PENDING_APPROVAL"]
