# Architecture Decision Records

Each file records one decision: the situation that forced it, what was decided,
what it costs, and what was rejected.

## Working rules

1. **ADRs are immutable.** Once a record is `Accepted`, it is not edited to
   reflect a change of mind. Write a new ADR, mark the old one
   `Superseded by ADR-NNNN`, and leave the original reasoning intact. The point
   is a record of how the thinking developed, not a document that always appears
   to have been right.
2. **Not everything is an ADR.** Write one when a decision is expensive to
   reverse, when a reasonable person would question it, or when a plausible
   alternative was rejected. Tool choices that cost an afternoon to change are
   not ADRs.
3. **Always record the rejected alternative.** A record that states only the
   choice is a changelog entry.

Copy [`template.md`](template.md) to start a new record.

## Index

| # | Title | Status |
|---|---|---|
| [0001](0001-rest-over-graphql.md) | REST over GraphQL for the public API | Accepted |
| [0002](0002-defer-http-query-method.md) | Defer the HTTP QUERY method until FastAPI supports it | Accepted |
| [0003](0003-sqlalchemy-and-alembic.md) | SQLAlchemy 2.0 for data access, Alembic from the first commit | Accepted |
| [0004](0004-single-user-with-authentication.md) | One user per deployment, with full authentication | Superseded by ADR 0012 |
| [0005](0005-currency-conversion-strategy.md) | Current rates for balances, historical rates for past aggregates | Accepted |
| [0006](0006-money-representation.md) | Money as NUMERIC, Decimal and JSON string | Accepted |
| [0007](0007-categorisation-rules-with-locked-overrides.md) | Rule-based categorisation with locked manual overrides | Accepted |
| [0008](0008-saving-goals-linked-to-account.md) | Saving goal progress derived from a linked account balance | Accepted |
| [0009](0009-credit-cards-as-negative-balance-accounts.md) | Credit cards as ordinary negative-balance accounts | Accepted |
| [0010](0010-two-level-category-hierarchy.md) | Exactly two category levels, transactions on leaves only | Accepted |
| [0011](0011-migrations-run-before-the-api-starts.md) | Migrations run as a one-shot container before the API starts | Proposed |
| [0012](0012-versioned-user-model-and-administrator-boundary.md) | Single-user v0.1, multi-user v1.0 and restricted administration | Accepted |
| [0013](0013-immutable-transactions-and-maintained-balances.md) | Immutable transactions and maintained account/running balances | Accepted |
