# Product Requirements Document: PersonalSaving (PS)

| | |
|---|---|
| **Status** | Implementation |
| **Version** | 0.1 (draft) |
| **Last updated** | 2026-10-25 |
| **Owner** | Leon Behrens |

---

## 1. Product Summary

PersonalSaving (PS) is a locally hosted web application that helps an individual
understand and steer their personal finances across multiple bank accounts. Bank
statements are imported from CSV exports, transactions are categorised
automatically, and a dashboard shows account balances, income and spending
trends, and progress toward saving goals.

PS runs entirely on the user's own machine. No financial data leaves the device.

## 2. Problem

People hold money across several accounts: a salary account, a savings account,
maybe a second bank and a credit card. Each bank shows only its own slice, in its
own interface, with its own idea of what a category is. Building a picture of
total spending, or of whether a saving goal is actually on track, means exporting
spreadsheets and reconciling them by hand.

Commercial budgeting services solve this, but at a price most people do not
examine closely: they require handing over bank credentials or statement data to
a third party, and they monetise that data. For a user who considers their
transaction history private, there is no good option between a manual
spreadsheet and a cloud service.

PS targets exactly that gap: the consolidated view of a budgeting service,
running on hardware the user controls.

## 3. Goals

- **G1:** Give the user one view of balances, income, spending and saving
  progress across all their accounts.
- **G2:** Keep all financial data on the user's own machine.
- **G3:** Reduce the manual effort of maintaining that view to a periodic CSV
  upload, by categorising transactions automatically.
- **G4:** Be deployable by a technically confident individual with a single
  command, once the application is complete.

## 4. Non-Goals

Explicitly out of scope for V1:

- **NG1:** No automatic bank connection (screen scraping, Open Banking, PSD2
  aggregators). Import is file-based.
- **NG2:** No budgeting or envelope allocation. PS reports what happened; it
  does not enforce a plan.
- **NG3:** No investment, securities or portfolio tracking.
- **NG4:** No tax reporting or export to tax software.
- **NG5:** No mobile application. The web UI should not be usable on a phone
  browser.
- **NG6:** No hosted or multi-tenant offering.

## 5. Target Audience

Individuals and households managing day-to-day money across a few bank accounts,
who want a consolidated overview without handing their bank data to a commercial
service. They are comfortable downloading a CSV from e-banking and running a
`docker compose up`, but are not necessarily developers, and no accounting
knowledge is assumed.

Primary deployment assumption: **one person per deployment.**

## 6. Core Concepts

| Concept | Description |
|---|---|
| **Account** | A bank account, cash wallet or credit card. Has a name, type, currency and balance. |
| **Transaction** | A single movement of money on one account. Signed amount: negative is an outflow, positive an inflow. |
| **Category** | A label for the purpose of a transaction (Groceries, Rent, Salary). Has a kind: income, expense or transfer. |
| **Category rule** | A user-defined pattern matched against a transaction's description to assign a category automatically. |
| **Saving goal** | A named target amount, with a date, linked to one account. Progress is derived from that account's balance. |
| **Import batch** | One CSV upload, retained so an import can be reviewed or reverted. |
| **Bank profile** | A reusable description of one bank's CSV layout: delimiter, encoding, date format, column mapping. |
| **Exchange rate** | A cached daily rate for one currency pair, used for conversion into the display currency. |

## 7. Functional Requirements

### 7.1 Authentication

The deployment serves a single user. Authentication exists so that an
accidentally exposed port does not expose the user's finances.

- **FR-AUTH-1:** The system supports exactly one user account per deployment.
- **FR-AUTH-2:** The user account is created on first run from configuration
  (environment variables) or via a CLI command. There is no public registration
  endpoint.
- **FR-AUTH-3:** Passwords are stored using a memory-hard hash (Argon2id).
  Plaintext and reversible storage are prohibited.
- **FR-AUTH-4:** Login follows the OAuth2 password flow and returns a
  short-lived JWT access token plus a longer-lived refresh token.
- **FR-AUTH-5:** All endpoints except login, token refresh and health require a
  valid access token.
- **FR-AUTH-6:** Failed login attempts are rate limited by exponential backoff,
  not by account lockout. Failures are counted globally rather than per client
  address, since the deployment has exactly one user and per-address counting is
  trivially bypassed by rotating addresses. The delay grows with consecutive
  failures up to a cap and resets on success. Lockout is explicitly rejected: it
  would let an attacker deny the legitimate user access to their own finances.
- **FR-AUTH-7:** The user can change their password from the UI.

### 7.2 Accounts

- **FR-ACC-1:** The user can create, edit, archive and delete accounts.
- **FR-ACC-2:** An account has: name, type (checking, savings, cash, credit
  card), currency, optional IBAN, optional opening balance and opening date.
- **FR-ACC-3:** An account's current balance is the opening balance plus the sum
  of its transactions. It is derived, never stored as an independently editable
  field.
- **FR-ACC-4:** Archiving an account hides it from the dashboard while retaining
  its transactions. Deleting an account requires confirmation and removes its
  transactions.
- **FR-ACC-5:** An account's currency cannot be changed once it has
  transactions.

### 7.3 Transactions

- **FR-TXN-1:** A transaction has: account, booking date, optional value date,
  signed amount, currency, description, optional counterparty, optional category,
  optional free-text note.
- **FR-TXN-2:** A transaction's currency is inherited from its account and
  cannot differ from it.
- **FR-TXN-3:** The user can list transactions with filtering by account, date
  range, category, amount range and free-text search on the description, with
  pagination and sorting.
- **FR-TXN-4:** The user can edit the category and note of any transaction.
  Amount, date and description of an imported transaction are read-only; manually
  entered transactions are fully editable.
- **FR-TXN-5:** The user can delete a manually entered transaction. Imported
  transactions are removed only by reverting their import batch.
- **FR-TXN-6:** Amounts are stored as exact decimals. Binary floating point is
  prohibited anywhere in the storage, transport or aggregation of monetary
  values.

### 7.4 CSV Import

- **FR-IMP-1:** V1 supports CSV import only. No PDF, XML, CAMT.053, MT940 or
  OFX parsing.
- **FR-IMP-2:** The user uploads a CSV and selects the target account and a bank
  profile.
- **FR-IMP-3:** A bank profile describes: delimiter, text encoding, number of
  header rows, date format, decimal and thousands separators, and the mapping
  from CSV columns to transaction fields. It also records whether amounts appear
  as one signed column or as separate debit and credit columns.
- **FR-IMP-4:** Bank profiles are stored and reusable. The system ships with
  profiles for common Swiss bank exports and the user can define their own.
- **FR-IMP-5:** Import is a two-step operation. The system first returns a
  **preview** listing the parsed rows, the rows it would skip as duplicates, and
  any rows that failed to parse. Nothing is written until the user confirms.
- **FR-IMP-6:** Rows that fail to parse do not abort the import. They are
  reported individually with their line number and the reason.
- **FR-IMP-7:** Duplicate detection: each transaction receives a fingerprint
  derived from its account, booking date, amount and normalised description
  (lowercased, whitespace collapsed, punctuation stripped). Where a single
  statement legitimately contains several identical movements on the same day, an
  occurrence index distinguishes them. A transaction whose fingerprint already
  exists is skipped.
- **FR-IMP-8:** The import result reports the number of rows inserted, skipped
  as duplicates, and failed.
- **FR-IMP-9:** An import batch can be reverted, removing exactly the
  transactions it created.
- **FR-IMP-10:** Uploads are bounded by a maximum file size, a maximum row count
  and a parse timeout, all configurable. The limits are enforced before the file
  is read into memory, and exceeding one returns an error naming the limit and
  its value.

> **Rationale for FR-IMP-7.** Users re-download statements with overlapping date
> ranges as a matter of course. Without deduplication the second import silently
> doubles the affected period, and the error is very hard to notice on a
> dashboard.

### 7.5 Manual Entry

- **FR-MAN-1:** The user can create a single transaction by hand, supplying
  account, date, amount, description and optionally a category.
- **FR-MAN-2:** Manual transactions are flagged as such and are excluded from
  duplicate detection against imported rows.
- **FR-MAN-3:** Manual entry covers cash spending and anything absent from a
  bank export. It is not intended as the primary data path.

### 7.6 Categorisation

- **FR-CAT-1:** Categories form exactly two levels: a group containing
  categories (ADR 0010). Each category has a kind: income, expense or transfer.
  The user can create, rename, reparent and delete groups and categories.
- **FR-CAT-2:** A category rule matches a pattern (substring or regular
  expression) against a transaction's description or counterparty and assigns a
  category.
- **FR-CAT-3:** Rules have an explicit priority order. The first matching rule
  wins.
- **FR-CAT-4:** Rules are applied automatically during import. Transactions
  matching no rule are assigned to the built-in **Uncategorised** category.
- **FR-CAT-5:** The user can override the category of any transaction manually.
  A manual override locks that transaction against further automatic
  categorisation.
- **FR-CAT-6:** The user can re-run all rules over existing transactions. This
  affects only transactions that have not been manually overridden.
- **FR-CAT-7:** When creating a rule, the UI previews how many existing
  transactions it would match.
- **FR-CAT-8:** The dashboard surfaces the count of uncategorised transactions
  and links directly to them.
- **FR-CAT-9:** Transactions attach only to leaf categories. Assigning a
  transaction directly to a group is rejected at the schema and API level, so
  that a group total is always exactly the sum of its categories.

### 7.7 Transfers Between Own Accounts

- **FR-TRF-1:** A movement between two of the user's own accounts must not be
  counted as income or expense. Both legs are excluded from all income and
  spending aggregates.
- **FR-TRF-2:** The system proposes transfer pairs by matching transactions in
  different accounts with opposite amounts within a short date window.
- **FR-TRF-3:** The user confirms or rejects each proposed pair. The user can
  also link two transactions as a transfer manually.
- **FR-TRF-4:** A linked transfer pair remains visible in each account's
  transaction list and continues to affect both account balances.

> **Rationale.** Moving CHF 500 from checking to savings produces an outflow in
> one account and an inflow in the other. Counted naively, this inflates both
> monthly spending and monthly income, and the distortion grows with every
> transfer the user makes.

### 7.8 Saving Goals

- **FR-GOAL-1:** A saving goal has a name, a target amount with currency, an
  optional target date, and a link to exactly one account.
- **FR-GOAL-2:** Progress is the linked account's current balance measured
  against the target amount.
- **FR-GOAL-3:** Where the goal currency differs from the account currency, the
  balance is converted for comparison per section 7.9.
- **FR-GOAL-4:** A goal displays: current amount, target amount, percentage
  complete, and remaining amount. Progress above 100% is shown as reached, with
  the true figure still displayed.
- **FR-GOAL-5:** Where a target date is set, the goal displays the monthly
  contribution required to reach the target by that date.
- **FR-GOAL-6:** Goals can be created, edited, marked complete and deleted.

### 7.9 Currency and Exchange Rates

- **FR-FX-1:** The user configures one **display currency**, defaulting to CHF.
- **FR-FX-2:** Every account and transaction carries an explicit currency code
  (ISO 4217).
- **FR-FX-3:** Original amounts are the source of truth and are never modified
  by conversion. Converted figures are derived at read time.
- **FR-FX-4:** Daily rates are fetched from a public exchange rate API
  ([Frankfurter](https://frankfurter.dev/), ECB-derived, no API key) and cached
  locally in the database.
- **FR-FX-5:** **Account balances and goal progress** are converted using the
  most recent available rate, since they describe the present value of money
  currently held.
- **FR-FX-6:** **Historical aggregates** (spending per category per month,
  income per month) are converted using the rate on each transaction's booking
  date. Figures for a past month must not change from one day to the next.
- **FR-FX-7:** Where no rate exists for a given date — weekends, holidays, gaps
  in the feed — the most recent prior rate is used and the figure is marked as
  approximate.
- **FR-FX-8:** The application remains fully functional without network access.
  Where a required rate is not cached and cannot be fetched, the dashboard
  displays per-currency subtotals without conversion and states that conversion
  is unavailable. Conversion failure never blocks import, categorisation or
  browsing.
- **FR-FX-9:** Rate fetching can be disabled entirely in configuration. With it
  disabled, the application makes no outbound network requests whatsoever.
- **FR-FX-10:** Exchange rates are stored with sufficient precision to avoid
  rounding drift, and conversion results are rounded only for display.
- **FR-FX-11:** Rate synchronisation records the date ranges already retrieved
  per currency pair, rather than the individual dates held, and rate lookup
  resolves to the most recent rate on or before the requested date. Reference
  rates are not published on weekends and holidays, so logic that fetches "any
  date without a rate" would request those dates indefinitely. A missing range
  is retrieved as one time-series request per currency pair, never one request
  per date.
- **FR-FX-12:** The exchange rate client honours HTTP 429 and `Retry-After`,
  retries with exponential backoff up to a fixed cap, and applies a hard request
  timeout. On exhaustion it falls back to FR-FX-8. Rate retrieval never blocks an
  import, a categorisation run or a page load.

> **Rationale for FR-FX-6.** Converting a 2024 transaction at today's rate means
> last year's grocery spending changes every morning. Storing rate-by-date costs
> one extra table and makes historical charts stable.

### 7.10 Dashboard

- **FR-DASH-1:** The dashboard presents, for a user-selected period:
  - total balance across all active accounts, in the display currency
  - balance per account
  - total income and total expense for the period
  - spending per category, with drill-down to the underlying transactions
  - income per category
  - income versus expense over time
  - progress for every active saving goal
- **FR-DASH-2:** The period selector offers: current month, last 3 / 6 / 12
  months, year to date, and a custom range.
- **FR-DASH-3:** Every aggregate figure is drillable to the transactions that
  compose it.
- **FR-DASH-4:** Transfers (7.7) are excluded from all income and expense
  figures.
- **FR-DASH-5:** The dashboard indicates when data is incomplete: uncategorised
  transactions present, unconverted currencies, or no import within the period.

## 8. Non-Functional Requirements

### 8.1 Privacy

- **NFR-PRIV-1:** All financial data is stored exclusively in the local
  PostgreSQL instance. There is no hosted component and no account registration.
- **NFR-PRIV-2:** The application contains no telemetry, analytics or crash
  reporting.
- **NFR-PRIV-3:** The exchange rate API is the only outbound network call. It
  transmits currency codes and dates only — never amounts, balances, account
  identifiers or any other financial data — and can be disabled (FR-FX-9).
- **NFR-PRIV-4:** Logs must not contain transaction descriptions, amounts,
  account numbers or authentication tokens.

### 8.2 Correctness

- **NFR-CORR-1:** Monetary amounts use exact decimal arithmetic end to end:
  `NUMERIC` in PostgreSQL, `Decimal` in Python, string-encoded in JSON. Binary
  floats are prohibited for money.
- **NFR-CORR-2:** Aggregation is performed in the database where practical, and
  rounding is applied only at the presentation layer.
- **NFR-CORR-3:** Dates are stored as calendar dates without timezone. A
  transaction booked on the 31st belongs to that month regardless of the
  viewer's locale.

### 8.3 Performance

- **NFR-PERF-1:** The dashboard renders in under one second for a database of
  50,000 transactions across 10 accounts.
- **NFR-PERF-2:** A 5,000-row CSV import completes, including preview, in under
  ten seconds.
- **NFR-PERF-3:** Transaction list queries are paginated and indexed on account
  and booking date.

### 8.4 Deployment and Operations

- **NFR-OPS-1:** The application starts with a single `docker compose up`,
  bringing up the API, the frontend and PostgreSQL.
- **NFR-OPS-2:** Database schema changes are applied by migration. Upgrading to
  a new version never requires the user to recreate their database.
- **NFR-OPS-3:** All configuration is supplied by environment variable with
  documented defaults. No secret is committed to the repository.
- **NFR-OPS-4:** The system provides a documented backup and restore procedure
  for the database.
- **NFR-OPS-5:** A health endpoint reports application and database status.

### 8.5 Quality

- **NFR-QUAL-1:** Every API endpoint has at least one automated test covering
  its success path and its primary failure mode.
- **NFR-QUAL-2:** CSV parsing, deduplication, currency conversion and aggregate
  calculations have unit tests with explicit edge cases.
- **NFR-QUAL-3:** Type checking passes in strict mode. Linting and formatting
  are enforced before commit.

### 8.6 Security

- **NFR-SEC-1:** V1 implements no general per-endpoint rate limiting. The
  deployment serves a single user, by default on localhost, where such limiting
  defends against nothing realistic while adding middleware, shared state and
  new failure modes. Login backoff (FR-AUTH-6) and upload limits (FR-IMP-10) are
  the deliberate exceptions, because each bounds a specific abuse path. A
  deployment exposed beyond localhost should rate limit at the reverse proxy,
  not in the application.

## 9. API Surface (indicative)

REST, with OpenAPI as the published contract.

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/auth/token` | Log in, obtain tokens |
| `POST` | `/auth/refresh` | Refresh access token |
| `GET` `POST` | `/accounts` | List, create |
| `GET` `PATCH` `DELETE` | `/accounts/{id}` | Read, update, delete |
| `POST` | `/transactions/search` | Filtered, paginated transaction search |
| `POST` | `/transactions` | Create manual transaction |
| `PATCH` `DELETE` | `/transactions/{id}` | Update, delete |
| `POST` | `/imports/preview` | Upload CSV, receive parse preview |
| `POST` | `/imports/confirm` | Commit a previewed import |
| `GET` | `/imports` | List import batches |
| `DELETE` | `/imports/{id}` | Revert an import batch |
| `GET` `POST` | `/bank-profiles` | List, create |
| `GET` `POST` | `/categories` | List, create |
| `GET` `POST` | `/category-rules` | List, create |
| `POST` | `/category-rules/apply` | Re-run rules over existing transactions |
| `GET` | `/transfers/suggestions` | Proposed transfer pairs |
| `POST` | `/transfers` | Confirm a transfer link |
| `GET` `POST` | `/goals` | List, create |
| `GET` | `/dashboard/summary` | Aggregated dashboard payload |
| `GET` | `/health` | Liveness and database status |

Transaction search uses `POST` with the filter in the request body rather than a
long query string. It is intended to migrate to the HTTP `QUERY` method
(RFC 10008) once FastAPI supports it natively; request and response shapes are
designed so that only the verb changes.

## 10. Future Scope

Candidates for later versions, deliberately excluded from V1:

- CAMT.053 and MT940 statement import (the Swiss banking standards, which would
  remove most per-bank CSV variation)
- PDF statement parsing
- Recurring transaction detection and upcoming-payment forecasting
- Budgets with per-category limits and alerts
- Multiple users per deployment, for households
- Data export (CSV, JSON) and a full backup/restore UI
- Goal projections based on observed contribution rate

## 11. Open Questions

Q2 and Q3 have been resolved; see [ADR 0009](adr/0009-credit-cards-as-negative-balance-accounts.md)
and [ADR 0010](adr/0010-two-level-category-hierarchy.md). Numbering is retained.

| # | Question | Impact |
|---|---|---|
| Q1 | Which specific Swiss bank CSV formats ship as built-in profiles in V1? | Determines import work; needs real sample exports to answer. |
| Q4 | Should an import batch retain the original uploaded file for audit, and if so for how long? | Privacy versus traceability. |
| Q5 | What happens to goals and rules when their linked account is deleted? | Needs an explicit cascade or block policy. |

## 12. Success Criteria

V1 is complete when a user can:

1. Deploy the application with one command on a clean machine.
2. Create their accounts and import a real CSV export from their bank, correcting
   parse errors from the preview rather than by editing the file.
3. Re-import an overlapping statement the following month without producing
   duplicates.
4. Have at least 80% of transactions categorised automatically after defining a
   handful of rules.
5. See a dashboard that reconciles with the balances shown in their e-banking.
6. Track a saving goal whose progress updates from imported statements without
   any manual bookkeeping.
