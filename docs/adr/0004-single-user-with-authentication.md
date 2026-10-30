# ADR 0004: One user per deployment, with full authentication

- **Status:** Superseded by [ADR 0012](0012-versioned-user-model-and-administrator-boundary.md)
- **Date:** 2026-10-24
- **Supersedes:** —

## Context

PS is self-hosted, one deployment per person. Three models were possible:
multiple users sharing a deployment, a single user with authentication, or no
authentication at all on the assumption that localhost is private.

Multi-user would require an ownership column on every domain table and an
authorization check on every endpoint. No authentication would be simplest, but
would mean that any future exposure of the port — a misconfigured firewall, a
reverse proxy, a tailnet — exposes the user's complete financial history.

Learning API authentication properly is also an explicit goal of this project.

## Decision

Exactly one user account per deployment. It is created at first run from
configuration or via a CLI command; there is no public registration endpoint.

Authentication uses the OAuth2 password flow with Argon2id password hashing,
issuing a short-lived JWT access token and a longer-lived refresh token. Every
endpoint except login, token refresh and health requires a valid token.

## Consequences

- Domain tables carry no `user_id`, keeping the schema and every query simpler.
- The deployment is not exposed merely because the port becomes reachable.
- Authentication is implemented to a realistic standard, satisfying the learning
  goal, without multiplying schema complexity.
- Households who share finances need one deployment each, and cannot see a
  combined picture.
- Adding multi-user support later means adding ownership to every table,
  authorization to every endpoint, and a migration backfilling the existing
  single user. Real work, but bounded and mechanical.

## Alternatives considered

**Multi-user households.** More realistic API practice and a genuinely useful
feature, but it doubles the scope of both the data model and the authorization
surface. Deferred to future scope.

**No authentication in V1.** Rejected. It drops the auth learning goal, and
retrofitting authentication onto an application that never had it is closer to a
rewrite than an addition. A personal finance application with no login is also
difficult to defend regardless of where it listens.
