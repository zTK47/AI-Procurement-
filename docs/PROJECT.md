# PROJECT.md

## Purpose

- Project name: AI Procurement
- User or organisational problem: Ordering goods requires manual forms,
  catalog search and approval chasing. Requesters should describe what they
  need in one prompt and get a validated, auditable purchase order.
- Intended users: Requesters, approvers (managers), procurement.
- In scope (MVP): catalog orders from a natural-language prompt (UC-001),
  LLM parsing through the LiteLLM gateway, budget/stock/approval rules,
  purchase order generation, web UI.
- Out of scope: free-text orders, OCI punch-out catalogs, ERP/SAP
  integration, goods receipt, authentication, committing credentials.

## Architecture

Clean Architecture in `src/app`, dependencies point inward:

`domain ← application ← interfaces ← infrastructure`

- `domain`: entities (`ProcurementRequest`, `CatalogItem`, `Supplier`,
  `CostCenter`, `PurchaseOrder`), value objects (`Money`, `Quantity`, `Sku`),
  `ParsedRequest`, workflow states, sourcing and approval rules.
- `application`: ports (`RequestParser`, repositories) and use cases
  (`SubmitRequest`, `ApproveRequest`, `RejectRequest`, `SendOrder`).
- `interfaces`: FastAPI router, request/response schemas, static UI.
- `infrastructure`: LiteLLM and rule-based parsers, SQLAlchemy repositories,
  seed data, wiring (`main.py`).

### Data model (SQLite + SQLAlchemy ORM)

| Entity (domain) | Table | Relations |
|---|---|---|
| `Supplier` | `suppliers` | 1:n catalog items, purchase orders |
| `CatalogItem` | `catalog_items` | n:1 supplier |
| `CostCenter` | `cost_centers` | 1:n requests |
| `ProcurementRequest` | `procurement_requests` | n:1 cost center, n:1 catalog item |
| Status history | `request_status_history` | n:1 request (audit trail) |
| `PurchaseOrder` | `purchase_orders` | 1:1 request, n:1 supplier |
| `OrderLine` | `purchase_order_lines` | n:1 purchase order, n:1 catalog item |

ER diagram and relationships: [DATA-MODEL.md](DATA-MODEL.md). Amounts are `NUMERIC(12,2)`. `DATABASE_URL` switches to PostgreSQL without code changes.

### Use-case services (application layer)

| Service | Purpose |
|---|---|
| `SubmitRequest` | Prompt → parse → resolve cheapest item → validate → approve or route |
| `ApproveRequest` / `RejectRequest` | Approver decision on a pending request |
| `SendOrder` | Create purchase order, consume budget, mark `ORDER_SENT` |

Decisions: [ADR-001](adr/ADR-001-catalog-order-mvp-architecture.md).

## Structure

| Path | Content |
|---|---|
| `src/app/` | Application (layers above) |
| `tests/unit/` | Domain and use-case tests (no network, no DB) |
| `tests/integration/` | API tests with SQLite and a fake parser |
| `tests/e2e/` | Smoke tests against a running container (`E2E_BASE_URL`) |
| `docs/specs/` | Use cases |
| `docs/adr/` | Architecture decisions |

## Commands

| Activity | Command |
|---|---|
| Install | `bash scripts/setup-python.sh` |
| Create demo DB | `.venv/bin/python scripts/init_db.py --reset` → `procurement.db` |
| Unit tests | `.venv/bin/python -m pytest tests/unit` |
| Integration tests | `.venv/bin/python -m pytest tests/integration` |
| E2E tests | `E2E_BASE_URL=http://localhost:8000 .venv/bin/python -m pytest tests/e2e` (needs a running instance) |
| Docker | `docker build -t procai .` then `docker run --rm -p 8000:8000 --env-file .env procai` |
| Run locally | `.venv/bin/uvicorn app.main:create_app --factory --reload --app-dir src` → http://localhost:8000 |
| CI | `.github/workflows/ci.yml`: structure check + unit/integration tests on every push and PR |
| Build/release | Push a tag `vX.Y.Z` → `release.yml` runs tests, builds the image, runs E2E against the container, pushes `ghcr.io/<owner>/procai`, creates the GitHub release |

## Dependencies

Declared in `requirements.txt` / `environments/python/requirements.txt`
(FastAPI, uvicorn, SQLAlchemy, LiteLLM, python-dotenv, pytest, httpx).
Environment variables: `LITELLM_API_BASE`, `LITELLM_API_KEY`, optional
`LITELLM_MODEL`, optional `DATABASE_URL` (default `sqlite:///./procurement.db`),
optional `PARSER` (`llm` default, `rules` to skip the LLM). Never commit secrets.
