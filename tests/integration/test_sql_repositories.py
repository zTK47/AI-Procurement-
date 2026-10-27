from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import inspect, select

from app.domain.entities import OrderLine, ParsedRequest, ProcurementRequest, PurchaseOrder, RequestStatus
from app.domain.value_objects import Money
from app.infrastructure.db import (
    Database,
    OrderLineRow,
    PurchaseOrderRow,
    SqlCatalogRepository,
    SqlCostCenterRepository,
    SqlRequestRepository,
    StatusHistoryRow,
)


@pytest.fixture
def database():
    db = Database("sqlite://")
    db.create_schema()
    db.seed()
    return db


def test_schema_has_relational_entity_tables(database):
    assert set(inspect(database.engine).get_table_names()) == {
        "suppliers", "catalog_items", "cost_centers", "procurement_requests",
        "request_status_history", "purchase_orders", "purchase_order_lines",
    }


def test_catalog_items_reference_suppliers(database):
    catalog = SqlCatalogRepository(database)
    item = next(i for i in catalog.list_items() if i.sku.value == "LEN-T14-G3")

    assert item.unit_price == Money(Decimal("1200.00"))
    assert catalog.get_supplier(item.supplier_id).name == "Alpine IT Distribution AG"


def test_sent_request_round_trips_with_history_and_purchase_order(database):
    catalog = SqlCatalogRepository(database)
    requests = SqlRequestRepository(database)
    item = next(i for i in catalog.list_items() if i.sku.value == "LEN-T14-G3")

    request = ProcurementRequest.create("req-1", "I need 5 new Lenovo Laptop", "CC-100", requester="Anna Keller")
    request.mark_parsed(ParsedRequest(5, "Lenovo Laptop", "Laptop", 0.95))
    request.mark_resolved(item)
    request.mark_validated(budget_ok=True, stock_ok=False)
    requests.save(request)
    request.approve()
    request.mark_sent(PurchaseOrder(
        "PO-1", "req-1", "CC-100", catalog.get_supplier("SUP-001"),
        (OrderLine(item.sku, item.name, request.quantity, item.unit_price),),
        datetime.now(timezone.utc),
    ))
    requests.save(request)

    loaded = requests.get("req-1")

    assert loaded.status is RequestStatus.ORDER_SENT
    assert loaded.requester == "Anna Keller"
    assert loaded.history == request.history
    assert loaded.parsed == request.parsed
    assert loaded.item.sku == item.sku
    assert loaded.total == Money(Decimal("6000"))
    assert loaded.approval_level == "MANAGER"
    assert loaded.purchase_order.total == Money(Decimal("6000"))
    assert loaded.purchase_order.supplier.id == "SUP-001"
    with database.sessions() as session:
        assert len(session.scalars(select(StatusHistoryRow)).all()) == len(request.history)
        assert session.scalar(select(PurchaseOrderRow)).request_id == "req-1"
        assert session.scalar(select(OrderLineRow)).quantity == 5


def test_cost_center_budget_is_persisted(database):
    centers = SqlCostCenterRepository(database)
    center = centers.get("CC-100")

    center.consume(Money(Decimal("1140")))
    centers.save(center)

    assert centers.get("CC-100").budget_remaining == Money(Decimal("48860"))
