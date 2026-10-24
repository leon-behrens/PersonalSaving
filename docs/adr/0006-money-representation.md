# ADR 0006: Money as NUMERIC, Decimal and JSON string

- **Status:** Accepted
- **Date:** 2026-10-24
- **Supersedes:** —

## Context

Binary floating point cannot represent decimal fractions such as `0.10`
exactly. In a system that sums thousands of transactions, the resulting errors
accumulate and balances drift away from what the bank reports.

The transport layer matters as much as storage. JSON numbers are IEEE 754
doubles, so a value stored exactly as `NUMERIC` and handled exactly as `Decimal`
becomes a float the instant `JSON.parse` sees it in the browser. Precision taken
seriously everywhere else is discarded at the last step.

## Decision

- **PostgreSQL:** `NUMERIC` for all monetary amounts.
- **Python:** `Decimal` throughout; `float` is prohibited for monetary values.
- **JSON:** amounts are serialised as strings, for example
  `{"amount": "-42.50", "currency": "CHF"}`.
- Exchange rates are stored at higher precision than amounts.
- Rounding happens only at the presentation layer.

## Consequences

- Exact arithmetic from database to screen.
- The frontend must parse amount strings with a decimal library rather than
  treating them as numbers, and must not perform arithmetic on them natively.
- Payloads are marginally more verbose, and the convention has to be documented
  so it is not "corrected" by someone later.

## Alternatives considered

**Integer minor units.** Storing 4250 rather than 42.50 is exact and widely
used, but is awkward for currencies with a different exponent and clumsy for
exchange rate arithmetic, which is not expressible in minor units at all.

**JSON numbers.** Rejected. It discards, at the boundary, the precision
guaranteed everywhere else in the stack, and the resulting errors are small
enough to go unnoticed until a balance disagrees with the bank.
