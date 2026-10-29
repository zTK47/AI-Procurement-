# AGENTS.md — AI-SDLC Router

Repository state lives in:

docs/TASKS.md

Maintain `docs/TASKS.md`: PHASE = selected phase; STATUS = ready, in-progress,
done or blocked. Set in-progress on entry, done only after the phase output is
verified, or blocked with a reason. Keep PHASE on completion; an explicitly
selected next phase starts as ready. Changes to this router require human review.

---

Phases may be **skipped or repeated**.

Typical iteration:

SPECIFY → DESIGN → DEVELOP → VALIDATE  
VALIDATE → SPECIFY (iteration)  
DEPLOY → SPECIFY (feedback)

---

## Fast Track

- Small corrections only; no feature, API, data, security, dependency or architecture changes.
- Record scope, reason, acceptance and checks in the existing UC or `docs/TASKS.md`.
- Shorten SPECIFY; skip DESIGN with a reason. Scope grows → regular flow.
- Keep required CI and review. Release/deployment still require authorization.

## Collaboration

- Human-approved decisions → ADR; current architecture → `docs/PROJECT.md`.
- Durable rules + ADR links → `AGENTS.md`, with human approval/review.
- Update related files together; preserve decision history and reconcile parallel changes.

## Context Load Order

1. docs/TASKS.md  
2. docs/PROJECT.md  
3. docs/specs/UC-[NNN]-[NAME].md (or the eligible Fast Track task entry)

---

## Phase → Skill

0 → skills/ai-sdlc-0-bootstrap  
1 → skills/ai-sdlc-1-specify  
2 → skills/ai-sdlc-2-design  
3 → skills/ai-sdlc-3-develop  
4 → skills/ai-sdlc-4-validate  
5 → skills/ai-sdlc-5-deploy  

---

## Commands

Use the project-specific install, test, run and release commands documented in
`docs/PROJECT.md`. Do not assume a language, framework or deployment platform
before the project context has been completed.

---

## Rules

- Use the language of the current user prompt for all communication and all
  natural-language artifacts. Do not default to the language of earlier
  messages.
- Update existing artifacts; create only what is missing.
- Keep artifacts **minimal**.
- Avoid unnecessary comments in code.
- Follow **TDD** (tests before code).
- Respect **Clean Architecture**  
  domain ← application ← interfaces ← infrastructure
- Prefer **small vertical slices** (one UC end-to-end).
- Read the [canonical AI-SDLC documentation](https://docs.aisl.science/learning-and-resources/ai-sdlc)
  when terminology or lifecycle responsibilities are unclear.

## Project rules (ProcAI)

- The LLM only parses a prompt into a `ParsedRequest`; sourcing, budget, stock
  and approval are deterministic domain rules ([ADR-001](docs/adr/ADR-001-catalog-order-mvp-architecture.md)).
- Money is `Decimal` (`Money` value object) in the domain and in persistence;
  amounts become `float` only in the JSON responses of the API.
- Behaviour changes in domain, application and API start with a failing test
  (`test:` commit), then `feat:`/`fix:`.
- Dependencies point inward: `domain` imports nothing outside `domain`;
  `interfaces` never imports `infrastructure`.
- Merges, release tags and deployments need explicit human approval; secrets
  live only in `.env`, Render and GitHub secrets ([ADR-002](docs/adr/ADR-002-deployment-render-neon.md)).
- A task is done only when the
  [Definition of Done](docs/TASKS.md#definition-of-done) in `docs/TASKS.md` is met.
- Decisions that cost something (rules, schema, deployment) get an ADR in `docs/adr/`.

If requirements or architecture are unclear → ask the user.
