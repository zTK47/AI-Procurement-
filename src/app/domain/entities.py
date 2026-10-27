from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from app.domain.rules import approval_level
from app.domain.value_objects import Money, Quantity, Sku


class InvalidTransition(Exception):
    """Raised when a workflow step is not allowed in the current state."""


class RequestStatus(str, Enum):
    CREATED = "CREATED"
    PARSED = "PARSED"
    RESOLVED = "RESOLVED"
    VALIDATED = "VALIDATED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    ORDER_SENT = "ORDER_SENT"
    REJECTED = "REJECTED"


S = RequestStatus
TRANSITIONS = {
    S.CREATED: {S.PARSED, S.REJECTED},
    S.PARSED: {S.RESOLVED, S.REJECTED},
    S.RESOLVED: {S.VALIDATED, S.REJECTED},
    S.VALIDATED: {S.PENDING_APPROVAL, S.APPROVED, S.REJECTED},
    S.PENDING_APPROVAL: {S.APPROVED, S.REJECTED},
    S.APPROVED: {S.ORDER_SENT},
    S.ORDER_SENT: set(),
    S.REJECTED: set(),
}


@dataclass(frozen=True)
class Supplier:
    id: str
    name: str
    email: str


@dataclass(frozen=True)
class CatalogItem:
    sku: Sku
    name: str
    category: str
    supplier_id: str
    unit_price: Money
    stock: int


@dataclass
class CostCenter:
    id: str
    name: str
    budget_remaining: Money

    def consume(self, amount: Money) -> None:
        if amount > self.budget_remaining:
            raise ValueError(f"Budget of cost center {self.id} exceeded")
        self.budget_remaining = self.budget_remaining - amount


@dataclass(frozen=True)
class ParsedRequest:
    quantity: int | None
    product_name: str
    category: str | None
    confidence: float

    @property
    def is_complete(self) -> bool:
        return bool(self.quantity and self.quantity > 0 and self.product_name.strip())


@dataclass(frozen=True)
class OrderLine:
    sku: Sku
    description: str
    quantity: Quantity
    unit_price: Money

    @property
    def line_total(self) -> Money:
        return self.unit_price * self.quantity


@dataclass(frozen=True)
class PurchaseOrder:
    po_number: str
    request_id: str
    cost_center_id: str
    supplier: Supplier
    lines: tuple[OrderLine, ...]
    created_at: datetime

    @property
    def total(self) -> Money:
        total = Money(0, self.lines[0].unit_price.currency)
        for line in self.lines:
            total = total + line.line_total
        return total


@dataclass
class ProcurementRequest:
    id: str
    raw_text: str
    cost_center_id: str
    requester: str = ""
    status: RequestStatus = RequestStatus.CREATED
    history: list[str] = field(default_factory=lambda: [RequestStatus.CREATED.value])
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    parsed: ParsedRequest | None = None
    item: CatalogItem | None = None
    total: Money | None = None
    budget_check: str | None = None
    stock_check: str | None = None
    approval_level: str | None = None
    rejection_reason: str | None = None
    purchase_order: PurchaseOrder | None = None

    @classmethod
    def create(cls, request_id: str, raw_text: str, cost_center_id: str, requester: str = "") -> ProcurementRequest:
        return cls(id=request_id, raw_text=raw_text, cost_center_id=cost_center_id, requester=requester)

    @property
    def quantity(self) -> Quantity:
        return Quantity(self.parsed.quantity)

    @property
    def requires_approval(self) -> bool:
        return self.approval_level is not None

    def ensure_can(self, target: RequestStatus) -> None:
        if target not in TRANSITIONS[self.status]:
            raise InvalidTransition(f"Cannot move request {self.id} from {self.status.value} to {target.value}")

    def _move(self, target: RequestStatus) -> None:
        self.ensure_can(target)
        self.status = target
        self.history.append(target.value)

    def mark_parsed(self, parsed: ParsedRequest) -> None:
        self._move(RequestStatus.PARSED)
        self.parsed = parsed

    def mark_unparseable(self, parsed: ParsedRequest) -> None:
        self.reject("PARSE_FAILED")
        self.parsed = parsed

    def mark_resolved(self, item: CatalogItem) -> None:
        self._move(RequestStatus.RESOLVED)
        self.item = item
        self.total = item.unit_price * self.quantity

    def mark_validated(self, budget_ok: bool, stock_ok: bool) -> None:
        self._move(RequestStatus.VALIDATED)
        self.budget_check = "PASSED" if budget_ok else "FAILED"
        self.stock_check = "PASSED" if stock_ok else "FAILED"
        if not budget_ok:
            self.reject("BUDGET_EXCEEDED")
            return
        self.approval_level = approval_level(self.total, stock_ok)
        self._move(RequestStatus.PENDING_APPROVAL if self.requires_approval else RequestStatus.APPROVED)

    def approve(self) -> None:
        if self.status is not RequestStatus.PENDING_APPROVAL:
            raise InvalidTransition(f"Request {self.id} is not pending approval")
        self._move(RequestStatus.APPROVED)

    def reject(self, reason: str) -> None:
        self._move(RequestStatus.REJECTED)
        self.rejection_reason = reason

    def mark_sent(self, order: PurchaseOrder) -> None:
        self._move(RequestStatus.ORDER_SENT)
        self.purchase_order = order
