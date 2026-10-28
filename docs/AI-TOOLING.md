# AI tooling, model selection and AI cost

How AI was used to **build** ProcAI and how AI is used **inside** ProcAI.

| Role | Tool / model | Where |
|---|---|---|
| Coding agent (builds the software) | **Claude Code** with **Claude Opus 5.5** | VS Code extension + terminal |
| LLM inside the product (parses prompts) | **Claude Haiku 5.5** (`azure_ai/claude-haiku-5-5`) | FHNW LiteLLM gateway |
| Agent steering | `AGENTS.md` + AI-SDLC skills (`skills/ai-sdlc-*`) | repository |
| Code context for the agent | MCP servers Context7 and GitMCP | `.mcp.json`, `.vscode/mcp.json` |

## 1. Coding agent: Claude Code

Claude Code was the team's default and main coding agent. Every commit it
helped write carries `Co-Authored-By: Claude Opus 5.5`.

**Why Claude Code**

- **Agentic, not only completion:** it plans, edits files, runs the tests,
  git and the app in the terminal, and reads the results (loop: plan → act →
  observe), which is what TDD with an agent needs.
- **Follows repository instructions:** it loads `AGENTS.md` (the AI-SDLC
  router) and the phase skills, so the same rules apply in every session.
- **MCP support** for extra context (section 3).
- **Course evidence (SW3):** Claude Code is in the Thoughtworks Radar "Adopt"
  ring and Claude Code with Opus 5.5 led the Artificial Analysis Coding Agent
  Index (66).
- **Trade-offs we accepted:** vendor-bound to Claude models and among the
  most expensive agents per task in that benchmark (about USD 13 per task). Mitigation: small, reviewable
  slices, human review of every pull request, and CI as the quality gate.

**How the agent was steered (AI-SDLC)**

| Phase | Artefact the agent produced | Human decision |
|---|---|---|
| 1 Specify | [UC-001](specs/UC-001-CATALOG-ORDER.md) from our whiteboard (catalog order logic) | use case, scope (catalog only), acceptance |
| 2 Design | [ADR-001](adr/ADR-001-catalog-order-mvp-architecture.md), [data model](DATA-MODEL.md) | architecture, ≥ 5 entities |
| 3 Develop | failing tests first, then code ([commit history](https://github.com/zTK47/AI-Procurement-/commits/main) (commit order; see the timing note in PROMPTS.md): `test:` before `feat:`) | UI views, colours, columns, statuses |
| 4 Validate | CI, Dockerfile, E2E, release pipeline | PR review and merge, release tag |
| 5 Deploy | [ADR-002](adr/ADR-002-deployment-render-neon.md), `cd.yml` | Render/Neon accounts, secrets, go-ahead |

Lifecycle state and evidence are kept in [TASKS.md](TASKS.md). Release and
deployment were only done after explicit approval (rule in `AGENTS.md`).
The key prompts and the commits they produced are listed in [PROMPTS.md](PROMPTS.md).

## 2. LLM inside ProcAI

The LLM does one narrow job: turn a prompt such as *"Bitte bestelle 3
Bürostühle"* into JSON (`quantity`, `productName`, `category`, `confidence`).
Everything that decides money — catalog match, cheapest supplier, budget,
stock, approval level — is deterministic code ([ADR-001](adr/ADR-001-catalog-order-mvp-architecture.md)).

- The answer is validated with pydantic; invalid JSON counts as a failure.
- If the gateway fails, a rule-based parser takes over, so ordering never
  depends on LLM availability.
- The model is configured with `LITELLM_MODEL`, without code changes.

## 3. MCP servers (code context)

| Server | URL | Why | Permissions |
|---|---|---|---|
| `context7` | `https://mcp.context7.com/mcp` | current, version-specific docs (FastAPI, SQLAlchemy, LiteLLM, pytest) instead of the model's training cut-off | read-only, public, no key |
| `ai-procurement-repo` (GitMCP) | `https://gitmcp.io/zTK47/AI-Procurement-` | search this repository's code and docs | read-only, public repo, no key |

Configured for Claude Code (`.mcp.json`, check with `/mcp`) and VS Code
(`.vscode/mcp.json`). The LiteLLM gateway's own `/mcp` endpoint exposes no
tools for our keys and is not used. Servers that need tokens (e.g. GitHub
MCP) belong in user scope only; tokens are never committed. Risk to keep in
mind: content read through MCP (issues, web pages) can contain prompt
injection, so tool calls that write are confirmed by a human.

## 4. Model selection for the product

All gateway models were benchmarked on ProcAI's real task with
[`scripts/benchmark_models.py`](../scripts/benchmark_models.py): 5 prompts
(English, German, colloquial, number words, "10x"), same parser as
production. Full results: [MODEL-EVALUATION.md](MODEL-EVALUATION.md).

| Model | Correct | Seconds | USD per request |
|---|---|---|---|
| `gpt-6-luna` | 5/5 | 1.2 | 0.000044 |
| **`azure_ai/claude-haiku-5-5`** (chosen) | 5/5 | 1.0 | 0.000048 |
| `gpt-5.6-luna` | 5/5 | 1.6 | 0.000071 |
| `azure_ai/gpt-oss-120b` | 5/5 | 0.8 | 0.000093 |
| `azure_ai/mistral-large-3` | 5/5 | 0.9 (22 s in an earlier run) | 0.000154 |
| `gpt-5.4-mini-new` | 5/5 | 1.1 | 0.000243 |
| `ibm/granite4.1:3b` | 5/5 | 4.2 | no price listed |
| embedding / non-chat models | 0/5 | — | not usable for chat |

**Decision: Claude Haiku 5.5.** Every chat model solved the task, so cost and
speed decide. Haiku is among the two cheapest and was the fastest of those
two; `gpt-6-luna` is about 8 % cheaper but slower. Mistral was the slowest
model in an earlier run (22 s per request), which would hurt the user
experience. Latency varies between runs, so the benchmark should be rerun
before changing the model.

## 5. AI cost assessment

| Item | Value |
|---|---|
| Tokens per request (Haiku) | ~257 in, ~44 out |
| Cost per request | **≈ USD 0.00005** |
| 1,000 requests | ≈ USD 0.05 |
| 100,000 requests | ≈ USD 5 |

- The low spend on our LiteLLM key (≈ 5 cents) is expected: it comes from
  the app and the benchmarks, not from a tracking problem.
- The coding agent did not run through this key (Opus 5.5 is not offered by
  the gateway), so the key's spend is only the product's AI cost.
- The keys are "LLM API only": spend reports (`/spend/logs`, `/key/info`
  spend) cannot be read with them. Spend is visible in the LiteLLM web
  dashboard (FHNW login). Per-request cost tracking inside ProcAI is in the
  backlog.
- Why it is cheap: the LLM only extracts a small JSON object; the expensive
  part of procurement (rules, approvals) is plain code.

## 6. Lessons learned

- **Test against the real gateway.** Two bugs passed all unit tests and were
  found only in a live run: Claude Haiku 5.5 rejects `temperature=0`, and
  the LiteLLM SDK treated `azure_ai/…` as a direct Azure call instead of a
  call to our proxy. The rule-based fallback hid both silently — a fallback
  needs logging and a check that the primary path really works.
- **Specs and tests keep the agent on track.** With UC-001 and failing tests
  first, the agent's changes were small and verifiable; screenshots and
  reviews were still needed for UI decisions.
- **Humans own the irreversible steps.** Merges, release tags, deployment and
  secrets stayed with the team; the agent prepared and verified them.
- **Secrets discipline.** `.env` is gitignored, keys live in Render/GitHub
  secrets, and every push was scanned for keys. A key that was pasted into a
  chat should be rotated.
- **Benchmarks are snapshots.** The same model varied from 0.9 s to 22 s, so
  we keep the benchmark as a script and rerun it.

## Open points

- ADR-001 and ADR-002 are *Proposed* until the team accepts them.
- In-app AI cost tracking (tokens and cost per request, by model).
