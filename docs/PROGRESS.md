# Progress

## November 20, 2026

- Established safe ignore rules, pinned the Python and JavaScript workspace tooling,
  added local secret and style checks, and configured dependency updates. The root setup
  and lint commands and the repository-wide hooks passed.
- Added the runnable FastAPI application, health and build endpoints, production settings
  validation, explicit host and CORS rules, a body-size limit, and structured request logs.
  HTTP error responses carry server-assigned IDs and omit request and exception details.
- Added immutable source and citation contracts, timed policy attestations, provisional
  obligations, and the four evidence-checked coverage labels. Checklist packets bind a
  reviewer decision to the exact versioned content and require traceable citations.
- Added SQLAlchemy transactions, Alembic migrations, immutable source and policy versions,
  tenant-scoped policy review records, and ordered append-only audit events for overrides
  and approvals. Local migration and repository checks use SQLite and generated PostgreSQL SQL.
- Added a local UTF-8 text admission gate for public, synthetic, and authorized
  de-identified inputs. It preserves original bytes and checksums, rejects unsupported
  files and duplicates within a tenant, and returns separately parsed text. Upload routes,
  PDF parsing, and OCR remain future work.
- Shipped a Next.js workspace with API status, evidence abstention, human review and data
  guidance, and a generated OpenAPI TypeScript contract. Verified the available and
  unavailable UI states against the running FastAPI and Next.js processes over loopback HTTP.
- Added GitHub Actions for Python, live PostgreSQL 17 with pgvector, the web build, contract
  drift, secret scanning, and pull-request dependency review. The hosted Python and web jobs
  passed 61 Python tests, including the live migration, and seven web tests. The local suite
  passed 60 Python tests and seven web tests, with the live PostgreSQL test skipped locally. Ruff, mypy,
  ESLint, Prettier, both production builds, and the contract drift check passed.
  [GitHub Actions run](https://github.com/Abel356/CareTrace/actions/runs/44773943926)
- Pushed 17 commits for the foundation session, including this handoff. The recurring build
  now completes one functional task per run and commits at 10-line code checkpoints.
- The verified regulatory corpus, authenticated policy intake, and customer-facing export
  remain pending. The test client emits one upstream deprecation warning.

## November 19, 2026

- Created the public `Abel356/CareTrace` GitHub repository on `main`.
- Added the discovery PRD and a concise public-facing project overview.
- Established healthcare-data safety, source provenance, human-review, and commit-quality rules.
- Selected a FastAPI + Next.js/TypeScript monorepo with PostgreSQL/pgvector and PostgreSQL full-text search for the first prototype.
- Chose small, functional commits over artificial line-count fragmentation while retaining a 100–140 daily target when the backlog supports it.
- Next: establish the tested monorepo foundation, core domain contracts, persistence model, and ingestion boundaries.
