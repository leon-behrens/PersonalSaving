# ADR 0013: Immutable transactions and maintained balances

- **Status:** Accepted
- **Date:** 2026-11-26
- **Supersedes:** ADR 0007 for post-creation category changes and rule reapplication

## Context

The account view needs a current balance and a running balance after every
transaction without summing the complete account history on each read. An account
can include manually recorded money alongside bank transactions, so the bank's
reported balance can differ from PersonalSaving's balance.

## Decision

Store `ACCOUNT.balance` and `FINANCIAL_TRANSACTION.balance_after` as exact decimal
values. Both are maintained by the server and are read-only to clients. Store an
optional `bank_reported_balance` separately on each transaction. Never overwrite
the calculated balance with the bank-reported balance or add the two balances.
A difference can be legitimate because manual transactions also affect the account.

Transaction records are immutable after creation, including their category and
note. Corrections create new entries. Reversing entries reference their original
transaction through `reversal_of_id`, have the opposite signed amount in the same
account and currency, and preserve the original record. A reversal is inserted at
most once for an original transaction. A corrected replacement, when needed, is
another new entry. Reversal creation and replacement creation succeed together.

`balance_after` is a server-maintained projection. Recomputing it is permitted
without changing the transaction's recorded facts. Account opening values are
editable under the rules below. Immutability applies to transaction facts and
excludes these explicitly rebuildable projections.

Order transactions by booking date. Preserve bank ordering within the same day
and source statement where available. Allocate a persistent account/day sequence
when records are first inserted to merge statement order with existing imports
and manual entries. Existing same-day entries retain their relative order. New
entries use the next sequence positions in source order. Separate statements do
not imply a shared bank ordering. Use this sequence as the final tie-breaker and
enforce uniqueness per account and booking date. Display newest booking dates and
highest sequences first. A bank-reported balance always retains its source meaning.

The opening balance is the amount at the start of `opening_date`, before entries
booked that day. All stored transactions contribute, including future-dated
entries. The displayed current balance therefore includes future recorded entries.
Reject transactions before the opening date during manual creation and CSV
validation, and recheck at confirmation. The user must explicitly adjust opening
values before accepting those entries. Opening date/balance edits are allowed,
but reject an opening date later than any existing transaction's booking date.

For ordered entries, start from the opening balance and add each signed amount
to produce `balance_after`. The account balance is the final running balance, or
the opening balance when no transactions exist. Serialize balance-affecting writes
per account, and update facts, running balances and account balance in one database
transaction. Historical inserts and opening-value changes recalculate the affected
suffix or full history before commit. Concurrent operations, failures and retries
must preserve these invariants. A rebuild from opening values and transaction facts
must reproduce stored calculated balances.

Import reversion retains original rows and appends one linked reversing entry for
each transaction created by that batch, with a matching booking date so the batch's
net effect is cancelled from its original dates. Reversion status, reversing entries
and recalculated balances commit together. Retrying reversion creates no additional
entries. Duplicate fingerprints remain reserved by retained original rows. Account
deletion cannot cascade-delete transaction history. Detailed transfer handling
and correction API schemas must be specified before implementing those operations.

Rules and manual categories are chosen before transaction creation. Existing
transactions cannot be recategorized or have notes edited. Changes to category
rules apply to new transactions. Category references must be preserved when
categories are retired. This replaces ADR 0007's post-creation override behavior.

## Consequences

Balance reads are cheap, while historical insertion and opening-value edits can
require many projection updates. The immutability policy retains mistakes and
corrections for inspection. Bank and calculated balances can be compared without
assuming they must match. Tests must cover concurrent writes, rollback, reversal
idempotency, backdated inserts, future entries, opening edits and balance rebuilds.
The existing implementation requires migrations and service changes to implement
this design.
