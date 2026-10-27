# TASKS.md

PHASE: 4
STATUS: in-progress

(0=Bootstrap | 1=Specify | 2=Design | 3=Develop | 4=Validate | 5=Deploy)

## Current Use Case

docs/specs/UC-001-CATALOG-ORDER.md — catalog order from a prompt (MVP)

Evidence (2026-10-27): 45 tests pass (`pytest`, unit + integration). Manual
run against the LiteLLM gateway (`azure_ai/claude-haiku-5-5`): English, German
and colloquial prompts parsed and resolved; approve → send produced a purchase
order and reduced the cost center budget. ADR-001 is Proposed and awaits team
acceptance. Data model normalised (7 ORM tables, ≥5 entities); 4 use-case
services; 49 tests pass incl. repository round-trip tests on SQLite.
UI: ProcAI with Requester and Procurement admin views (light blue/white),
checked visually in headless Chrome; click flows to be tested manually.
Requests record the requester name; both admin tables share one layout
(date, reference, requester, department, supplier, item, total, status); 51 tests pass.

## Backlog

- VALIDATE (in progress): Dockerfile, CI with unit + integration tests, release
  workflow (build image → E2E against container → push to GHCR).
  Evidence 2026-10-27: CI run 40532384562 green on feature/uc-001-catalog-order
  (structure, 36 unit + 15 integration tests on Python 3.12, Docker build,
  3 E2E tests against the container). Open: first tagged release (v0.1.0)
  after merge to main, which verifies the GHCR push.
- DEPLOY: Render + Neon PostgreSQL (needs a PostgreSQL driver).
- UC-002 Free-text order (offer upload → order request PDF → supplier).
- OCI punch-out catalogs; multi-line orders; authentication/roles.
- Done: LiteLLM gateway integration (client, env variables, unit tests).

## Fast Track

- MCP code context (done 2026-10-27): shared, credential-free MCP config in
  `.vscode/mcp.json` and `.mcp.json` (Context7, GitMCP for this repo).
  Reason: SW4 requirement to give the agent code context. Acceptance: both
  servers answer MCP `initialize`; no secrets in tracked files. Checks: JSON
  validated, endpoints probed, `pytest` run. DESIGN skipped: tooling only, no
  application code change.

## Working agreement

- Keep one active use case small enough to deliver vertically.
- Update this file when the lifecycle phase or active use case changes.
- Link decisions and validation evidence from the relevant project artefact.
