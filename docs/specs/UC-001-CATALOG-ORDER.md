# UC-001-CATALOG-ORDER

## Intent
A requester orders catalog goods by writing one natural-language prompt. The
system turns it into a validated purchase request and a purchase order that
is ready to send to the supplier, without manual form filling.

## Scope

IN: catalog orders with one line item, rule-based approval, sending the purchase order.

OUT (backlog in [docs/TASKS.md](../TASKS.md#prioritised-backlog-wsjf)): free-text
orders (BL-08), multi-line requests (BL-05), authentication and roles (BL-04),
OCI punch-out (BL-09), stock-aware sourcing (BL-01), budget reservation (BL-02).

## Actors

Primary: Requester (employee with a cost center)
Secondary: Procurement admin (approves on behalf of MANAGER/DIRECTOR, releases
the purchase order), LLM via LiteLLM gateway, Supplier

Views (ProcAI web UI): Requester view (prompt + track own requests) and
Procurement admin view (KPIs, action queue with approve/reject/send, all
requests with date and status Requested/Approved/Ordered/Rejected, purchase
orders). No authentication in the MVP; the view is chosen in the UI.

## Preconditions

- Catalog items, suppliers and cost centers exist (seeded master data).
- The requester selects a cost center.

## Flow

1. Requester submits a prompt, e.g. "I need 5 new Lenovo Laptop", and a cost center.
2. System stores the request (`CREATED`).
3. Parser extracts quantity, product name and category with a confidence (`PARSED`).
   The LLM parser is used; if the gateway is unavailable a rule-based parser is used.
4. System resolves the catalog item from the internal catalog. If several
   supplier offers match, the cheapest unit price wins (sourcing rule)
   (`RESOLVED`). Products outside the catalog are rejected.
5. System validates: budget (total ≤ cost center remaining budget) and stock
   (quantity ≤ stock) (`VALIDATED`).
6. Every resolved request enters `PENDING_APPROVAL`. Procurement decides
   whether to approve or reject it; budget and stock results remain visible for
   that decision.
7. Procurement admin approves (`APPROVED`) or rejects (`REJECTED`) with a reason.
8. Procurement admin sends the order from the Procurement view: a purchase order
   document is generated for the supplier, the budget is consumed (`ORDER_SENT`).
   The API endpoint `POST /api/requests/{id}/send` does not check roles (BL-04).

Every state change is appended to the request history.

## Errors

- empty prompt or unknown cost center → 422 / 404
- quantity or product not recognised → `REJECTED`, reason `PARSE_FAILED`
- no matching catalog item → `REJECTED`, reason `ITEM_NOT_FOUND`
- budget exceeded → `PENDING_APPROVAL` with a failed budget check
- approve/reject/send in the wrong state → 409
- unknown request id → 404

## Non-functional requirements

- Money is `Decimal` (`Money` value object) in the domain and in persistence.
- The LLM only parses the prompt; all decisions are deterministic code ([ADR-001](../adr/ADR-001-catalog-order-mvp-architecture.md)).
- If the gateway fails, the rule-based parser takes over (`FallbackParser`).
- Secrets only in `.env`, Render and GitHub secrets ([ADR-002](../adr/ADR-002-deployment-render-neon.md)).
- `/api/health` reports status, deployed version and the configured parser.

## Acceptance

Given the catalog contains two Lenovo laptops (1,200 and 1,350 CHF)
When the requester submits "I need 5 new Lenovo Laptop" for cost center CC-100
Then the request resolves to the 1,200 CHF item, total 6,000 CHF,
budget check passes and the request is `PENDING_APPROVAL` at level `MANAGER`

Given a pending request
When the procurement admin approves it (MANAGER level) and sends it from the Procurement view
Then the state is `ORDER_SENT`, a purchase order for the supplier exists and
the cost center budget is reduced by the total

Given a prompt for a product that is not in the catalog
When it is submitted
Then the request is `REJECTED` with reason `ITEM_NOT_FOUND`

## Tests

Unit: value objects, sourcing rule, approval rule, state transitions,
rule-based parser, use cases with in-memory repositories
Integration: FastAPI endpoints with SQLite repositories and a fake parser
E2E (API level, `tests/e2e/test_smoke.py`): health and UI served, master data,
catalog order approval and sending; runs against the Docker container in CI and
Release, the read-only subset against production after each deploy. No
browser/UI tests; the UI is checked manually.
