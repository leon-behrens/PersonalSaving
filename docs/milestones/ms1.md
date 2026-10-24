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

## Out of scope

Deliberately excluded, to be built on top later:

- Any domain model or table beyond Alembic's own version table
- Authentication (Milestone 3)
- Any frontend
- CSV import, categories, goals, exchange rates, dashboard

## Tasks

### 1. Repository and tooling

- [ ] Initialise the project with `uv`; pin the Python version
- [ ] `pyproject.toml` with separate main and dev dependency groups
- [ ] Configure `ruff` for both linting and formatting
- [ ] Configure `mypy` in strict mode
- [ ] `pre-commit` hooks: ruff, ruff-format, mypy
- [ ] `.env.example` listing every variable with a safe default or a placeholder

### 2. Application skeleton

- [ ] FastAPI application factory
- [ ] `pydantic-settings` configuration object: database URL, environment, log
      level, external base URL
- [ ] Structured logging configured at startup, with the `NFR-PRIV-4` rule
      (no financial data in logs) established from the beginning
- [ ] `/api/v1` route prefix in place, so versioning exists before there is
      anything to version
- [ ] `GET /api/v1/health` returning application status and a real database
      round-trip (`SELECT 1`), satisfying `NFR-OPS-5`
- [ ] Run uvicorn with `--proxy-headers`, and keep the external base URL
      configurable, so a reverse proxy can be added later without code changes

### 3. Database and migrations

- [ ] PostgreSQL service in Compose, with a named volume for its data
- [ ] Async SQLAlchemy 2.0 engine and a session dependency
- [ ] `alembic init`, configured for async operation and pointed at the
      declarative metadata for autogenerate
- [ ] Baseline migration, applied against an empty database
- [ ] Verify `alembic upgrade head` and `alembic downgrade base` both succeed
- [ ] Decide and document how migrations run on startup

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
- [ ] One test calling `GET /api/v1/health` through `httpx.AsyncClient` and
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
- [ ] Every environment variable documented in `.env.example`

## Definition of done

Each of these is checkable, on a clean machine, from a fresh clone:

1. `docker compose up` brings the stack up with no manual steps.
2. `GET /api/v1/health` returns `200` and reports the database as reachable.
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
