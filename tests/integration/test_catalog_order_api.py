import pytest
from fastapi.testclient import TestClient

from app.domain.entities import ParsedRequest
from app.main import create_app


class FakeParser:
    def __init__(self):
        self.results = {
            "I need 5 new Lenovo Laptop": ParsedRequest(5, "Lenovo Laptop", "Laptop", 0.95),
            "2 mice please": ParsedRequest(2, "Mouse", "Accessories", 0.9),
            "I need 3 Commodore 64": ParsedRequest(3, "Commodore 64", "Computer", 0.8),
            "something nice": ParsedRequest(None, "", None, 0.1),
        }

    def parse(self, text):
        return self.results[text]


@pytest.fixture
def client():
    app = create_app(parser=FakeParser(), database_url="sqlite://")
    with TestClient(app) as test_client:
        yield test_client


def submit(client, prompt, cost_center="CC-100", requester="Anna Keller"):
    return client.post("/api/requests", json={"prompt": prompt, "costCenterId": cost_center, "requesterName": requester})


def test_catalog_order_resolves_cheapest_item_and_needs_manager_approval(client):
    response = submit(client, "I need 5 new Lenovo Laptop")

    assert response.status_code == 201
    body = response.json()
    assert body["requestId"].startswith("req-")
    assert body["status"] == "PENDING_APPROVAL"
    assert body["parsedData"] == {
        "quantity": 5,
        "productName": "Lenovo Laptop",
        "category": "Laptop",
        "confidence": 0.95,
    }
    assert body["resolvedData"]["sku"] == "LEN-T14-G3"
    assert body["resolvedData"]["unitPrice"] == 1200.0
    assert body["resolvedData"]["total"] == 6000.0
    assert body["resolvedData"]["currency"] == "CHF"
    assert body["validation"] == {
        "budgetCheck": "PASSED",
        "stockCheck": "FAILED",
        "requiresApproval": True,
        "approvalLevel": "MANAGER",
    }
    assert body["workflow"]["history"] == [
        "CREATED", "PARSED", "RESOLVED", "VALIDATED", "PENDING_APPROVAL",
    ]


def test_approved_request_is_sent_as_purchase_order_and_consumes_budget(client):
    request_id = submit(client, "I need 5 new Lenovo Laptop").json()["requestId"]
    budget_before = _budget(client, "CC-100")

    assert client.post(f"/api/requests/{request_id}/approve").json()["status"] == "APPROVED"
    sent = client.post(f"/api/requests/{request_id}/send")

    assert sent.status_code == 200
    body = sent.json()
    assert body["status"] == "ORDER_SENT"
    order = body["purchaseOrder"]
    assert order["poNumber"].startswith("PO-")
    assert order["supplier"]["id"] == "SUP-001"
    assert order["lines"] == [
        {"sku": "LEN-T14-G3", "description": "Lenovo ThinkPad T14 Gen 3",
         "quantity": 5, "unitPrice": 1200.0, "lineTotal": 6000.0},
    ]
    assert order["total"] == 6000.0
    assert _budget(client, "CC-100") == budget_before - 6000.0


def test_small_order_in_stock_is_approved_automatically(client):
    body = submit(client, "2 mice please").json()

    assert body["status"] == "APPROVED"
    assert body["validation"]["requiresApproval"] is False
    assert body["validation"]["approvalLevel"] is None


def test_unknown_product_is_rejected(client):
    body = submit(client, "I need 3 Commodore 64").json()

    assert body["status"] == "REJECTED"
    assert body["rejectionReason"] == "ITEM_NOT_FOUND"


def test_unparseable_prompt_is_rejected(client):
    body = submit(client, "something nice").json()

    assert body["status"] == "REJECTED"
    assert body["rejectionReason"] == "PARSE_FAILED"


def test_budget_exceeded_is_rejected(client):
    body = submit(client, "I need 5 new Lenovo Laptop", cost_center="CC-300").json()

    assert body["status"] == "REJECTED"
    assert body["rejectionReason"] == "BUDGET_EXCEEDED"
    assert body["validation"]["budgetCheck"] == "FAILED"


def test_manager_can_reject_pending_request(client):
    request_id = submit(client, "I need 5 new Lenovo Laptop").json()["requestId"]

    body = client.post(f"/api/requests/{request_id}/reject", json={"reason": "Use refurbished"}).json()

    assert body["status"] == "REJECTED"
    assert body["rejectionReason"] == "Use refurbished"


def test_sending_unapproved_request_is_a_conflict(client):
    request_id = submit(client, "I need 5 new Lenovo Laptop").json()["requestId"]

    assert client.post(f"/api/requests/{request_id}/send").status_code == 409


def test_unknown_request_and_cost_center_return_404(client):
    assert client.get("/api/requests/req-missing").status_code == 404
    assert submit(client, "I need 5 new Lenovo Laptop", cost_center="CC-999").status_code == 404


def test_empty_prompt_is_invalid(client):
    assert submit(client, "   ").status_code == 422


def test_request_records_the_requester_name(client):
    body = submit(client, "2 mice please", requester="  Marco Rossi ").json()

    assert body["requesterName"] == "Marco Rossi"
    assert client.get(f"/api/requests/{body['requestId']}").json()["requesterName"] == "Marco Rossi"


def test_requester_name_is_required(client):
    assert submit(client, "2 mice please", requester=" ").status_code == 422


def test_requests_are_listed_newest_first(client):
    first = submit(client, "2 mice please").json()["requestId"]
    second = submit(client, "I need 5 new Lenovo Laptop").json()["requestId"]

    ids = [item["requestId"] for item in client.get("/api/requests").json()]

    assert ids[:2] == [second, first]
    assert client.get(f"/api/requests/{first}").json()["requestId"] == first


def test_master_data_endpoints(client):
    assert {c["id"] for c in client.get("/api/cost-centers").json()} >= {"CC-100", "CC-200", "CC-300"}
    assert any(item["sku"] == "LEN-T14-G3" for item in client.get("/api/catalog").json())
    assert {"id": "SUP-001", "name": "Alpine IT Distribution AG", "email": "orders@alpine-it.example"} in client.get("/api/suppliers").json()


def test_health_reports_the_deployed_version(client, monkeypatch):
    monkeypatch.setenv("APP_VERSION", "abc1234")

    assert client.get("/api/health").json()["version"] == "abc1234"


def test_ui_is_served(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<title>ProcAI" in response.text
    assert 'id="view-user"' in response.text
    assert 'id="view-admin"' in response.text


def _budget(client, cost_center_id):
    return next(c["budgetRemaining"] for c in client.get("/api/cost-centers").json() if c["id"] == cost_center_id)
