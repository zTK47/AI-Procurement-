# Prompt log and traceability

## Purpose

This log shows how the coding agent (Claude Code) was prompted and what each
prompt produced. Prompts, specs, tests and commits form one traceable chain:
spec → failing test → implementation → evidence (CI runs, releases, live checks).

Sources: the git history (`git log`, commits with a `Co-Authored-By: Claude`
trailer) and the Claude Code session transcript of this repository (user
messages only, secrets redacted). Dates are from 27–28 October 2026.

Note on timing: the commits `af34f4e` … `3c24f36` were created within 30
seconds at 16:32 on 27.10, after the work in the session. Their order follows
the lifecycle (spec → red → green → UI); their timestamps do not show when
each step happened. Later branches were committed step by step.
TDD evidence from the transcript (UTC, 27.10): the first UC-001 run at 13:56:38 failed with 4 collection errors because the tested modules did not exist yet (red); the full suite passed at 14:01:13 with 44 tests (green).

TODO(human): only one transcript exists (this repository, one session). Add
prompts from other team members' coding-agent sessions, if there were any.

## Prompt log

| # | Phase | Prompt | Result (commits) | Human decision or correction |
|---|---|---|---|---|
| 1 | 1 Specify | Develop an AI procurement solution inspired by Lio and lhotse: a user writes a prompt and the LLM generates the order to send; focus on the catalog order; two-colour palette; "first implementation is just mvp" (summary) | `31a1917` UC-001 + ADR-001 | Scope limited to catalog orders (MVP); whiteboard sketches provided as input |
| 2 | 2 Design | "Database SQL lite + ORM, at least 5 entities and at least 2 use cases as services (brief)." | `31a1917` data model in PROJECT.md, `718ccb0` repository tests (red), `b1f1b5e` 7 ORM tables (green) | Requirement taken from the grading criteria |
| 3 | 2 Design | "we don't havae the database in the repository can you create a procurement.db in SQLite we need a datamodeler with relationship between the entities" | `31a1917` DATA-MODEL.md, ER diagram, schema.sql; `3c24f36` scripts/init_db.py + procurement.db | Demo database committed on purpose (`.gitignore` exception) (untracked again in `9c9d525`) |
| 4 | 3 Develop | "implementeted the use case in the UI to test we need 2 views, a userv view, and procurement admin view. chose 2 colors light blue and white get inspire from https://lhotse.de/en/ and https://www.lio.ai and name it the website ProcAI" | `718ccb0` UI test (red), `3c24f36` UI (green) | Two views, light blue/white palette, name "ProcAI" |
| 5 | 3 Develop | Shorten the requester text, remove the detail panel and the catalog section, add a date column, limit statuses to Requested/Approved/Ordered/Rejected with red for Rejected only, add requester, department and supplier columns, same structure for both tables (summary of three prompts) | `718ccb0` requester-name tests (red), `b1f1b5e` `requester_name` column + `/api/suppliers` (green), `3c24f36` UI | Human corrected the agent's first UI draft three times |
| 6 | — (Fast Track) | "this is the key API model litellm https://litellm.engines.aisl.science/ this is our base URL - we have to add the MCP to the repository" (key `<redacted>`) | `af34f4e` .mcp.json, .vscode/mcp.json, .env.example | MCP was a course requirement (TASKS.md Fast Track); key kept out of git |
| 7 | 4 Validate | "Today: commit and push in meaningful steps (docs → tests → implementation → UI) … Make CI run the unit and integration tests on every push and pull request … Add a Dockerfile, and have the release workflow build the image, publish it to GitHub Packages and run an E2E smoke test against the container … can you implemement this points carefully" | `af34f4e`…`3c24f36`, `4f6f476` CI tests, `cb116cc` Dockerfile + E2E + release, `3b69dc6` container job in CI, `31379fe` evidence | PR #1 merged by Elpidio (`0c82ee2`) |
| 8 | 4 Validate | "push the tag 0.1.0." (summary of a longer message) | tag `v0.1.0` on `0c82ee2` | Release authorized by the human; named `v0.1.0` because `release.yml` triggers on `v*` |
| 9 | 5 Deploy | "how can i connect render and neon deployment", followed by a pasted Render deploy log (summary) | `236d089` ADR-002, `07bd58b` tests (red), `0324a44` PostgreSQL driver + version in health (green), `1109b36` cd.yml | PR #2 merged by Elpidio (`7cc5dd9`); Render and Neon accounts and settings created by the human |
| 10 | 5 Deploy | "done" (after the step-by-step Render/Neon/GitHub settings guide) | tag `v0.1.1` on `7cc5dd9`; evidence recorded in `10eb67e` (TASKS.md) | Human configured Render environment and GitHub secrets; agent verified the live app |
| 11 | 4 Validate | Assess the AI cost on LiteLLM: the virtual key had spent only 5 cents; which models to use and how to get a cost overview (summary) | `950b7bf` benchmark script + MODEL-EVALUATION.md, `74144e7` AI cost in AI-TOOLING.md | TODO(human): confirm the team accepts Claude Haiku 5.5 as the product model |
| 12 | 4 Validate | "let's implement the point 5 and 6.- about the agent our application is showing AI claude haiku 5-5. we set our AI agent default and mainly claude code" | `950b7bf`, `74144e7` AI-TOOLING.md, `10eb67e` README | Human stated the tools used (Claude Code); PR #3 merged by Elpidio (`f9aebe6`) |

## Corrections after the agent's first answer

- Claude Haiku 5.5 rejected `temperature=0`; only a live run showed it because the rule-based fallback hid the error. The parser calls the model without `temperature` (`b1f1b5e`; [AI-TOOLING.md](AI-TOOLING.md) section 6).
- The LiteLLM SDK treated `azure_ai/…` as a direct Azure call instead of a call to our proxy; also found only live. Regression test `test_complete_routes_through_the_openai_compatible_gateway` (`718ccb0`), fix with the `openai/<model>` prefix (`b1f1b5e`).
- Docker was not available locally, so the Dockerfile was first built in GitHub Actions; a container job was added to CI to verify it before merging (`3b69dc6`).
- The first UI draft was corrected by the human in three rounds (prompt 5): panels removed, statuses and colours limited, columns added (`3c24f36`).
- The AGENTS.md project rules were reworded by the human before the commit (Money and TDD bullets, Definition of Done link) (`6bf0d83`).

## UC-001 → tests

Acceptance criteria from [UC-001](specs/UC-001-CATALOG-ORDER.md); test names from `pytest --collect-only -q`.

| Acceptance criterion | Test function | File | Level |
|---|---|---|---|
| AC1: "I need 5 new Lenovo Laptop" resolves to the 1,200 CHF item, total 6,000 CHF, budget passes, `PENDING_APPROVAL` at `MANAGER` | `test_catalog_order_resolves_cheapest_item_and_needs_manager_approval` | tests/integration/test_catalog_order_api.py | integration |
| AC1 | `test_submit_runs_parse_resolve_validate_and_persists` | tests/unit/test_use_cases.py | unit |
| AC1 | `test_matching_uses_all_product_tokens_and_ignores_plural` | tests/unit/test_domain.py | unit |
| AC1 | `test_approval_level` | tests/unit/test_domain.py | unit |
| AC1 | `test_large_order_needs_approval_before_it_is_sent` | tests/e2e/test_smoke.py | e2e |
| AC2: a pending request, approved and sent, is `ORDER_SENT`, a purchase order exists, the budget is reduced by the total | `test_approved_request_is_sent_as_purchase_order_and_consumes_budget` | tests/integration/test_catalog_order_api.py | integration |
| AC2 | `test_approve_reject_and_send` | tests/unit/test_use_cases.py | unit |
| AC2 | `test_sent_request_round_trips_with_history_and_purchase_order` | tests/integration/test_sql_repositories.py | integration |
| AC2 | `test_large_order_needs_approval_before_it_is_sent` (status only, budget not checked) | tests/e2e/test_smoke.py | e2e |
| AC3: a product not in the catalog is `REJECTED` with reason `ITEM_NOT_FOUND` | `test_unknown_product_is_rejected` | tests/integration/test_catalog_order_api.py | integration |
| AC3 | `test_matching_returns_nothing_for_unknown_product` | tests/unit/test_domain.py | unit |
