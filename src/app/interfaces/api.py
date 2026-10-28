"""FastAPI interface: REST endpoints and DTO mapping for UC-001."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field, field_validator

from app.application.ports import CatalogRepository, CostCenterRepository, RequestRepository
from app.application.use_cases import ApproveRequest, NotFound, RejectRequest, SendOrder, SubmitRequest
from app.domain.entities import InvalidTransition, ProcurementRequest
from app.domain.value_objects import Money

STATIC_DIR = Path(__file__).parent / "static"


@dataclass
class Services:
    submit: SubmitRequest
    approve: ApproveRequest
    reject: RejectRequest
    send: SendOrder
    catalog: CatalogRepository
    cost_centers: CostCenterRepository
    requests: RequestRepository
    parser_name: str


class SubmitBody(BaseModel):
    prompt: str = Field(max_length=1000)
    costCenterId: str
    requesterName: str = Field(max_length=100)
    unitPrice: float | None = Field(default=None, gt=0)

    @field_validator("prompt", "requesterName")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Must not be empty")
        return value.strip()


class RejectBody(BaseModel):
    reason: str = Field(default="Rejected by approver", min_length=1, max_length=200)


def _amount(money: Money | None) -> float | None:
    return float(money.amount) if money else None


def request_dto(request: ProcurementRequest) -> dict:
    parsed, item, order = request.parsed, request.item, request.purchase_order
    return {
        "requestId": request.id,
        "status": request.status.value,
        "rawText": request.raw_text,
        "requesterName": request.requester,
        "costCenterId": request.cost_center_id,
        "createdAt": request.created_at.isoformat(),
        "parsedData": None if parsed is None else {
            "quantity": parsed.quantity,
            "productName": parsed.product_name,
            "category": parsed.category,
            "confidence": parsed.confidence,
        },
        "resolvedData": None if item is None else {
            "sku": item.sku.value,
            "name": item.name,
            "supplierId": item.supplier_id,
            "unitPrice": _amount(item.unit_price),
            "currency": item.unit_price.currency,
            "stock": item.stock,
            "total": _amount(request.total),
        },
        "validation": None if request.budget_check is None else {
            "budgetCheck": request.budget_check,
            "stockCheck": request.stock_check,
            "requiresApproval": request.requires_approval,
            "approvalLevel": request.approval_level,
        },
        "workflow": {"currentState": request.status.value, "history": request.history},
        "rejectionReason": request.rejection_reason,
        "purchaseOrder": None if order is None else {
            "poNumber": order.po_number,
            "createdAt": order.created_at.isoformat(),
            "costCenterId": order.cost_center_id,
            "supplier": {"id": order.supplier.id, "name": order.supplier.name, "email": order.supplier.email},
            "lines": [
                {
                    "sku": line.sku.value,
                    "description": line.description,
                    "quantity": line.quantity.value,
                    "unitPrice": _amount(line.unit_price),
                    "lineTotal": _amount(line.line_total),
                }
                for line in order.lines
            ],
            "total": _amount(order.total),
            "currency": order.total.currency,
        },
    }


router = APIRouter(prefix="/api")


def _services(http_request: Request) -> Services:
    return http_request.app.state.services


@router.get("/health")
def health(http_request: Request):
    version = os.getenv("APP_VERSION") or os.getenv("RENDER_GIT_COMMIT") or "dev"
    return {"status": "ok", "version": version, "parser": _services(http_request).parser_name}


@router.get("/cost-centers")
def list_cost_centers(http_request: Request):
    return [
        {"id": c.id, "name": c.name, "budgetRemaining": _amount(c.budget_remaining), "currency": c.budget_remaining.currency}
        for c in _services(http_request).cost_centers.list_all()
    ]


@router.get("/suppliers")
def list_suppliers(http_request: Request):
    return [{"id": s.id, "name": s.name, "email": s.email} for s in _services(http_request).catalog.list_suppliers()]


@router.get("/catalog")
def list_catalog(http_request: Request):
    return [
        {"sku": i.sku.value, "name": i.name, "category": i.category, "supplierId": i.supplier_id,
         "unitPrice": _amount(i.unit_price), "currency": i.unit_price.currency, "stock": i.stock}
        for i in _services(http_request).catalog.list_items()
    ]


@router.get("/requests")
def list_requests(http_request: Request):
    return [request_dto(r) for r in _services(http_request).requests.list_recent()]


@router.post("/requests", status_code=201)
def submit_request(body: SubmitBody, http_request: Request):
    from decimal import Decimal
    return request_dto(_services(http_request).submit.execute(
        body.prompt, body.costCenterId, body.requesterName,
        Decimal(str(body.unitPrice)) if body.unitPrice is not None else None,
    ))


@router.get("/requests/{request_id}")
def get_request(request_id: str, http_request: Request):
    request = _services(http_request).requests.get(request_id)
    if request is None:
        raise NotFound(f"Request {request_id} not found")
    return request_dto(request)


@router.post("/requests/{request_id}/approve")
def approve_request(request_id: str, http_request: Request):
    return request_dto(_services(http_request).approve.execute(request_id))


@router.post("/requests/{request_id}/reject")
def reject_request(request_id: str, http_request: Request, body: RejectBody | None = None):
    return request_dto(_services(http_request).reject.execute(request_id, (body or RejectBody()).reason))


@router.post("/requests/{request_id}/send")
def send_order(request_id: str, http_request: Request):
    return request_dto(_services(http_request).send.execute(request_id))


def install(app: FastAPI, services: Services) -> None:
    app.state.services = services
    app.include_router(router)

    @app.exception_handler(NotFound)
    def not_found(_, error: NotFound):
        return JSONResponse(status_code=404, content={"detail": str(error)})

    @app.exception_handler(InvalidTransition)
    def conflict(_, error: InvalidTransition):
        return JSONResponse(status_code=409, content={"detail": str(error)})

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(STATIC_DIR / "index.html")
