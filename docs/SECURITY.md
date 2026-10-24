# Security

| | |
|---|---|
| **Status** | Planning, no implementation exists yet |
| **Last updated** | 2026-10-24 |
| **Applies to** | PersonalSaving (PS), all versions |

> **PS is not yet software.** This document describes the intended security
> posture of a system still in design. No code has been written, nothing has
> been reviewed or tested, and there is no release to deploy. Treat every
> statement below as a commitment being made, not a protection being offered.

## Threat model

Being explicit about what PS does and does not defend against, because a
security document that implies total protection is worse than none.

### In scope

- **Unauthorised access over the network.** If the port becomes reachable —
  a misconfigured firewall, a reverse proxy, a VPN or tailnet — an attacker must
  not reach the user's financial data.
- **Credential guessing.** A single, predictable user account is an obvious
  brute-force target.
- **Data leaking through side channels.** Logs, error messages and crash output
  must not contain financial data.
- **Third-party exposure.** Any outbound request must be justified, bounded and
  free of financial data.
- **Dependency compromise**, to the limited extent a small project can address
  it: pinned versions and prompt updates.

### Out of scope

- **A compromised host.** PS stores data in a local PostgreSQL instance. Anyone
  with access to that machine or that database has the data, and no application
  measure changes this.
- **Physical access** to the machine PS runs on.
- **Malicious input from the operator.** The user supplies their own CSV files
  and writes their own category rules. They are not an adversary to themselves;
  resource limits exist to prevent accidents, not attacks.
- **Multi-user isolation.** PS serves one user per deployment by design
  ([ADR 0004](adr/0004-single-user-with-authentication.md)). There is no tenancy
  boundary to defend.

## Deployment model

**PS is designed to run on localhost.** That is the default and the supported
configuration.

**PS does not serve TLS.** The application speaks plain HTTP. A deployment
reachable from anywhere other than the local machine must sit behind a reverse
proxy that terminates TLS. Without one, credentials and complete financial
history cross the network in clear text.

Before exposing a deployment beyond localhost:

- Terminate TLS at a reverse proxy with a valid certificate.
- Set a strong, unique password — this is the only thing standing between the
  internet and the data.
- Generate a fresh JWT signing secret for that deployment.
- Apply rate limiting at the proxy. PS deliberately implements none in general
  (`NFR-SEC-1`), beyond login backoff and upload limits.

Exposing a personal finance application to the public internet is a decision
with real consequences. A VPN or tailnet is almost always the better answer than
a public hostname.

## Authentication

- One account per deployment, created at first run from configuration or a CLI
  command. There is no registration endpoint
  ([ADR 0004](adr/0004-single-user-with-authentication.md)).
- Passwords are hashed with **Argon2id**. Plaintext and reversible storage are
  prohibited.
- Login uses the OAuth2 password flow, issuing a short-lived JWT access token
  and a longer-lived refresh token.
- Failed logins are slowed by **exponential backoff, not account lockout**
  (`FR-AUTH-6`). Lockout would let an attacker deny the legitimate user access
  to their own finances.

**The JWT signing secret must be generated per deployment.** A shipped default
secret would let anyone forge a valid token for every installation. The
application must refuse to start if the secret is unset or matches a known
placeholder.

## Data handling

**At rest.** Data lives in a local PostgreSQL instance. PS does not encrypt it
at the application level. Protecting the data at rest is the operator's
responsibility, normally through full-disk encryption.

**Backups.** A backup contains the complete financial history and deserves the
same protection as the live database. Backups written to cloud storage or
removable media should be encrypted.

**Logs.** Logs must never contain transaction descriptions, amounts, account
numbers, authentication tokens or password material (`NFR-PRIV-4`). This applies
to exception tracebacks, which are the usual way such data escapes.

**Secrets.** All configuration arrives through environment variables. No secret
is committed; `.env` is excluded from version control.

## Outbound network traffic

PS makes **one** kind of outbound request: daily exchange rates from
[Frankfurter](https://frankfurter.dev/)
([ADR 0005](adr/0005-currency-conversion-strategy.md)).

That request carries **currency codes and dates only** — never amounts,
balances, account identifiers, descriptions or any other financial data
(`NFR-PRIV-3`). It can be disabled entirely in configuration, after which PS
makes no outbound requests at all and falls back to unconverted per-currency
subtotals.

There is no telemetry, no analytics and no crash reporting, and none will be
added.

## Input handling

**CSV import.** Uploads are bounded by maximum file size, maximum row count and
a parse timeout, enforced before the file is read into memory (`FR-IMP-10`).
Parse failures are reported per row and never abort an import.

**Statement text is untrusted.** A transaction description is written by
whoever sent the payment, not by the user. It reaches the database verbatim and
is rendered in the UI. React escapes by default, which covers this, but any
future code path rendering descriptions as HTML, inserting them into generated
documents, or writing them to exported CSV must treat them as hostile input.
CSV export in particular carries a formula-injection risk once it exists.

## Known limitations

Current by design, listed so nobody assumes otherwise:

- No two-factor authentication.
- No encryption at rest at the application level.
- No audit log of access or administrative actions.
- No token revocation list; a leaked refresh token is valid until it expires.
- No TLS served by the application.
- Retention of uploaded statement files is undecided (PRD open question Q4) and
  has a direct privacy consequence.

## Reporting a vulnerability

Please do **not** open a public issue for a security problem.

Use GitHub's private vulnerability reporting on this repository
(**Security → Report a vulnerability**), which opens a private channel with the
maintainer.

<!-- Optionally add a contact address here as an alternative to GitHub reporting. -->

PS is a personal project maintained by one person in their own time. Expect an
acknowledgement within a week. There is no bug bounty.

When reporting, please include what you did, what happened, and what you
expected — a proof of concept helps considerably.
