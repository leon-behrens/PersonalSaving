# PersonalSaving

PersonalSaving (PS) is a web application to inspect, transform and track your spending, bank accounts and saving goals. Bank records are imported from CSV exports, and a local dashboard shows your accounts, spending trends and progress toward your saving goals.

**Status: Planning** Design phase

## Goal

Give people a clear overview of their banking status, spending and saving goals, running entirely on their own machine. Once the application itself works, the next aim is to make it simple to self-deploy.

## Privacy

PS is built to run locally. Your bank statements, balances and transaction history stay on your own computer. There is no hosted service, no account to create, and no third party ever receives your financial data.

## Target Audience

Individuals and households managing day-to-day money across a few bank accounts, who want a single overview of where their money goes without handing their bank data to a commercial budgeting service. No accounting background required.

## Core Features

### Getting data in

- **CSV import:** Upload a CSV export from your bank to load many transactions at once. V1 supports CSV only.
- **Manual entry:** Add single transactions, accounts or balances by hand, for cash spending or anything an export does not cover.

### Dashboard

Generated automatically from your data:

- Balance per bank account
- Spending, in total and per category
- Income, in total and per category
- Progress toward each saving goal

### Saving goals

- Define goals manually with a target amount and date, and track progress against them.

## Tech Stack

### Frontend

- TypeScript, React, Tailwind CSS
- Typed API client generated from the OpenAPI specification

### Backend

- Python, FastAPI (monolith)
- SQLAlchemy 2.0 (async) as ORM, Alembic for schema migrations
- Pydantic for validation, pydantic-settings for configuration
- Authentication: OAuth2 password flow with JWT access tokens

### Database

- PostgreSQL

### API

- REST, with OpenAPI as the public contract
- Standard verbs: `GET`, `POST`, `PATCH`, `DELETE`
- Transaction search runs over `POST /transactions/search` with the filter in the
  request body. Planned migration to the HTTP `QUERY` method (RFC 10008) once
  FastAPI supports it natively; the request and response shapes are designed so
  that only the verb changes.

### Tooling

- `uv` for dependency and environment management
- `ruff` for linting and formatting
- `mypy` in strict mode for type checking
- `pytest` with `httpx` for unit and API tests
- `pre-commit` hooks

### Deployment

- Docker Compose (application and PostgreSQL)
- Hosting: localhost

## Licence

MIT. See [LICENSE](LICENSE).
