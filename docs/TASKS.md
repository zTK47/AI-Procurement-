# TASKS.md

PHASE: 5
STATUS: done

(0=Bootstrap | 1=Specify | 2=Design | 3=Develop | 4=Validate | 5=Deploy)

Iteration goal: Submission-ready on 29.10: evidence, documentation and release v0.1.2.

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
Test counts above are snapshots at that time. Current (28.10, `pytest --collect-only -q`):
37 unit, 20 integration, 4 E2E (API level), 61 in total.

Current strict-catalog iteration (29.10): the seeded catalog contains 110
items across 5 suppliers, including Medion and MediaMarkt with overlapping
offers. Unknown products are rejected with `ITEM_NOT_FOUND`; matching offers
select the cheapest supplier. Focused validation: 60 passed, 4 E2E skipped
without `E2E_BASE_URL`.

## Backlog

- VALIDATE (done 2026-10-27): CI green (structure, 51 tests on Python 3.12,
  Docker build, 3 E2E tests against the container); release v0.1.0 green
  (run 40535225506): image ghcr.io/ztk47/procai:v0.1.0 published and
  publicly pullable, GitHub release created.
- DEPLOY (done 2026-10-27, ADR-002): release v0.1.1 (run 40543462659)
  triggered CD (run 40543771789): Render deploy hook, version check, read-only
  smoke tests green. Production https://ai-procurement-dfjq.onrender.com uses
  claude-haiku-5-5 (live parse confidence 0.95) and Neon PostgreSQL: a request
  created before the deploy was still present afterwards. Limitation: v0.1.1
  had the same commit as the running build, so the version check could not
  show a change yet.
- Documentation: README rewritten for ProcAI (screenshots, architecture,
  run/test/deploy); docs/AI-TOOLING.md (agent, MCP, model selection, AI cost,
  lessons learned); model benchmark script + MODEL-EVALUATION.md.
- Done: LiteLLM gateway integration (client, env variables, unit tests).

### Prioritised backlog (WSJF)

Relative estimates (modified Fibonacci), to be confirmed by the team.
WSJF = cost of delay / job size.

| ID | Item | Cost of delay | Job size | WSJF | Depends on | Source |
|---|---|---|---|---|---|---|
| BL-01 | Stock-aware sourcing (cheapest item with enough stock) | 8 | 2 | 4.0 | - | [ADR-003](adr/ADR-003-sourcing-and-budget-commitment.md) |
| BL-02 | Budget reservation at approval, release on reject | 8 | 3 | 2.7 | BL-07 or a database reset | [ADR-003](adr/ADR-003-sourcing-and-budget-commitment.md) |
| BL-03 | Parser health: report in `/api/health` which parser answered (LLM or rules) and warn on fallback; not persisted per request, no schema change | 5 | 2 | 2.5 | - | [AI-TOOLING.md](AI-TOOLING.md) section 8 |
| BL-04 | Authentication and roles (requester / manager / procurement) | 13 | 8 | 1.6 | - | previous backlog; PROJECT.md out of scope |
| BL-05 | Multi-line requests | 8 | 5 | 1.6 | - | previous backlog |
| BL-06 | AI cost tracking per request | 3 | 3 | 1.0 | - | previous backlog; AI-TOOLING.md section 5 |
| BL-07 | Migration tool (Alembic) | 5 | 5 | 1.0 | - | [ADR-002](adr/ADR-002-deployment-render-neon.md), [ADR-003](adr/ADR-003-sourcing-and-budget-commitment.md) |
| BL-08 | UC-002 Free-text order (offer upload → order request PDF → supplier) | 5 | 8 | 0.6 | - | previous backlog |
| BL-09 | OCI punch-out catalogs | 3 | 13 | 0.2 | - | previous backlog; PROJECT.md out of scope |

### Open items

- Team acceptance of ADR-001 and ADR-002.
- Presentation on 29.10.
- Test gap: low stock with a total above CHF 25,000 (DIRECTOR) is not covered by
  `test_approval_level`; add the case as a characterization test (it documents
  existing behaviour, so it passes immediately and is not a red test). Planned
  for the follow-up pull request.

## Fast Track

- MCP code context (done 2026-10-27): shared, credential-free MCP config in
  `.vscode/mcp.json` and `.mcp.json` (Context7, GitMCP for this repo).
  Reason: SW4 requirement to give the agent code context. Acceptance: both
  servers answer MCP `initialize`; no secrets in tracked files. Checks: JSON
  validated, endpoints probed, `pytest` run. DESIGN skipped: tooling only, no
  application code change.
- Capstone documentation (28.10, branch `chore/capstone-polish`): commits
  `6bf0d83` (AGENTS.md project rules), `622869e` (PROMPTS.md), `33ec56c`
  (README TDD claim), `d693fd9` (AI-TOOLING sections 7–9), `531d43a` (ADR-003
  and the README/PROJECT links), plus this TASKS.md update. Reason: no
  behaviour or public-contract change; ADR-003 is only Proposed and nothing of
  it is implemented. Checks: tests unchanged (no file under `src/`, `tests/`
  or `.github/` changed; the 57 unit and integration tests pass). The AGENTS.md change needs the human
  review of the pull request.

## Definition of Done

- [ ] Acceptance criteria exist in `docs/specs/UC-XXX.md`, or a Fast Track entry exists here.
- [ ] Behaviour changes in domain, application and API start with a failing test (`test:` commit), then `feat:`/`fix:`.
- [ ] Unit, integration and E2E tests pass locally and in CI (`ci.yml`).
- [ ] Dependency rule respected: domain imports only domain; application imports domain and application; interfaces never import infrastructure.
- [ ] Docs updated: spec, `docs/PROJECT.md`, README when behaviour or commands change; an ADR for consequential decisions (Proposed until a human accepts it).
- [ ] Pull request reviewed and merged by the other team member; no secrets in the diff.
- [ ] Release: tag `v*`, green Release run, CD run, `/api/health` shows the released commit; run links saved under VALIDATE/DEPLOY.

Planned, not yet enforced: coverage report in CI, architecture test, linter.

## Working agreement

- Keep one active use case small enough to deliver vertically.
- Update this file when the lifecycle phase or active use case changes.
- Link decisions and validation evidence from the relevant project artefact.
