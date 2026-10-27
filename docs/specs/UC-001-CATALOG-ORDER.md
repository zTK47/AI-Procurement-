# UC-001-CATALOG-ORDER

## Intent
A requester orders catalog goods by writing one natural-language prompt. The
system turns it into a validated purchase request and a purchase order that
is ready to send to the supplier, without manual form filling.

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
4. System resolves the catalog item. If several items match, the cheapest
   unit price wins (sourcing rule) (`RESOLVED`).
5. System validates: budget (total ≤ cost center remaining budget) and stock
   (quantity ≤ stock) (`VALIDATED`).
6. Approval rule: total ≤ 1,000 CHF and stock available → `APPROVED`
   automatically; otherwise `PENDING_APPROVAL` with level `MANAGER`
   (total ≤ 25,000 CHF) or `DIRECTOR`.
7. Procurement admin approves (`APPROVED`) or rejects (`REJECTED`) with a reason.
8. Procurement admin sends the order: a purchase order document is generated for the
   supplier, the budget is consumed (`ORDER_SENT`).

Every state change is appended to the request history.

## Errors

- empty prompt or unknown cost center → 422 / 404
- quantity or product not recognised → `REJECTED`, reason `PARSE_FAILED`
- no matching catalog item → `REJECTED`, reason `ITEM_NOT_FOUND`
- budget exceeded → `REJECTED`, reason `BUDGET_EXCEEDED`
- approve/reject/send in the wrong state → 409
- unknown request id → 404

## Acceptance

Given the catalog contains two Lenovo laptops (1,200 and 1,350 CHF)
When the requester submits "I need 5 new Lenovo Laptop" for cost center CC-100
Then the request resolves to the 1,200 CHF item, total 6,000 CHF,
budget check passes and the request is `PENDING_APPROVAL` at level `MANAGER`

Given a pending request
When the manager approves it and the requester sends it
Then the state is `ORDER_SENT`, a purchase order for the supplier exists and
the cost center budget is reduced by the total

Given a prompt for a product that is not in the catalog
When it is submitted
Then the request is `REJECTED` with reason `ITEM_NOT_FOUND`

## Tests

Unit: value objects, sourcing rule, approval rule, state transitions,
rule-based parser, use cases with in-memory repositories
Integration: FastAPI endpoints with SQLite repositories and a fake parser
E2E: out of scope for the MVP (UI checked manually)
