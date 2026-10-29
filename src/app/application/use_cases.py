from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.application.ports import CatalogRepository, CostCenterRepository, RequestParser, RequestRepository
from app.domain.entities import (
    InvalidTransition,
    OrderLine,
    ProcurementRequest,
    PurchaseOrder,
    ParsedRequest,
    RequestStatus,
)
from app.domain.rules import find_matching_items, select_cheapest


class NotFound(Exception):
    """Raised when a referenced request, cost center or supplier does not exist."""


def _load(requests: RequestRepository, request_id: str) -> ProcurementRequest:
    request = requests.get(request_id)
    if request is None:
        raise NotFound(f"Request {request_id} not found")
    return request


class SubmitRequest:
    def __init__(
        self,
        parser: RequestParser,
        catalog: CatalogRepository,
        cost_centers: CostCenterRepository,
        requests: RequestRepository,
    ):
        self.parser = parser
        self.catalog = catalog
        self.cost_centers = cost_centers
        self.requests = requests

    def execute(self, prompt: str, cost_center_id: str, requester: str = "") -> ProcurementRequest:
        center = self.cost_centers.get(cost_center_id)
        if center is None:
            raise NotFound(f"Cost center {cost_center_id} not found")

        request = ProcurementRequest.create(f"req-{uuid4().hex[:8]}", prompt.strip(), cost_center_id, requester.strip())
        self._process(request, center.budget_remaining)
        self.requests.save(request)
        return request

    def _process(self, request: ProcurementRequest, budget) -> None:
        parsed = self.parser.parse(request.raw_text)
        if parsed.quantity is None and parsed.product_name.strip():
            parsed = ParsedRequest(
                quantity=1,
                product_name=parsed.product_name,
                category=parsed.category,
                confidence=parsed.confidence,
            )
        if not parsed.is_complete:
            request.mark_unparseable(parsed)
            return
        request.mark_parsed(parsed)

        matches = find_matching_items(self.catalog.list_items(), parsed)
        if not matches:
            request.reject("ITEM_NOT_FOUND")
            return
        item = select_cheapest(matches)
        request.mark_resolved(item)

        request.mark_validated(
            budget_ok=request.total <= budget,
            stock_ok=request.quantity.value <= item.stock,
        )


class ApproveRequest:
    def __init__(self, requests: RequestRepository):
        self.requests = requests

    def execute(self, request_id: str) -> ProcurementRequest:
        request = _load(self.requests, request_id)
        request.approve()
        self.requests.save(request)
        return request


class RejectRequest:
    def __init__(self, requests: RequestRepository):
        self.requests = requests

    def execute(self, request_id: str, reason: str) -> ProcurementRequest:
        request = _load(self.requests, request_id)
        if request.status is not RequestStatus.PENDING_APPROVAL:
            raise InvalidTransition(f"Request {request_id} is not pending approval")
        request.reject(reason)
        self.requests.save(request)
        return request


class SendOrder:
    def __init__(self, requests: RequestRepository, catalog: CatalogRepository, cost_centers: CostCenterRepository):
        self.requests = requests
        self.catalog = catalog
        self.cost_centers = cost_centers

    def execute(self, request_id: str) -> ProcurementRequest:
        request = _load(self.requests, request_id)
        request.ensure_can(RequestStatus.ORDER_SENT)

        supplier = self.catalog.get_supplier(request.item.supplier_id)
        center = self.cost_centers.get(request.cost_center_id)
        if supplier is None or center is None:
            raise NotFound("Supplier or cost center no longer exists")

        now = datetime.now(timezone.utc)
        order = PurchaseOrder(
            po_number=f"PO-{now:%Y%m%d}-{uuid4().hex[:6].upper()}",
            request_id=request.id,
            cost_center_id=center.id,
            supplier=supplier,
            lines=(OrderLine(request.item.sku, request.item.name, request.quantity, request.item.unit_price),),
            created_at=now,
        )
        try:
            center.consume(order.total)
        except ValueError as error:
            raise InvalidTransition(str(error)) from error

        request.mark_sent(order)
        self.cost_centers.save(center)
        self.requests.save(request)
        return request
