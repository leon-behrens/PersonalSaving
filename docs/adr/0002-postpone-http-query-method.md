# ADR 0002: Postpone the HTTP QUERY method until FastAPI supports it

- **Status:** Accepted
- **Date:** 2026-10-24
- **Supersedes:** —

## Context

Transaction search takes a structured filter — account lists, date ranges,
category lists, amount bounds, free text. Encoding that in a URL query string is
awkward and runs into length limits.

The HTTP `QUERY` method, published as **RFC 10008 in September 2026**, exists for
exactly this case: a safe, idempotent method that carries a request body. On
semantics it is the correct verb for this endpoint.

The tooling is not ready:

- **Starlette 1.7.0** (23 September 2026) supports `QUERY` in `HTTPEndpoint`,
  CORS and OpenAPI 3.2 schema generation.
- **FastAPI does not.** There is no `@app.query()` decorator. The implementation
  PR is stalled on Swagger UI rendering, and the tracking discussion remains
  open. `api_route(methods=["QUERY"])` reportedly routes correctly but does not
  produce a correct OpenAPI schema — disqualifying here, because the OpenAPI
  document is the published contract and the source of the generated frontend
  client.
- **Browsers** permit `fetch(url, { method: 'QUERY', body })` today. Method names
  are case-sensitive, and cross-origin requests are preflighted.
- **The main benefit is not yet realised.** `QUERY`'s advantage over `POST` is
  that responses are cacheable. Chrome and Firefox do not cache `QUERY`
  responses, and the Fetch standard left caching unresolved.
- **nginx** method support is an open PR, and its `limit_except` block rejects
  the method silently — a deployment hazard.

## Decision

Transaction search uses `POST /transactions/search` with the filter in the
request body. The request and response shapes are designed so that migrating to
`QUERY` changes only the HTTP verb and a CORS header — no change to payloads,
models or client code structure.

**Revisit when:** FastAPI ships native `QUERY` support with correct OpenAPI 3.2
output.

## Consequences

- Works today across the entire stack — framework, browser, proxy, generated
  client.
- No semantic loss in practice: `POST` with a filter body is the established
  pre-`QUERY` idiom and is universally understood.
- The endpoint is semantically imprecise until migration. `POST` is neither safe
  nor cacheable, so the API claims less than it could about an operation that
  only reads.
- The eventual migration is a breaking change for any client that hardcodes the
  verb, and must follow the versioning policy.

## Alternatives considered

**`GET` with filters in the query string.** Rejected. The filter contains arrays
and ranges, producing unwieldy URLs that approach length limits and are
unpleasant to construct and log.

**`api_route(methods=["QUERY"])` now.** Rejected. It would route, but the
generated OpenAPI document would misrepresent the endpoint, breaking the
contract and the generated client — the two things the specification exists to
guarantee.
