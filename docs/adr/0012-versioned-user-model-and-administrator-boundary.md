# ADR 0012: Single-user v0.1, multi-user v1.0 and restricted administration

- **Status:** Accepted
- **Date:** 2026-10-30
- **Updated:** 2026-10-30 — aligned with System Design section 5.2.1
- **Supersedes:** [ADR 0004](0004-single-user-with-authentication.md)

## Context

Local v0.1 serves one person per deployment. The target v1.0 serves multiple
users, whose financial records must remain isolated. User provisioning and
password recovery require administration without granting administrators access
to other users' financial records through the application.

## Decision

### Local v0.1

Exactly one user exists per local deployment. Initial login credentials are
provided through `.env`. On first login, the user can set their name and must
change their password.

If the password is forgotten, a local administrative CLI command sets a new
one-time password. The user can log in once with that password to set a new
password. The detailed bootstrap, credential lifetime and session-revocation
procedures remain to be specified in the authentication contract.

### Multi-user v1.0

Multiple users may use one deployment. Authentication is delegated to an OpenID
Connect provider using Authorization Code with PKCE. The provider remains
undecided; Amazon Cognito User Pools is a candidate for managed hosting.
Provider-specific administrator bootstrap, user provisioning and password
recovery procedures remain open rather than being prescribed as application CLI
or `.env` operations.

PersonalSaving retains responsibility for financial-data authorization. The
administrator may provision users and initiate password resets but has no
application permission to read, search, export or modify another user's financial
records. These administrative capabilities do not grant financial-data access.

Financial resources must be scoped to their owner, directly or through an
unambiguous parent relationship. Every resource access, list, aggregate, import
and background operation enforces that scope. A client-supplied user or account
identifier is never proof of authorization. The administrator role must not
bypass financial ownership checks.

### Authentication responsibilities

The local implementation owns credential verification and password storage.
V1.0 delegates those responsibilities to the selected identity provider rather
than requiring PersonalSaving to store or hash provider-managed passwords.

Authentication remains required for financial operations in both versions.
Local login and recovery, and v1.0 sign-in, callback, refresh and logout behavior,
will be specified separately. Readiness remains unauthenticated. Browser
credential handling, token lifetimes and revocation policy remain open. Neither
version adopts the OAuth2 resource owner password credentials grant prohibited
by RFC 9700 section 2.4.

### Meaning and limits of administrator privacy

The restriction is enforced by application authorization. It does not establish
cryptographic isolation from an operator who controls the database, application
code, host or signing keys. Administrator-issued replacement login passwords
can also enable impersonation. If administrators must be technically unable to
assume a user's identity, recovery must use an independently verified user channel
and cannot simply give the administrator a new unrestricted password. Stronger
protection against the host operator would require a separate encryption/key
management design and is not claimed by this decision.

## Consequences

- V0.1 stays single-user, while v1.0 explicitly includes multi-user isolation.
- Moving existing data to v1.0 requires an ownership migration and backfill to
  the original user before additional users can access the deployment.
- V1.0 needs cross-user authorization tests, including administrator denial,
  collection filters, aggregates and indirect resource relationships.
- User provisioning and recovery must be designed without a general-purpose
  administrator impersonation endpoint.
- The PRD and authentication contract must be reconciled with this revised
  scope; older single-user descriptions are historical, not v1.0 requirements.

## Alternatives considered

**One user per deployment forever.** Simpler isolation, but does not satisfy the
chosen multi-user v1.0 scope.

**Administrator has access to all financial data.** Easier to implement through
a global role bypass, but explicitly rejected by the privacy requirement.

**Multi-user v0.1.** Brings ownership and administration work into the first local
release unnecessarily. Deferred to v1.0, with an explicit migration requirement.

## References

- [RFC 9700, section 2.4](https://www.rfc-editor.org/rfc/rfc9700.html#section-2.4)
