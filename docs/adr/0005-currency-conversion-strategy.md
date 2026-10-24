# ADR 0005: Current rates for balances, historical rates for past aggregates

- **Status:** Accepted
- **Date:** 2026-10-24
- **Supersedes:** —

## Context

Accounts may be held in different currencies, and the dashboard must present
totals in one display currency.

The obvious approach — convert everything at today's rate — has a defect that is
easy to miss and hard to live with. Applying today's rate to a transaction from
2024 means that last year's grocery total changes every morning as the rate
moves. Month-over-month comparisons become meaningless, because the historical
figures are not stable.

The two cases are genuinely different. An account balance describes money held
*now*, so today's rate is the correct one. A transaction that happened in March
describes value exchanged *then*.

PS also claims that financial data never leaves the machine, so any outbound
call needs to be justified and bounded, and the application must remain usable
with no network at all.

## Decision

The original amount and currency are the source of truth and are never modified.
All converted figures are derived at read time.

- **Balances and goal progress** convert at the most recent available rate.
- **Historical aggregates** — spending per category per month, income per month —
  convert at the rate on each transaction's booking date.

Daily rates come from [Frankfurter](https://frankfurter.dev/) (ECB-derived,
free, no API key, historical rates available) and are cached in a local table.
Where no rate exists for a date — weekends, holidays, feed gaps — the most
recent prior rate is used and the figure is marked approximate.

The application remains fully functional offline. Where a rate is neither cached
nor fetchable, the dashboard shows per-currency subtotals without conversion and
says conversion is unavailable. Conversion failure never blocks import,
categorisation or browsing. Rate fetching can be disabled entirely in
configuration, after which PS makes no outbound requests at all.

## Consequences

- Historical charts are stable; a past month's figure never changes.
- Present-value figures are accurate rather than frozen at import time.
- The privacy claim stays clean and specific: the only outbound call carries
  currency codes and dates, never amounts, balances or account identifiers, and
  it can be switched off.
- One extra table and a scheduled fetch to build and operate.
- Two conversion paths to implement and test rather than one.
- Figures near weekends and holidays carry an "approximate" marker that must be
  surfaced in the UI without being alarming.

## Alternatives considered

**Current rates for everything.** Simpler by one code path, rejected because it
makes historical reporting unstable — the primary thing the dashboard exists to
show.

**CHF only.** Simplest, rejected because it does not match the accounts the user
actually holds, and retrofitting currency touches every table and every
aggregate.

**No conversion; per-currency subtotals only.** Rejected as the default, since
it fails to answer "how much did I spend". Retained as the offline fallback,
where it is the honest answer.
