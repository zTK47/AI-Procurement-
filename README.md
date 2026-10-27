# AI-SDLC Project Template

[![AI-SDLC](https://img.shields.io/badge/AI--SDLC-v1.0.0-blue)](https://ai-sdlc.aisl.science)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22833065.svg)](https://doi.org/10.5281/zenodo.22833065)
[![arXiv](https://img.shields.io/badge/arXiv-2609.24348-b31b1b.svg)](https://doi.org/10.48550/arXiv.2609.24348)

Starter repository for student and teaching projects that use the AI-Assisted
Software Development Life Cycle (AI-SDLC).

The method is documented canonically in [AISL Docs](https://docs.aisl.science/learning-and-resources/ai-sdlc). This repository contains only the executable, repository-local
workflow artefacts. It does not contain a complete copy of the method or
application-specific code.

## Create a project

1. Select **Use this template** on GitHub and create a new repository.
2. Open the new repository in GitHub Codespaces and run the agent setup below.
3. Complete `docs/PROJECT.md` with the project context, architecture and commands.
4. Start the lifecycle with `AGENTS.md` and record progress in `docs/TASKS.md`.
5. Use `docs/specs/UC-TEMPLATE.md` for the first use-case specification.

GitHub Copilot instructions are provided in `.github/copilot-instructions.md`.
The included GitHub Actions workflows check the required AI-SDLC structure and
provide a technology-neutral source release baseline. Add project-specific
build, test and artifact-publishing steps during VALIDATE.
`.github/workflows/cd.yml` is included as an inactive template and must be
configured during DEPLOY, after the deployment platform, required secrets and
post-deploy checks have been decided.

## LiteLLM integration

The repository connects to the shared OpenAI-compatible LiteLLM gateway instead
of storing provider credentials or running a model locally. Copy
`.env.example` to `.env`, replace the gateway key, and install the Python
dependencies:

```bash
cp .env.example .env
bash scripts/setup-python.sh
```

The configured default model is `azure_ai/claude-haiku-5-5`. Other models can
be selected by changing `LITELLM_MODEL` in `.env`, provided the gateway account
has access to that model. The client lives in
`src/app/infrastructure/llm_client.py` and sends requests as
`openai/<model>` so the gateway does the provider routing.

## ProcAI – catalog order MVP (UC-001)

ProcAI has two views (switch in the header, no login in the MVP):

- **Requester** (`/#/request`): write a prompt, see how it was understood,
  sourced and checked, and track your requests.
- **Procurement** (`/#/admin`): KPIs, action queue (approve, reject with
  reason, send purchase order), all requests with date and status filter
  (Requested, Approved, Ordered, Rejected) and purchase orders. Refreshes
  every 5 seconds.

A requester types what they need ("I need 5 new Lenovo Laptop"). The LLM
extracts quantity, product and category; deterministic rules then pick the
cheapest matching catalog item, check budget and stock, route the request for
approval and generate the purchase order for the supplier. If the gateway is
unreachable, a rule-based parser takes over. See
[UC-001](docs/specs/UC-001-CATALOG-ORDER.md) and
[ADR-001](docs/adr/ADR-001-catalog-order-mvp-architecture.md).

```bash
.venv/bin/uvicorn app.main:create_app --factory --reload --app-dir src
# open http://localhost:8000  (API docs: http://localhost:8000/docs)
.venv/bin/python -m pytest          # unit + integration tests
```

Run with Docker (no local Python needed):

```bash
docker build -t procai .
docker run --rm -p 8000:8000 --env-file .env procai   # or -e PARSER=rules without a key
```

Released images: `ghcr.io/<owner>/procai:<version>` (see Releases).

Workflow: `CREATED → PARSED → RESOLVED → VALIDATED → PENDING_APPROVAL →
APPROVED → ORDER_SENT` (or `REJECTED`). Orders ≤ 1,000 CHF in stock are
auto-approved; above that a MANAGER (≤ 25,000 CHF) or DIRECTOR approves.

## MCP servers

Shared MCP configuration is versioned for VS Code (`.vscode/mcp.json`) and
Claude Code (`.mcp.json`). Neither file contains credentials.

| Server | URL | Why | Permissions |
|---|---|---|---|
| `context7` | `https://mcp.context7.com/mcp` | Current, version-specific docs for FastAPI, LiteLLM, SQLAlchemy and pytest instead of stale model knowledge | Read-only, public docs, no key |
| `ai-procurement-repo` (GitMCP) | `https://gitmcp.io/zTK47/AI-Procurement-` | Lets the agent search this repository's code and docs as context | Read-only, public repo, no key |

VS Code: open the repository and start the servers from `.vscode/mcp.json`
(or `MCP: List Servers`). Claude Code: the servers are offered on first start
in the repository; check them with `/mcp`.

The LiteLLM gateway also exposes `/mcp`, but no tools are published for our
keys, so it is not configured. Add servers that need tokens (for example the
GitHub MCP server) only in user scope and never commit tokens.

## Agent setup

Codespaces creates a Python development container with Python, Pylance,
debugging and GitHub Copilot extensions. It also prepares `.agents/skills` and
the Python environment automatically. The default terminal locale is English;
the VS Code UI uses its own user display-language setting.

Run `bash scripts/setup-skills.sh` from the repository root when another agent
is used. Run `bash scripts/setup-python.sh` again when the Python environment
needs to be recreated or refreshed.
Choose `copilot`, `codex`, `claude`, `cline`, `opencode`, `cursor`, `kiro`,
`junie`, `devin` or `all`. The script links to the canonical `skills/` directory and
falls back to copying if links are unavailable. Existing destinations are kept;
copies must be refreshed manually after skill changes. Verify discovery in your
agent; setup does not install or configure the agent itself.

For non-interactive setup, pass the same selection, for example `bash scripts/setup-skills.sh copilot`. The `claude` and `all` selections also create a missing `CLAUDE.md` containing `@AGENTS.md`; an existing file is preserved. Shared instructions and skills are not modified.

## Repository artefacts

- `AGENTS.md` — lifecycle router and guardrails
- `docs/PROJECT.md` — project context and commands
- `docs/TASKS.md` — current lifecycle state
- `docs/specs/` — executable use-case specifications
- `skills/ai-sdlc-*` — phase-specific execution guidance
- `.devcontainer/` — Codespaces and VS Code baseline
- `environments/python/` — Python environment profile, including the source
  VS Code debug configuration
- `scripts/setup-python.sh` — Python environment and dependency setup
- `.github/` — Copilot instructions, CI, release and CD workflow templates
