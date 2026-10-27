# ADR-002 Deployment on Render with Neon PostgreSQL

Status: Proposed

## Context

ProcAI must run publicly for the capstone demo. The free Render web service
sleeps and restarts, so SQLite inside the container loses all requests on
every restart and deploy. Deployments should only ship validated releases.

## Alternatives

- SQLite in the container: no setup, but data is lost on restart/deploy.
- Render PostgreSQL (free): deleted after 30 days.
- Neon PostgreSQL (free, 0.5 GB, no expiry): external, serverless.
- Deploy every merge to `main` (Render auto-deploy) vs. only releases.

## Decision

- Hosting: Render web service built from the repository Dockerfile, region
  Frankfurt, health check `/api/health`. Auto-deploy is off.
- Database: Neon PostgreSQL (Frankfurt) via `DATABASE_URL`; the app maps
  `postgres://`/`postgresql://` to the psycopg 3 driver and uses
  `pool_pre_ping` because Neon closes idle connections.
- CD: only a successful `Release` (tag `v*`, tests + image + E2E) triggers
  `cd.yml`, which calls the Render deploy hook, waits until `/api/health`
  reports the released commit, and runs read-only smoke tests against the
  live URL. The GitHub environment `production` can require a reviewer.
- Secrets (`DATABASE_URL`, `LITELLM_API_KEY`, deploy hook) live only in
  Render and GitHub secrets.

## Consequences

- Data survives restarts and deploys; tables and master data are created on
  first start (`create_all` + seed), no migration tool yet.
- Production only changes through a tagged, tested release.
- The deploy hook deploys the latest commit of `main`; releases are tagged
  from `main`, so the version check fails loudly if they ever diverge.
- Free tier: the first request after idle takes about a minute (cold start).
