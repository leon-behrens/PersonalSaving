# ADR 0008: Saving goal progress derived from a linked account balance

- **Status:** Accepted
- **Date:** 2026-10-24
- **Supersedes:** —

## Context

A saving goal needs a source of truth for how much has been saved toward it.
Three mechanisms were available: the balance of a linked account, contributions
recorded manually by the user, or transactions individually tagged to a goal.

The product's central promise is that a periodic CSV upload is the only
maintenance required. Any mechanism demanding ongoing manual bookkeeping works
against that.

## Decision

A goal references exactly one account. Progress is that account's current
balance measured against the target amount. Where the goal and account
currencies differ, conversion follows the present-value path in ADR 0005.

## Consequences

- Progress updates automatically from imported statements with no user effort,
  which is precisely the product promise.
- In practice this means one goal per account. Several goals sharing a single
  savings account cannot be tracked separately.
- The account's entire balance counts toward the goal, even if the user mentally
  earmarks part of it for something else.
- Goals are only as meaningful as the user's account structure. Someone saving
  for three things in one account is not served.

## Alternatives considered

**Manual contributions.** Accurate for shared accounts and allows several goals
per account, but requires ongoing manual entry, contradicting the automation
goal.

**Transactions tagged to a goal.** The most flexible — multiple goals per
account, exact attribution — but the most work to build and the most work for
the user to maintain.

Either may supersede this record if the one-goal-per-account limit proves too
restrictive in practice.
