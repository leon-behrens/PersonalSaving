# Milestone 1: Walking Skeleton

| | |
|---|---|
| **Status** | Ongoing |
| **Goal** | End-to-end plumbing with no features in it |
| **Depends on** | Nothing |
| **Blocks** | Every subsequent milestone |

## Objective

A fresh clone of this repository starts with one command, answers a health
check that genuinely reaches the database, runs a passing test suite, and goes
green in CI — with no domain models, no tables and no business logic.

## Why this first

The instinct is to start with transactions, because that is the interesting
part. Resisting it is the point of this milestone.

Features built before the harness exists get their tests, typing and
containerisation retrofitted afterwards, which is slower and produces worse
versions of all three. Building the harness first means every feature from
Milestone 2 onward lands in a working environment and is tested from its first
line.

It also validates `NFR-OPS-1` — that PS starts with a single command — on day
one, rather than discovering at the end that the application does not
containerise cleanly.

## In scope

- Project tooling and dependency management
- Application skeleton with configuration and logging
- PostgreSQL, async SQLAlchemy engine, Alembic wired up
- Containerisation and Compose
- Test harness with one real test
- Continuous integration
- Developer setup instructions
- Architecture documentation and diagrams

## Out of scope

Deliberately excluded, to be built on top later:

- Any domain model or table beyond Alembic's own version table
- Authentication (Milestone 3)
- Any frontend
- CSV import, categories, goals, exchange rates, dashboard

## Tasks

### 1. Repository and tooling

- [x] Initialise the project with `uv`; pin the Python version
- [x] `pyproject.toml` with separate main and dev dependency groups
- [x] Configure `ruff` for both linting and formatting
- [x] Configure `mypy` in strict mode
- [x] `pre-commit` hooks: ruff, ruff-format, mypy
- [x] `.env.example` listing every variable with a safe default or a placeholder

### 2. Application skeleton

- [x] FastAPI application factory
- [x] `pydantic-settings` configuration object: database URL, environment, log
      level, external base URL
- [x] Structured logging configured at startup, with the `NFR-PRIV-4` rule
      (no financial data in logs) established from the beginning —
      **development format only; the production branch currently raises**
- [x] `/api/v1` route prefix in place, so versioning exists before there is
      anything to version
- [x] `GET /api/health` returning application status and a real database
      round-trip (`SELECT 1`), satisfying `NFR-OPS-5`. Deliberately outside the
      version prefix: a container healthcheck or reverse proxy should not need
      to know the API version, and the endpoint must not move when `/api/v2`
      appears
- [ ] Run uvicorn with `--proxy-headers`, and keep the external base URL
      configurable, so a reverse proxy can be added later without code changes —
      the `servers` block is wired to `EXTERNAL_BASE_URL`; `--proxy-headers`
      lands with the container command in task 4

### 3. Database and migrations

- [x] PostgreSQL service in Compose, with a named volume for its data
- [x] Async SQLAlchemy 2.0 engine and a session dependency
- [x] `alembic init`, configured for async operation and pointed at the
      declarative metadata for autogenerate
- [x] Baseline migration, applied against an empty database
- [x] Verify `alembic upgrade head` and `alembic downgrade base` both succeed
- [x] Decide and document how migrations run on startup

### 4. Containerisation

- [ ] `Dockerfile` for the API, multi-stage, installing via `uv`
- [ ] `.dockerignore`
- [ ] `docker-compose.yml` bringing up API and database together
- [ ] Database healthcheck plus `depends_on: condition: service_healthy`, so
      the API does not race the database on startup

### 5. Test harness

- [ ] `pytest`, `pytest-asyncio` and `httpx` installed and configured
- [ ] `asyncio_mode = auto` so tests need no per-test decorator
- [ ] Test database fixture: separate database, migrations applied, torn down
      afterwards
- [ ] One test calling `GET /api/health` through `httpx.AsyncClient` and
      asserting both the status code and the reported database state
- [ ] Coverage reporting configured but not yet enforced

### 6. Continuous integration

- [ ] GitHub Actions workflow running on pull requests
- [ ] Steps: `ruff check`, `ruff format --check`, `mypy`, `pytest` against a
      PostgreSQL service container
- [ ] Commit the generated `openapi.json`
- [ ] CI step regenerating the specification and failing if it differs from the
      committed copy, so contract changes appear as reviewable diffs from the
      first endpoint onward

### 7. Documentation

- [ ] README section: prerequisites, setup, running, testing
- [x] Every environment variable documented in `.env.example`

### 8. Architecture documentation

- [ ] `docs/architecture.md`, with the diagrams exported to an accompanying PDF
- [ ] **Architecture diagram** — the deployment shape: browser, reverse proxy
      (future), API container, PostgreSQL container, and the single outbound
      call to the exchange rate API
- [ ] **Component diagram** — the backend's internal structure: application
      factory, routers, settings, database layer, and where the import,
      categorisation and currency services will sit
- [ ] **Sequence diagram** — at minimum the CSV import flow (upload → preview →
      deduplicate → confirm → insert), the most involved interaction in the
      product
- [ ] **Data flow diagram** — where financial data is stored and which
      boundaries it crosses. This one doubles as evidence for the privacy
      claims in `SECURITY.md`: it should make visible that nothing but currency
      codes and dates leaves the machine

Keep the diagram **source** in the repository as text — Mermaid in the Markdown,
or PlantUML beside it — and treat the PDF as a rendered artefact. Diagrams drawn
in a GUI tool and committed as images stop being updated, because editing them
is a chore and the diff is unreadable.

Note that `.gitignore` currently excludes `*.pdf`, so a committed export needs
an explicit negation.

## Definition of done

Each of these is checkable, on a clean machine, from a fresh clone:

1. `docker compose up` brings the stack up with no manual steps.
2. `GET /api/health` returns `200` and reports the database as reachable.
3. `alembic upgrade head` followed by `alembic downgrade base` both succeed.
4. `pytest` passes.
5. `ruff check`, `ruff format --check` and `mypy` all report clean.
6. A pull request goes green in CI.
7. `openapi.json` is committed, and CI fails if it goes stale.

## Known gotchas

**Alembic's async configuration is fiddly.** `env.py` needs reworking to drive
an async engine, and the examples in circulation vary in quality. Budget more
time for this than its size suggests.

**Autogenerated migrations must be read before they are applied.** Alembic
reports a column rename as a drop plus an add, which destroys that column's
data if run unseen. Establish the habit now, while the migrations are trivial.

**The API will race the database** without a healthcheck on the Postgres
service. `depends_on` alone waits for the container to start, not for the
database to accept connections.

**mypy in strict mode against SQLAlchemy 2.0** needs the `Mapped[]` annotation
style throughout. Getting this right on an empty project is easy; retrofitting
it later is not.

**Keep `/health` cheap.** It will be polled by Docker, by CI and possibly by a
proxy. A single `SELECT 1`, no counts or joins.

## References

- [ADR 0003](../adr/0003-sqlalchemy-and-alembic.md) — SQLAlchemy and Alembic
  from the first commit
- PRD `NFR-OPS-1`, `NFR-OPS-3`, `NFR-OPS-5` — single-command start,
  environment configuration, health endpoint
- PRD `NFR-QUAL-3` — strict type checking, enforced linting
- PRD `NFR-PRIV-4` — logging restrictions

## Next

**Milestone 2 — Accounts CRUD.** The first vertical slice: model, migration,
schemas, endpoints and tests, through every layer this milestone has set up.
