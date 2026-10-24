# ADR 0010: Exactly two category levels, transactions on leaves only

- **Status:** Accepted
- **Date:** 2026-10-24
- **Supersedes:** —

Resolves PRD open question Q3.

## Context

Category depth has to be fixed before the schema is written, because it reaches
into every aggregate query in the application.

A flat list is too coarse to present. Thirty peer categories on a dashboard
cannot be summarised, and people naturally think in groups — Food divides into
Groceries, Restaurants and Coffee.

An arbitrary-depth tree is the opposite failure. Aggregating over one requires
recursive CTEs or a closure table, and that cost is paid in every dashboard
query for the lifetime of the project, for a depth that personal finance does
not need.

## Decision

Exactly two levels: a **group** containing **categories**.

Transactions attach only to leaf categories. Assigning a transaction directly to
a group is forbidden at the schema level, not merely discouraged.

The dashboard shows groups by default and drills down to the categories within
them.

## Consequences

- The drill-down users expect, without recursive queries. Every aggregate stays
  a plain `GROUP BY` on either the parent or the category.
- Totals are unambiguous. Because no transaction can sit at both levels, a
  group's total is exactly the sum of its categories, with no double counting
  and no "other" bucket.
- A user who wants three levels cannot have them.
- The leaf-only rule must be enforced in both schema and API, and reparenting a
  category between groups needs care so historical aggregates stay coherent.

## Alternatives considered

**Flat list.** Simplest possible queries, rejected as too coarse to present
usefully.

**Arbitrary depth.** Maximum flexibility, rejected because it imposes permanent
query complexity for a capability this domain does not require.
