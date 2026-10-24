# ADR 0009: Credit cards as ordinary negative-balance accounts

- **Status:** Accepted
- **Date:** 2026-10-24
- **Supersedes:** —

Resolves PRD open question Q2.

## Context

Most discretionary spending happens on a credit card, so a spending tracker that
excludes cards shows an incomplete picture of exactly the spending the user most
wants to understand.

The question was whether a card needs a model of its own — statement periods,
due dates, minimum payments, interest — or whether it can be an ordinary
account.

There is one accounting trap. A card payment of CHF 800 from the checking
account is an outflow from checking and an inflow to the card. Counted naively,
the month shows CHF 800 of "spending" on top of the purchases that created the
balance — the same money twice.

## Decision

A credit card is an ordinary account whose balance is negative when money is
owed. The `credit_card` account type affects presentation only: the balance is
labelled as owed, and an optional credit limit allows available credit to be
shown.

Card payments from another account are handled by the existing transfer
detection (FR-TRF), which excludes both legs from income and spending.

## Consequences

- One account model. Net worth remains a plain sum of balances across accounts,
  with no special-casing.
- The accounting comes out right: purchases on the card count as spending in
  their categories, and the monthly payment is a transfer and is excluded. This
  depends on transfer detection, which makes FR-TRF load-bearing rather than a
  refinement.
- No statement periods, due dates, minimum payments or interest modelling. PS
  cannot answer "how much is due on the 15th".
- Interest charges and card fees arrive as ordinary transactions and are
  categorised like any other.

## Alternatives considered

**A distinct account type with settlement logic.** Would enable due-date
reminders and statement views. Deferred: it is a payment-reminder feature rather
than a modelling necessity, and it carries a meaningful amount of schema and
logic.

**No credit card support in V1.** Honest scoping, rejected because it leaves the
core use case half-served.
