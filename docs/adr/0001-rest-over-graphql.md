# ADR 0001: REST over GraphQL for the public API

- **Status:** Accepted
- **Date:** 2026-10-24
- **Supersedes:** —

## Context

PS needs a public API contract between its FastAPI backend and its React
frontend.

GraphQL was initially preferred, on the reasoning that most operations are
database queries and so a "query language" seemed the natural fit. That
reasoning does not hold. The *graph* in GraphQL refers to the graph of related
entities exposed by the API, not to SQL. A GraphQL server is a set of resolver
functions; the SQL behind them is the same SQL a REST handler would run, and it
is written by hand either way.

GraphQL would in fact make the data access harder initially. A request for fifty
transactions that each include their account issues fifty-one queries unless
DataLoader-style batching is added — the N+1 problem, which REST sidesteps
because the server controls the query shape.

The conditions under which GraphQL earns its complexity — many heterogeneous
clients the API owner does not control, deeply nested graph traversal — do not
apply. PS has one frontend, built and owned by the same developer, over largely
flat tabular data plus dashboard aggregates that want purpose-built endpoints
regardless.

## Decision

The public API is REST, with OpenAPI as the published contract. FastAPI
generates the OpenAPI document from the route definitions and Pydantic models,
and the TypeScript client for the frontend is generated from that document.

## Consequences

- No resolver layer, no batching infrastructure, no GraphQL-specific caching or
  authorization concerns.
- Interactive documentation and a typed frontend client come for free from the
  generated specification.
- The skills involved transfer to the widest range of future work.
- Clients cannot select fields, so response shapes are fixed by the server.
  Some over-fetching is possible; at this data scale it is irrelevant.
- If a second client with materially different data needs ever appears, this
  should be revisited.

## Alternatives considered

**GraphQL via Strawberry.** Rejected for V1 on the reasoning above. Explicitly
not rejected forever: adding a GraphQL layer later, over the same service layer,
is planned as a deliberate comparison exercise. Building both over one domain
teaches considerably more than choosing one blind.

**Graphene.** Considered as the GraphQL library and rejected independently; it
is largely dormant, and Strawberry is the actively maintained option.
