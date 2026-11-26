# ADR 0007: Rule-based categorisation with locked manual overrides

- **Status:** Superseded for post-creation overrides and rule reapplication by [ADR 0013](0013-immutable-transactions-and-maintained-balances.md)
- **Date:** 2026-10-24
- **Supersedes:** —

## Context

Categorising every transaction by hand does not survive contact with a few
hundred transactions, and the dashboard is worthless without categories. Purely
automatic rules, meanwhile, always misclassify something.

The interaction between the two is where the real design problem sits. Rules get
re-run — when the user edits a rule, adds one, or re-imports. If a re-run
overwrites categories the user set by hand, their corrections vanish silently
and the feature becomes untrustworthy.

## Decision

User-defined rules match a pattern against a transaction's description or
counterparty, are evaluated in explicit priority order, and the first match
wins. Rules are applied automatically during import; unmatched transactions go
to a built-in **Uncategorised** category.

Any manual category change sets a lock flag on that transaction. Re-running
rules skips locked transactions entirely.

## Consequences

- Bulk accuracy from rules, with a human escape hatch for the cases they get
  wrong.
- User corrections are durable, which is what makes the automation trustworthy.
- One extra boolean on the transaction table and one branch in the rule runner.
- A user who fixes a transaction by hand and later writes a rule that would
  classify it differently will see the rule appear not to work. The UI must
  explain the lock and offer a way to clear it.
- The count of uncategorised transactions becomes a meaningful health signal
  worth surfacing on the dashboard.

## Alternatives considered

**Manual only.** Trivial to build, unusable beyond a few hundred transactions.

**Rules only, no override.** Simpler data model, but leaves no way to fix a
misclassification — and there is always one.

**Rules that always overwrite on re-run.** Rejected outright. It destroys user
work on every rule edit, which is the worst available failure mode for a feature
whose entire value rests on the user trusting its output.
