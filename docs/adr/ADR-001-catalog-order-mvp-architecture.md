# ADR-001 Catalog order MVP architecture

Status: Proposed

## Context

UC-001 turns a natural-language prompt into a validated purchase order. The
MVP must run without a working LLM key (demo, CI) and stay small enough to
deliver as one vertical slice.

## Alternatives

- LLM does everything (parse, resolve, validate): flexible, but not auditable
  and not testable deterministically.
- Rule-based parsing only: deterministic, but no natural-language robustness.
- Separate SPA frontend (React): nicer UI, but a second build and deployment.

## Decision

- The LLM only **parses** the prompt into a `ParsedRequest` (pydantic-validated
  JSON). Resolution, budget, stock and approval are deterministic domain rules.
- A `RequestParser` port has two adapters: `LiteLLMParser` (gateway) and
  `RuleBasedParser`; a fallback adapter uses the rule-based parser when the
  LLM call fails.
- Sourcing rule: when several catalog items match, the cheapest unit price wins.
- Approval: auto-approve ≤ 1,000 CHF with stock; otherwise MANAGER (≤ 25,000 CHF)
  or DIRECTOR.
- Persistence: SQLAlchemy 2 ORM with `DATABASE_URL` (SQLite locally, PostgreSQL
  in the cloud), normalised into 7 tables with foreign keys (requests, status
  history, purchase orders and order lines are relational, not JSON); master
  data seeded at start-up. No migrations tool yet (`create_all`).
- UI: one static HTML page served by FastAPI, two-colour palette.

## Consequences

- Business rules are unit-testable without network access.
- The LLM can be swapped through the gateway (`LITELLM_MODEL`) without code change.
- Free-text and punch-out catalogs remain out of scope and can reuse the
  parser port later.
