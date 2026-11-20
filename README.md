# CareTrace

CareTrace is an AI-assisted inspection-readiness workspace for Ontario long-term-care teams.

It maps versioned regulatory obligations to policy passages and evidence requests while keeping
citations, uncertainty, reviewer decisions, and human approval visible throughout the workflow.

CareTrace is a discovery-stage product hypothesis. It does not provide legal advice, certify
compliance, assess residents, or replace qualified clinical, privacy, or legal review.

## Initial scope

- Ontario long-term-care infection prevention and control (IPAC)
- Public regulatory sources and inspection reports
- Synthetic or explicitly authorized de-identified policies
- Source-grounded obligation maps, document-coverage reviews, and evidence checklists
- Human-reviewed Markdown or PDF exports with an audit trail

See [the product requirements](docs/PRD.md), [architecture](docs/ARCHITECTURE.md),
and [the next session plan](docs/TODO.md).

## Development

Install Python 3.13 (or let uv manage it), uv 0.13.9 or a later 0.13 release,
Node.js 24, and pnpm 11.25.0. PostgreSQL 17 is the target for persistence development.

```sh
pnpm run setup
pnpm run lint
pnpm run typecheck
pnpm run test
pnpm run build
uv run --locked pre-commit install
uv run --locked pre-commit run --all-files
```

The lockfiles are generated with `uv lock` and `pnpm install --lockfile-only`.

Run `pnpm run dev:api` from the repository root, then open `http://127.0.0.1:8000/docs`.
The API exposes `/livez` for process liveness, `/readyz` for service readiness, and
`/api/v1/build` for the installed API version. Local development can run without a
database. When a database URL is configured, readiness also checks database connectivity.

See `.env.example` for the request-size limit and explicit host and browser-origin
allowlists. Production requires an explicit host list and HTTPS origins. Error responses
carry a server-generated request ID, which also appears in the structured request log.

To initialize persistence, set `CARETRACE_DATABASE_URL` using `.env.example` as a
template, then run `pnpm run db:migrate`. PostgreSQL requires the server's pgvector
extension files and a migration role able to install the extension. Use a separate,
lower-privilege connection for the running API. SQLite is supported for local testing.

Run `pnpm run dev:web` in another terminal and open http://127.0.0.1:3000.
The web server reads the API readiness endpoint. For a different API origin, copy
`apps/web/.env.example` to `apps/web/.env.local` and set `CARETRACE_API_ORIGIN`.
Run `pnpm run contracts:generate` after changing OpenAPI and `pnpm run contracts:check`
to detect stale TypeScript contracts.

## Status

Repository foundation and discovery work are in progress.
