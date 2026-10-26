# ADR 0011: Migrations run as a one-shot container before the API starts

- **Status:** Accepted
- **Date:** 2026-10-26
- **Supersedes:** —

## Context

[ADR 0003](0003-sqlalchemy-and-alembic.md) committed this project to Alembic
from the first commit, so the schema of any database is reached by applying
migrations in order. Something therefore has to run `alembic upgrade head` when
a new version is deployed. The question is what runs it, and when.

The constraints are specific to this product:

- `NFR-OPS-1` requires that one command starts the stack.
- `NFR-OPS-2` requires that upgrading never makes the user recreate their
  database because it holds their financial history.
- The operator is an individual self-hosting the application
  ([ADR 0004](0004-single-user-with-authentication.md)), not a system
  administrator. A documented manual procedure is not something they can be
  expected to follow correctly before every upgrade.

Two technical facts shape the options. **Alembic takes no lock by default**, so
two processes running `upgrade head` against the same database concurrently can
conflict. And the API must not serve requests against a schema it does not
expect, so a migration failure has to prevent startup rather than being ignored.

## Decision

Migrations run as a **dedicated one-shot container** in Compose. It executes
`alembic upgrade head` and exits. The API service declares:

```yaml
depends_on:
  migrate:
    condition: service_completed_successfully
```

so it starts only after migrations have completed successfully.

Both services are built from the same image; only the command differs.

Local development is a separate concern: developers run
`uv run alembic upgrade head` by hand against their own database.

## Consequences

- `docker compose up` remains the single command the user runs, satisfying
  `NFR-OPS-1`.
- Migrations run exactly once no matter how many API containers exist, so the
  concurrency problem never arises and no advisory lock is needed.
- A failed migration is a container that exited non-zero, visible in
  `docker compose ps` with its own logs, rather than a stack trace buried in
  application startup output.
- The API image's responsibility stays "serve requests".
- The API cannot start against a schema it was not built for.
- The compose file gains a service, and the API's startup is gated on another
  container completing.
- Startup is slower whenever there is a migration to apply.
- A failed migration leaves the stack half up: the database runs, the API never
  starts. The operator has to read the migration container's logs to find out
  why. This needs to be documented where an operator will look.
- Recovery from a *failed* migration is automatic — PostgreSQL's transactional
  DDL rolls the migration back and the database stays at the previous revision.
  Recovery from a migration that succeeded and was wrong is **restore from
  backup**, not `alembic downgrade`: reversing a dropped column recreates it
  empty. The backup is the safety net; the downgrade is a development tool.

## Alternatives considered

**Running migrations inside the application's lifespan.** Fewer moving parts and
no extra service. Rejected on three counts: it gives the API image a second job,
it turns a schema failure into a service that will not start with the reason
hidden inside application logs, and it silently assumes a single instance. That
last assumption is the dangerous one — it holds today and would stop holding
without anyone noticing, at which point concurrent upgrades race against a
database that has no lock protecting it.

**An entrypoint script that migrates and then execs the server.** Common and
simple, but it carries the same race, conflates the same two jobs, and hides the
behaviour inside the image instead of declaring it in the compose file where an
operator can see it.

**Manual migration by the operator.** Maximum control, and a natural point at
which to take a backup first. Rejected because it turns upgrading from a command
into a procedure, which does not match who this software is for.
