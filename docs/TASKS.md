# TASKS.md

PHASE: 5
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

- VALIDATE (done 2026-10-27): CI green (structure, 51 tests on Python 3.12,
  Docker build, 3 E2E tests against the container); release v0.1.0 green
  (run 40535225506): image ghcr.io/ztk47/procai:v0.1.0 published and
  publicly pullable, GitHub release created.
- DEPLOY (in progress, ADR-002): Render live at
  https://ai-procurement-dfjq.onrender.com (read-only smoke tests green);
  PostgreSQL driver + release-gated cd.yml added. Open: Neon DATABASE_URL and
  LiteLLM env vars in Render, deploy hook secret, release v0.1.1 via CD.
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
