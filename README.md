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
uv run --locked pre-commit install
uv run --locked pre-commit run --all-files
```

The lockfiles are generated with `uv lock` and `pnpm install --lockfile-only`.

## Status

Repository foundation and discovery work are in progress.
