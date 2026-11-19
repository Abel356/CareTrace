# Tomorrow's TODO — November 20, 2026

## Session outcome

Deliver a tested monorepo foundation for CareTrace: a runnable FastAPI service, a runnable Next.js shell,
typed domain contracts, an initial PostgreSQL schema, and explicit public/de-identified-data boundaries.

The 100–140 commit range is a throughput target, not permission to create no-op or artificially fragmented
history. Every commit must complete a coherent micro-task, carry a descriptive message, and be pushed.

## 1. Repository and toolchain — target 12–16 commits

- Add root ignore, editor, environment-example, and licensing files.
- Document supported Python, Node.js, package-manager, and PostgreSQL versions.
- Establish `apps/api`, `apps/web`, `packages/contracts`, and `infra` boundaries.
- Add root commands for setup, linting, typing, tests, builds, and local development.
- Add pre-commit checks for whitespace, secrets, Python, and TypeScript.
- Add dependency-update and security-reporting configuration.
- Record architecture decisions for the monorepo and the MVP retrieval stack.
- Verify a clean clone can discover every documented command.

## 2. FastAPI foundation — target 18–22 commits

- Create the API package and application factory.
- Add typed settings with safe development defaults and strict production validation.
- Add structured logging, request IDs, and a consistent error envelope.
- Add liveness, readiness, and build-information endpoints.
- Add API versioning and OpenAPI metadata with the product's non-advice boundary.
- Add CORS, trusted-host, security-header, and request-size configuration.
- Add dependency-injected clock, ID generator, and database-session interfaces.
- Add unit tests for startup, settings, middleware, errors, and health endpoints.

## 3. Domain contracts — target 22–28 commits

- Model source documents, source versions, sections, and immutable citation spans.
- Model jurisdictions, as-of dates, effective dates, retrieval timestamps, and checksums.
- Model provisional obligations with actor, action, condition, frequency, and review state.
- Model policy documents, excerpts, authorization state, and de-identification attestation.
- Model coverage assessments using only the four PRD-approved document-coverage labels.
- Model evidence checklist items, owners, states, and source-backed rationale.
- Model reviewer overrides, reasons, approvals, unresolved items, and audit events.
- Model export packets with source, prompt, model, corpus, and reviewer versions.
- Add serialization, validation, equality, immutability, and invalid-state tests.

## 4. Persistence foundation — target 18–22 commits

- Configure SQLAlchemy 2 sessions for SQLite tests and PostgreSQL runtime use.
- Add tables and repositories for sources, versions, sections, and citation spans.
- Add tables and repositories for obligations, policies, excerpts, and assessments.
- Add tables and repositories for evidence items, decisions, approvals, and audit events.
- Enforce tenant keys, immutable source-version checksums, and append-only audit ordering.
- Add Alembic configuration and the initial migration with pgvector guarded by dialect.
- Add transaction, constraint, repository-contract, and migration smoke tests.

## 5. Ingestion and safety boundaries — target 15–18 commits

- Define an ingestion manifest and deterministic content-checksum service.
- Add public-source, synthetic, and authorized-de-identified classification states.
- Reject unsupported uploads and missing authorization attestations by default.
- Add file-size, media-type, extension, and duplicate-content validation.
- Preserve originals while separating parsed text, chunks, and derived obligations.
- Define parser and OCR ports without claiming support before implementation exists.
- Add fixtures and tests using synthetic content only; commit no real client policies or PHI.

## 6. Next.js shell and shared contracts — target 12–15 commits

- Create the web app with strict TypeScript, linting, formatting, and test configuration.
- Add an accessible product shell, navigation landmarks, and development status banner.
- Add visible legal-advice, human-review, source-date, and data-handling notices.
- Add typed API-client boundaries and generated-contract drift checks.
- Add health/status UI states with loading, unavailable, and insufficient-evidence language.
- Add component and accessibility tests for the initial shell.

## 7. CI, verification, and handoff — target 6–9 commits

- Add GitHub Actions for Python lint/type/test and web lint/type/test/build jobs.
- Add secret scanning, dependency review, and least-privilege workflow permissions.
- Run the full available check suite and record exact results.
- Update `docs/PROGRESS.md` with completed work, test counts, and open risks.
- Replace this file with a concrete November 21 plan based on observed progress.

## Completion gates

- No secrets, PHI, identifiable resident data, or unapproved organizational content is committed.
- Both applications start from documented commands and expose only implemented capabilities.
- Core domain invalid states fail deterministically and are covered by tests.
- CI is green, the working tree is clean, all commits are pushed, and tomorrow's plan is current.
