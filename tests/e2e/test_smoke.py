"""End-to-end smoke tests against a running ProcAI instance (e.g. the Docker image).

Run: E2E_BASE_URL=http://localhost:8000 .venv/bin/python -m pytest tests/e2e
"""

import os

import httpx
import pytest

BASE_URL = os.getenv("E2E_BASE_URL")
pytestmark = pytest.mark.skipif(not BASE_URL, reason="E2E_BASE_URL is not set")


@pytest.fixture(scope="module")
def api():
    with httpx.Client(base_url=BASE_URL, timeout=60) as client:
        yield client


def budget(api, cost_center_id):
    return next(c["budgetRemaining"] for c in api.get("/api/cost-centers").json() if c["id"] == cost_center_id)


def submit(api, prompt):
    response = api.post("/api/requests", json={"prompt": prompt, "costCenterId": "CC-100", "requesterName": "E2E Test"})
    assert response.status_code == 201, response.text
    return response.json()


def test_service_is_healthy_and_serves_the_ui(api):
    assert api.get("/api/health").json()["status"] == "ok"
    page = api.get("/")
    assert page.status_code == 200
    assert "<title>ProcAI" in page.text


def test_auto_approved_order_is_sent_to_supplier(api):
    before = budget(api, "CC-100")

    request = submit(api, "2 Logitech Mouse")
    assert request["status"] == "APPROVED"
    assert request["resolvedData"]["sku"] == "LOG-MX3S"

    sent = api.post(f"/api/requests/{request['requestId']}/send").json()
    assert sent["status"] == "ORDER_SENT"
    assert sent["purchaseOrder"]["total"] == 178.0
    assert budget(api, "CC-100") == pytest.approx(before - 178.0)


def test_large_order_needs_approval_before_it_is_sent(api):
    request = submit(api, "I need 5 new Lenovo Laptop")
    assert request["status"] == "PENDING_APPROVAL"
    assert request["validation"]["approvalLevel"] == "MANAGER"
    assert api.post(f"/api/requests/{request['requestId']}/send").status_code == 409

    assert api.post(f"/api/requests/{request['requestId']}/approve").json()["status"] == "APPROVED"
    assert api.post(f"/api/requests/{request['requestId']}/send").json()["status"] == "ORDER_SENT"

    listed = {r["requestId"]: r["status"] for r in api.get("/api/requests").json()}
    assert listed[request["requestId"]] == "ORDER_SENT"
