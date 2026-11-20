# Prototype architecture

## Workspace boundaries

| Path | Responsibility |
| --- | --- |
| `apps/api` | FastAPI entry point, configuration, and application workflows |
| `apps/web` | Next.js interface and typed API client |
| `packages/contracts` | Domain and wire contracts shared across the application |
| `infra` | Local infrastructure and database migrations |

Use one repository and version changes to the API, contracts, and client together. Keep
the HTTP interface versioned and use its OpenAPI schema to verify client contracts.

## Retrieval and data boundaries

Use PostgreSQL 17 for the prototype. Start with full-text retrieval and structured
filters on source versions, jurisdictions, as-of dates, and citation spans. Add vector
retrieval through pgvector when a bounded evaluation can measure its contribution.
Retain source and version metadata with each candidate result so that citation and date
checks can be performed before the result is used. Abstain when a supported passage is
unavailable.

Keep authorized inputs and original documents out of Git. Use synthetic fixtures for
policy and workflow tests. Preserve exact source passages and metadata for public evidence.
Document-coverage assessments and evidence suggestions require qualified human review.
