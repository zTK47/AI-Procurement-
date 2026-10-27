from decimal import Decimal

import pytest

from app.application.use_cases import (
    ApproveRequest,
    NotFound,
    RejectRequest,
    SendOrder,
    SubmitRequest,
)
from app.domain.entities import (
    CatalogItem,
    CostCenter,
    InvalidTransition,
    ParsedRequest,
    RequestStatus,
    Supplier,
)
from app.domain.value_objects import Money, Sku


class InMemoryCatalog:
    def __init__(self):
        self.items = [
            CatalogItem(Sku("LEN-T14-G3"), "Lenovo ThinkPad T14 Gen 3", "Laptop", "SUP-001", Money(Decimal("1200")), 3),
            CatalogItem(Sku("LEN-X1-C11"), "Lenovo ThinkPad X1 Carbon Gen 11", "Laptop", "SUP-002", Money(Decimal("1350")), 20),
        ]
        self.suppliers = {"SUP-001": Supplier("SUP-001", "Alpine IT Distribution AG", "orders@alpine-it.example")}

    def list_items(self):
        return list(self.items)

    def get_supplier(self, supplier_id):
        return self.suppliers.get(supplier_id)


class InMemoryCostCenters:
    def __init__(self):
        self.centers = {"CC-100": CostCenter("CC-100", "IT", Money(Decimal("50000")))}

    def get(self, cost_center_id):
        return self.centers.get(cost_center_id)

    def save(self, center):
        self.centers[center.id] = center


class InMemoryRequests:
    def __init__(self):
        self.saved = {}

    def save(self, request):
        self.saved[request.id] = request

    def get(self, request_id):
        return self.saved.get(request_id)


class StaticParser:
    def __init__(self, parsed):
        self.parsed = parsed

    def parse(self, text):
        return self.parsed


@pytest.fixture
def repos():
    return InMemoryCatalog(), InMemoryCostCenters(), InMemoryRequests()


def submit(repos, parsed=ParsedRequest(5, "Lenovo Laptop", "Laptop", 0.95)):
    catalog, centers, requests = repos
    return SubmitRequest(StaticParser(parsed), catalog, centers, requests).execute(
        "I need 5 new Lenovo Laptop", "CC-100", requester="Anna Keller")


def test_submit_runs_parse_resolve_validate_and_persists(repos):
    request = submit(repos)

    assert request.status is RequestStatus.PENDING_APPROVAL
    assert request.item.sku.value == "LEN-T14-G3"
    assert request.requester == "Anna Keller"
    assert repos[2].get(request.id) is request


def test_submit_rejects_when_quantity_missing(repos):
    request = submit(repos, ParsedRequest(None, "Lenovo Laptop", "Laptop", 0.3))

    assert request.rejection_reason == "PARSE_FAILED"


def test_submit_with_unknown_cost_center_raises(repos):
    catalog, centers, requests = repos

    with pytest.raises(NotFound):
        SubmitRequest(StaticParser(None), catalog, centers, requests).execute("x", "CC-999")


def test_approve_reject_and_send(repos):
    catalog, centers, requests = repos
    request = submit(repos)

    ApproveRequest(requests).execute(request.id)
    order = SendOrder(requests, catalog, centers).execute(request.id).purchase_order

    assert order.supplier.name == "Alpine IT Distribution AG"
    assert order.total == Money(Decimal("6000"))
    assert centers.get("CC-100").budget_remaining == Money(Decimal("44000"))

    with pytest.raises(InvalidTransition):
        RejectRequest(requests).execute(request.id, "too late")


def test_send_requires_approval(repos):
    catalog, centers, requests = repos
    request = submit(repos)

    with pytest.raises(InvalidTransition):
        SendOrder(requests, catalog, centers).execute(request.id)


def test_unknown_request_raises_not_found(repos):
    with pytest.raises(NotFound):
        ApproveRequest(repos[2]).execute("req-missing")
