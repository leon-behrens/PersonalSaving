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

## Layout

```
src/personalsaving/    application package
pyproject.toml         project metadata and dependencies
uv.lock                resolved dependency versions (committed)
.python-version        interpreter version used locally
```
