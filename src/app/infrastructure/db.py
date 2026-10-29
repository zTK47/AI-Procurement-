"""SQLAlchemy ORM model and persistence adapters for the repository ports."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, Numeric, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
from sqlalchemy.pool import StaticPool

from app.domain.entities import (
    CatalogItem,
    CostCenter,
    OrderLine,
    ParsedRequest,
    ProcurementRequest,
    PurchaseOrder,
    RequestStatus,
    Supplier,
)
from app.domain.value_objects import Money, Quantity, Sku
from app.infrastructure import seed

Amount = Numeric(12, 2, asdecimal=True)


class Base(DeclarativeBase):
    pass


class SupplierRow(Base):
    __tablename__ = "suppliers"
    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(200))
    items: Mapped[list[CatalogItemRow]] = relationship(back_populates="supplier")


class CatalogItemRow(Base):
    __tablename__ = "catalog_items"
    sku: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(100), index=True)
    supplier_id: Mapped[str] = mapped_column(ForeignKey("suppliers.id"))
    unit_price: Mapped[Decimal] = mapped_column(Amount)
    currency: Mapped[str] = mapped_column(String(3), default="CHF")
    stock: Mapped[int] = mapped_column(Integer)
    supplier: Mapped[SupplierRow] = relationship(back_populates="items")


class CostCenterRow(Base):
    __tablename__ = "cost_centers"
    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    budget_remaining: Mapped[Decimal] = mapped_column(Amount)
    currency: Mapped[str] = mapped_column(String(3), default="CHF")


class RequestRow(Base):
    __tablename__ = "procurement_requests"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    raw_text: Mapped[str] = mapped_column(String(1000))
    requester_name: Mapped[str] = mapped_column(String(100), default="")
    cost_center_id: Mapped[str] = mapped_column(ForeignKey("cost_centers.id"))
    status: Mapped[str] = mapped_column(String(30), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    parsed_quantity: Mapped[int | None] = mapped_column(Integer)
    parsed_product: Mapped[str | None] = mapped_column(String(200))
    parsed_category: Mapped[str | None] = mapped_column(String(100))
    parsed_confidence: Mapped[float | None] = mapped_column(Float)
    sku: Mapped[str | None] = mapped_column(ForeignKey("catalog_items.sku"))
    unit_price: Mapped[Decimal | None] = mapped_column(Amount)
    total: Mapped[Decimal | None] = mapped_column(Amount)
    currency: Mapped[str] = mapped_column(String(3), default="CHF")
    budget_check: Mapped[str | None] = mapped_column(String(10))
    stock_check: Mapped[str | None] = mapped_column(String(10))
    approval_level: Mapped[str | None] = mapped_column(String(20))
    rejection_reason: Mapped[str | None] = mapped_column(String(200))

    item: Mapped[CatalogItemRow | None] = relationship()
    history: Mapped[list[StatusHistoryRow]] = relationship(
        order_by="StatusHistoryRow.position", cascade="all, delete-orphan")
    purchase_order: Mapped[PurchaseOrderRow | None] = relationship(
        back_populates="request", cascade="all, delete-orphan")


class StatusHistoryRow(Base):
    __tablename__ = "request_status_history"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_id: Mapped[str] = mapped_column(ForeignKey("procurement_requests.id"), index=True)
    position: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30))
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class PurchaseOrderRow(Base):
    __tablename__ = "purchase_orders"
    po_number: Mapped[str] = mapped_column(String(40), primary_key=True)
    request_id: Mapped[str] = mapped_column(ForeignKey("procurement_requests.id"), unique=True)
    supplier_id: Mapped[str] = mapped_column(ForeignKey("suppliers.id"))
    cost_center_id: Mapped[str] = mapped_column(ForeignKey("cost_centers.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    request: Mapped[RequestRow] = relationship(back_populates="purchase_order")
    supplier: Mapped[SupplierRow] = relationship()
    lines: Mapped[list[OrderLineRow]] = relationship(cascade="all, delete-orphan")


class OrderLineRow(Base):
    __tablename__ = "purchase_order_lines"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    po_number: Mapped[str] = mapped_column(ForeignKey("purchase_orders.po_number"), index=True)
    sku: Mapped[str] = mapped_column(ForeignKey("catalog_items.sku"))
    description: Mapped[str] = mapped_column(String(200))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[Decimal] = mapped_column(Amount)
    currency: Mapped[str] = mapped_column(String(3), default="CHF")


def normalize_database_url(url: str) -> str:
    """Hosted PostgreSQL URLs (Neon, Render) use postgres:// or postgresql://; use the psycopg 3 driver."""
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


class Database:
    def __init__(self, url: str):
        url = normalize_database_url(url)
        options: dict[str, Any] = {}
        if url.startswith("sqlite"):
            options["connect_args"] = {"check_same_thread": False}
            if url in ("sqlite://", "sqlite:///:memory:"):
                options["poolclass"] = StaticPool
        else:
            options["pool_pre_ping"] = True
        self.engine = create_engine(url, **options)
        self.sessions = sessionmaker(self.engine, expire_on_commit=False)

    def create_schema(self) -> None:
        Base.metadata.create_all(self.engine)

    def seed(self) -> None:
        with self.sessions.begin() as session:
            if session.scalar(select(SupplierRow).limit(1)) is not None:
                return
            session.add_all(SupplierRow(id=i, name=n, email=e) for i, n, e in seed.SUPPLIERS)
            session.add_all(
                CatalogItemRow(sku=s, name=n, category=c, supplier_id=sup, unit_price=Decimal(p), stock=st)
                for s, n, c, sup, p, st in seed.CATALOG_ITEMS
            )
            session.add_all(CostCenterRow(id=i, name=n, budget_remaining=Decimal(b)) for i, n, b in seed.COST_CENTERS)


def _supplier(row: SupplierRow) -> Supplier:
    return Supplier(row.id, row.name, row.email)


def _item(row: CatalogItemRow, unit_price: Money | None = None) -> CatalogItem:
    price = unit_price or Money(row.unit_price, row.currency)
    return CatalogItem(Sku(row.sku), row.name, row.category, row.supplier_id, price, row.stock)


def _cost_center(row: CostCenterRow) -> CostCenter:
    return CostCenter(row.id, row.name, Money(row.budget_remaining, row.currency))


class SqlCatalogRepository:
    def __init__(self, database: Database):
        self.db = database

    def list_items(self) -> list[CatalogItem]:
        with self.db.sessions() as session:
            return [_item(row) for row in session.scalars(select(CatalogItemRow).order_by(CatalogItemRow.sku))]

    def list_suppliers(self) -> list[Supplier]:
        with self.db.sessions() as session:
            return [_supplier(row) for row in session.scalars(select(SupplierRow).order_by(SupplierRow.id))]

    def get_supplier(self, supplier_id: str) -> Supplier | None:
        with self.db.sessions() as session:
            row = session.get(SupplierRow, supplier_id)
            return _supplier(row) if row else None


class SqlCostCenterRepository:
    def __init__(self, database: Database):
        self.db = database

    def list_all(self) -> list[CostCenter]:
        with self.db.sessions() as session:
            return [_cost_center(row) for row in session.scalars(select(CostCenterRow).order_by(CostCenterRow.id))]

    def get(self, cost_center_id: str) -> CostCenter | None:
        with self.db.sessions() as session:
            row = session.get(CostCenterRow, cost_center_id)
            return _cost_center(row) if row else None

    def save(self, center: CostCenter) -> None:
        with self.db.sessions.begin() as session:
            session.get(CostCenterRow, center.id).budget_remaining = center.budget_remaining.amount


def _write(row: RequestRow, request: ProcurementRequest) -> None:
    parsed, item = request.parsed, request.item
    row.status = request.status.value
    row.parsed_quantity = parsed.quantity if parsed else None
    row.parsed_product = parsed.product_name if parsed else None
    row.parsed_category = parsed.category if parsed else None
    row.parsed_confidence = parsed.confidence if parsed else None
    row.sku = item.sku.value if item else None
    row.unit_price = item.unit_price.amount if item else None
    row.total = request.total.amount if request.total else None
    row.currency = item.unit_price.currency if item else "CHF"
    row.budget_check = request.budget_check
    row.stock_check = request.stock_check
    row.approval_level = request.approval_level
    row.rejection_reason = request.rejection_reason

    now = datetime.now(timezone.utc)
    for position, status in enumerate(request.history[len(row.history):], start=len(row.history)):
        row.history.append(StatusHistoryRow(position=position, status=status, changed_at=now))

    order = request.purchase_order
    if order and row.purchase_order is None:
        row.purchase_order = PurchaseOrderRow(
            po_number=order.po_number,
            supplier_id=order.supplier.id,
            cost_center_id=order.cost_center_id,
            created_at=order.created_at,
            lines=[
                OrderLineRow(sku=line.sku.value, description=line.description, quantity=line.quantity.value,
                             unit_price=line.unit_price.amount, currency=line.unit_price.currency)
                for line in order.lines
            ],
        )


def _read(row: RequestRow) -> ProcurementRequest:
    parsed = None
    if row.parsed_confidence is not None:
        parsed = ParsedRequest(row.parsed_quantity, row.parsed_product or "", row.parsed_category, row.parsed_confidence)
    order = None
    if row.purchase_order:
        po = row.purchase_order
        order = PurchaseOrder(
            po_number=po.po_number,
            request_id=row.id,
            cost_center_id=po.cost_center_id,
            supplier=_supplier(po.supplier),
            lines=tuple(
                OrderLine(Sku(l.sku), l.description, Quantity(l.quantity), Money(l.unit_price, l.currency))
                for l in po.lines
            ),
            created_at=po.created_at,
        )
    return ProcurementRequest(
        id=row.id,
        raw_text=row.raw_text,
        cost_center_id=row.cost_center_id,
        requester=row.requester_name,
        status=RequestStatus(row.status),
        history=[h.status for h in row.history],
        created_at=row.created_at,
        parsed=parsed,
        item=_item(row.item, Money(row.unit_price, row.currency)) if row.item else None,
        total=Money(row.total, row.currency) if row.total is not None else None,
        budget_check=row.budget_check,
        stock_check=row.stock_check,
        approval_level=row.approval_level,
        rejection_reason=row.rejection_reason,
        purchase_order=order,
    )


class SqlRequestRepository:
    def __init__(self, database: Database):
        self.db = database

    def save(self, request: ProcurementRequest) -> None:
        with self.db.sessions.begin() as session:
            row = session.get(RequestRow, request.id)
            if row is None:
                row = RequestRow(id=request.id, raw_text=request.raw_text, requester_name=request.requester,
                                 cost_center_id=request.cost_center_id, created_at=request.created_at)
                session.add(row)
            _write(row, request)

    def get(self, request_id: str) -> ProcurementRequest | None:
        with self.db.sessions() as session:
            row = session.get(RequestRow, request_id)
            return _read(row) if row else None

    def list_recent(self, limit: int = 50) -> list[ProcurementRequest]:
        with self.db.sessions() as session:
            rows = session.scalars(select(RequestRow).order_by(RequestRow.created_at.desc()).limit(limit))
            return [_read(row) for row in rows]
