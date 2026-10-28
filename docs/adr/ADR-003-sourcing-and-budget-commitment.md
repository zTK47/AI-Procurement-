# ADR-003 Sourcing with stock and budget commitment

Status: Proposed

## Context

The question "what if more than 1 catalog share same product?" came up on our
whiteboard of 26 Sep. The MVP answers it as follows (verified in the code):

- `select_cheapest` in `src/app/domain/rules.py` picks the lowest unit price
  among the matching items and does not look at stock. Low stock only sets
  `stock_ok=False`, which forces an approval (`approval_level`). Stock is never
  reduced when an order is sent.
- `SubmitRequest._process` in `src/app/application/use_cases.py` checks the
  budget at submit time (`request.total <= budget_remaining`); `SendOrder.execute`
  consumes it later via `CostCenter.consume`, which raises `InvalidTransition`
  (HTTP 409) if the budget no longer covers the order.

This creates two risks:

- The cheapest item can be one with too little stock. Seed example: "I need 5
  new Lenovo Laptop" picks LEN-T14-G3 (CHF 1,200, stock 3) instead of
  LEN-X1-C11 (CHF 1,350, stock 20), so it needs approval as a backorder.
- Two requests can both pass the budget check before either one is sent; the
  second is then refused only at send time, after it was already approved.

## Alternatives

Sourcing:

- A – cheapest regardless of stock (today): simple and cheapest; can pick an item that cannot be delivered.
- B – cheapest among items with enough stock: deliverable and still price-driven; may cost more per unit.
- C – split an order over several suppliers: uses all stock; several purchase orders, more complex approval and UI.

Budget:

- A – check at submit, consume at send (today): simple; parallel requests can overbook until send.
- B – reserve at approval, release on reject or cancel: no overbooking; needs a persisted reservation and a cancel step.
- C – check again at send: catches overbooking, but only after the approval was already given.

## Decision

Proposed for the next iteration: sourcing B and budget B. Until it is
implemented, the MVP behaviour above stays and is documented as a known
limitation. Nothing of this decision is implemented yet.

If no matching item has enough stock, keep today's behaviour: resolve the
cheapest matching item, record stock_check = FAILED and require approval
(MANAGER up to CHF 25,000, DIRECTOR above, as in `approval_level`); the
approver decides about a back-order. This matches the example on the
whiteboard of 26 Sep (stockCheck FAILED -> PENDING_APPROVAL).

## Consequences

- A failing test comes first, at rules level (`select_cheapest` with stock) and
  at use-case level (`SubmitRequest`, `ApproveRequest`, `RejectRequest`, `SendOrder`).
- The reservation needs a persisted field or table. There is no migration tool
  ([ADR-002](ADR-002-deployment-render-neon.md)), so the schema change needs either
  a migration step or a database reset.
- `APPROVED` currently allows only `ORDER_SENT`; releasing a reservation on cancel
  needs a new workflow transition.
- Under sourcing B the canonical UC-001 example (5 Lenovo laptops) resolves to
  LEN-X1-C11 instead of LEN-T14-G3, total CHF 6,750 instead of 6,000,
  stockCheck PASSED instead of FAILED, still `PENDING_APPROVAL` at `MANAGER`.
  Acceptance criterion 1 and two tests change:
  `test_catalog_order_resolves_cheapest_item_and_needs_manager_approval` and
  `test_submit_runs_parse_resolve_validate_and_persists`. The E2E test is not
  affected (it checks only status and approval level).
- [UC-001](../specs/UC-001-CATALOG-ORDER.md) must be updated when this is implemented.
- Backlog: BL-01 (sourcing B) and BL-02 (budget B) in
  [docs/TASKS.md](../TASKS.md#prioritised-backlog-wsjf).
