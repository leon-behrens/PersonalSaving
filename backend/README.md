# PersonalSaving — Backend

Python backend for PersonalSaving: FastAPI, SQLAlchemy 2.0, PostgreSQL.

See the [project README](../README.md) for what the product is, and
[`docs/`](../docs) for the PRD, decision records and milestones.

## Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Docker and Docker Compose

uv manages the Python interpreter itself, so Python need not be installed
separately. The version recorded in `.python-version` is fetched automatically
on the first sync.

## Setup

From this directory:

```bash
uv sync
```

This creates `.venv/` and installs every dependency at the exact version
recorded in `uv.lock`.

## Everyday commands

Run everything through `uv run`. There is no virtual environment to activate.

| Command | Purpose |
|---|---|
| `uv sync` | Make `.venv` match `uv.lock` exactly |
| `uv run <cmd>` | Run a command inside the project environment |
| `uv add <pkg>` | Add a runtime dependency |
| `uv add --dev <pkg>` | Add a development-only dependency |
| `uv remove <pkg>` | Remove a dependency |
| `uv lock --upgrade` | Re-resolve dependencies to newer versions |
| `uv tree` | Show the resolved dependency tree |

Quote any argument that contains extras. zsh treats square brackets as a glob
pattern and will refuse the command outright:

```bash
uv add "sqlalchemy[asyncio]" "uvicorn[standard]"
```

## Dependency layout

- `[project.dependencies]` — required to run the application; ships in the
  container image.
- `[dependency-groups]` `dev` — tooling required only during development, never
  installed in production.

`uv.lock` pins every direct and transitive dependency and **is committed to the
repository**. It is what makes an install on another machine, in CI, or in
Docker identical to a local one. It is generated, never hand-edited.

## Running

The whole stack, as a user would run it:

```bash
docker compose up -d          # from the repository root
```

That starts PostgreSQL, applies migrations in a one-shot container, then starts
the API. See [ADR 0011](../docs/adr/0011-migrations-run-before-the-api-starts.md)
for why migrations are a separate service.

For development, run the database in Docker and the API on the host so that
reload works:

```bash
docker compose up -d db
uv run alembic upgrade head
uv run uvicorn personalsaving.app:create_app --factory --reload --port 4455
```

| URL | What |
|---|---|
| <http://127.0.0.1:4455/api/health> | Readiness, including a database round-trip |
| <http://127.0.0.1:4455/docs> | Interactive API documentation |
| <http://127.0.0.1:4455/openapi.json> | The generated specification |

The port must match `EXTERNAL_BASE_URL` in `.env`, which is what the API
advertises to clients.

## Migrations

Locally you apply migrations yourself:

```bash
uv run alembic upgrade head      # apply everything outstanding
uv run alembic current           # what the database thinks it is
uv run alembic history           # the revision chain
uv run alembic downgrade -1      # step back one
```

To create one after changing a model:

```bash
uv run alembic revision --autogenerate -m "describe the change"
```

**Read the generated file before applying it.** Autogenerate reports a column
rename as a drop plus an add, which destroys that column's data if run unseen.

A deployment never needs these commands — the `migrate` service runs
`alembic upgrade head` before the API starts.

## Testing

Tests need a running PostgreSQL server. They do not touch your development
database: the harness creates a uniquely named throwaway database, applies
migrations to it, runs each test inside a transaction that is rolled back, and
drops the database afterwards.

```bash
docker compose up -d db
uv run pytest
```

Coverage is reported on every run and is deliberately not enforced — the number
is there to be looked at, not defended.

The harness refuses to run when `ENVIRONMENT_NAME` is `production`, because it
issues `CREATE DATABASE` and `DROP DATABASE` against whatever server the
environment names.

## Quality checks

```bash
uv run ruff check .              # lint
uv run ruff format .             # format
uv run mypy                      # strict type checking
```

Install the git hooks once per clone — they are not installed automatically:

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```

The hooks run the same checks as CI. CI is the enforcement boundary; the hooks
just tell you sooner.

## The API contract

`openapi.json` is generated from the code and committed. CI regenerates it and
fails if the committed copy has drifted, so a change to the API shows up as a
reviewable diff.

After changing any route or schema:

```bash
uv run python scripts/export_openapi.py
```

The `servers` block is stripped before writing, because it varies per
deployment and would otherwise make the file differ between environments.

## Layout

```
src/personalsaving/    application package
tests/                 test suite and fixtures
alembic/               migration environment and versions
scripts/               developer utilities
Dockerfile             production image, multi-stage
openapi.json           generated API contract (committed)
pyproject.toml         project metadata, dependencies and tool configuration
uv.lock                resolved dependency versions (committed)
.python-version        interpreter version used locally
```
