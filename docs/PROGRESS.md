# Progress

## November 27, 2026

- Retained O. Reg. 246/22 v29, s. 102 (2), alongside subsection (3). A fresh
  Ontario e-Laws download reproduced the November 22 capture's July 1–31, 2025
  historical notice and both excerpts under `BK129`. The manifest retains the
  original capture time and records the updated SHA-256. The surveillance span
  is `[4, 273)` in v29 and `[4, 275)` in v28 because the clause spacing differs.
  The v29 subsection (3) span remains `[4, 143)`.
  [Ontario e-Laws v29](https://www.ontario.ca/laws/regulation/220246/v29#BK129)
- Both snapshot verifiers passed. Eleven live FastAPI and Next.js loopback cases
  checked the API responses and rendered panel. On June 30 and July 1,
  `surveillance` returns subsection (2) and `protocols` returns both subsections,
  each with the selected version and its exact citation. June 26 and August 1
  return insufficient evidence. Automated checks cover both ends of each version.
- Local checks passed 114 Python tests and 14 web tests, lint, strict types,
  private-key and secret scans, both production builds, and OpenAPI drift detection.
  Windows blocked the secret-hook launcher, so its Python entry point ran directly.
  The live PostgreSQL test was skipped locally. Hosted CI passed 115 Python tests,
  including PostgreSQL with pgvector, and 14 web tests. The existing upstream
  TestClient deprecation warning remains. No task blocker remains.
  [GitHub Actions run for the final code checkpoint](https://github.com/Abel356/CareTrace/actions/runs/46033893095)

### Checkpoints

Seven commits cover the task and handoff. They verify the v28 baseline and
outer date boundaries, allowlist the new public digest, retain the generated
v29 evidence, verify surveillance spans in both versions, verify shared-query
citations, document the expanded excerpt and retire its obsolete digest, and
record verification and the November 28 plan. The single-passage expansion
and its regressions supported seven coherent checkpoints.

## November 26, 2026

- Retained O. Reg. 246/22 v29, s. 102 (3), for July 1 through July 31, 2025,
  inclusive. Confirmed the historical notice through the indexed Ontario e-Laws
  page and extracted the subsection from the official HTML saved November 22.
  The attributed UTF-8 excerpt and manifest preserve the original retrieval time,
  checksum, version, jurisdiction, and exact span under the section 102 anchor.
  A fresh direct fetch was unavailable.
  [Ontario e-Laws v29](https://www.ontario.ca/laws/regulation/220246/v29#BK129)
- The opt-in lookup verifies both snapshots before resolving the requested date.
  It returns exact passages from the single applicable version and abstains for
  gaps, overlapping dates, missing or altered evidence, and unmatched queries.
  Subsection 102 (3) has the same wording in both versions and a version-specific
  citation link. July surveillance queries abstain because v29 contains only
  subsection 102 (3).
  [Ontario e-Laws v28](https://www.ontario.ca/laws/regulation/220246/v28#BK129)
- Eight live FastAPI and Next.js loopback cases checked the June 30 and July 1
  changeover, July 31 coverage, both outer date boundaries, and passage selection.
  Automated tests also checked overlapping verified intervals, unavailable or
  modified snapshots, and exact web citations with an accessibility scan.
- Local checks passed 109 Python tests and 14 web tests, both snapshot verifiers,
  lint, strict typing, builds, private-key and secret scans, and OpenAPI drift
  detection. One live PostgreSQL test was skipped locally. Windows blocked the
  installed secret-check launcher, so staged checks ran directly before each
  commit. Hosted CI passed 110 Python tests with PostgreSQL and pgvector and
  14 web tests. The existing upstream TestClient deprecation warning remains.
  [GitHub Actions run](https://github.com/Abel356/CareTrace/actions/runs/45877062316)

### Checkpoints

Nine commits cover the changeover and handoff. They cover the public digest,
the retained snapshot, version selection, four date boundaries, overlap
abstention, invalid evidence, panel rendering, usage documentation, and this
handoff. The task reached nine coherent checkpoints within its snapshot,
lookup, and verification scope.

## November 25, 2026

- Added O. Reg. 246/22 v28, s. 102 (2) to the opt-in public IPAC lookup.
  The snapshot verifies every passage against the shared SHA-256 and historical
  effective interval. Each passage carries its own subsection locator and
  exact Unicode span. Both e-Laws links open at the official section 102
  anchor, which serves both subsections.
  [Ontario e-Laws v28](https://www.ontario.ca/laws/regulation/220246/v28#BK129)
- Compared the retained UTF-8 bytes with the official e-Laws HTML saved on
  November 22. Extracted the historical notice and the subsection and clause
  paragraphs under `BK129`, decoded HTML entities, stripped markup and outer
  whitespace, and preserved the clause line breaks and nonbreaking spaces.
  Joined the notice and subsections with blank lines, then checked the
  resulting SHA-256 and the June 27–30 interval against the adjacent versions.
  A fresh e-Laws request was unavailable during this run.
- Verified the live API and web panel over loopback. `surveillance` returned
  subsection (2), `standards and protocols` returned subsection (3), and
  `protocols` returned both. The panel rendered the exact quotes and source
  links. June 26 and July 1 returned insufficient evidence. Automated tests
  also covered missing and modified snapshots, invalid spans, and duplicate
  section identifiers.
- Local verification passed 101 Python tests, 13 web tests, repository hooks,
  lint, strict type checks, the Python package and Next.js builds, and OpenAPI
  contract drift. The local suite skipped the disposable PostgreSQL test.
  GitHub Actions passed all 102 Python tests, including PostgreSQL with
  pgvector, and all 13 web tests. The existing TestClient deprecation warning
  remains.
  [GitHub Actions run](https://github.com/Abel356/CareTrace/actions/runs/45711754471)

### Checkpoints

Twenty-two pushed commits cover the task, including this handoff. The run
started with 20 published implementation, corpus, and verification checkpoints
from `7f06cda` through `e8b1cc0`. The API regression in `3ba44e8` confirms that
a shared query returns both citations at either end of the verified interval.
The remaining work after that regression was verification and documentation.

## November 24, 2026

- Shipped an opt-in public IPAC citation panel for local development and test.
  The workspace uses the server-side API origin and generated contract to look
  up a query as of a selected date. A match shows the exact excerpt, subsection
  link, jurisdiction, version, and effective interval.
- Live loopback checks against Next.js and FastAPI returned the retained quote
  and link for `protocols` on June 27, 2025, insufficient evidence on July 1,
  and a distinct unavailable message after the API stopped. The running
  production build excluded the panel and its link with the flag enabled.
- All 13 local web tests passed, along with ESLint, Prettier, TypeScript,
  the Next.js production build, the snapshot verifier, and OpenAPI contract
  drift detection. The rendered panel passed the automated accessibility check.
  Browser interaction was unavailable because the Windows browser tool could
  not enforce URL policy in Firefox.
- Windows Application Control blocked the installed Git hook interpreter and
  some native Python modules. Staged whitespace, private-key, secret, and
  relevant web checks ran directly. An alternate local Python runtime ran
  the API and snapshot verifier. Its full suite reported 86 passes, seven
  failures loading the PostgreSQL driver, and one live-database skip.
  GitHub Actions passed all 94 Python tests, including live PostgreSQL with
  pgvector, and all 13 web tests, builds, lint, typing, and contract drift.
  The existing TestClient deprecation warning remains.
  [GitHub Actions run](https://github.com/Abel356/CareTrace/actions/runs/45455287068)

### Checkpoints

Ten commits cover the task and handoff.

1. `9748f30` shares the server-side API request settings with readiness.
2. `a8356e4` fetches public citations using the generated contract.
3. `771c205` renders the exact quote, provenance, and distinct result states.
4. `95c4198` adds the query and as-of date form.
5. `92d46fb` enables the panel only in opted-in development and test runs.
6. `348806d` makes form controls and quotes readable at narrow widths.
7. `061ae21` verifies exact citation provenance and panel accessibility.
8. `3e5df4f` verifies evidence abstention and unavailable responses.
9. `cd5e919` verifies opt-out and production exclusion.
10. This handoff documents activation, verification, and the November 25 plan.

## November 23, 2026

- Shipped `GET /api/v1/public/ipac/citations` behind `CARETRACE_ENABLE_PUBLIC_IPAC`
  in development and test. Each lookup validates the retained bytes, effective interval,
  and exact quote before returning O. Reg. 246/22 v28, s. 102 (3), with source provenance.
  The endpoint matches queries within the verified span and abstains for missing matches,
  dates outside June 27–30, 2025, or unavailable or invalid evidence.
  [Ontario e-Laws v28](https://www.ontario.ca/laws/regulation/220246/v28#BK129)
- Thirteen HTTP cases covered provenance, offsets, both date boundaries, mismatches,
  missing and tampered snapshots, local activation, production exclusion, method limits,
  and the standard validation response. The offline verification command passed.
- Local checks passed 93 Python tests, seven web tests, Ruff, mypy, ESLint, Prettier,
  all repository hooks, Python and Next.js builds, and TypeScript contract drift.
  GitHub Actions passed 94 Python tests, including the live PostgreSQL 17/pgvector
  check skipped locally, and the web and API contract job. The existing TestClient
  deprecation warning persists. No task blocker remains.
  [GitHub Actions run](https://github.com/Abel356/CareTrace/actions/runs/45217304039)

### Checkpoints

Nine commits cover the task and handoff.

1. `9ca1fed` defines the public citation response contract.
2. `548cb84` returns only verified, date-matched spans.
3. `d8e5e93` adds the opt-in local HTTP route.
4. `b151eec` verifies exact citations at both date boundaries.
5. `d334286` verifies abstention for unsupported dates and evidence.
6. `ee9ac43` verifies local activation and read-only behavior.
7. `d897a89` exports the public route and documents activation.
8. `b0a719e` regenerates the OpenAPI TypeScript types with `pnpm run contracts:generate`.
9. This handoff records verification and the November 24 plan.

## November 22, 2026

- Retained the first public IPAC snapshot, O. Reg. 246/22 (General), v28, s. 102 (3).
  Ontario e-Laws lists June 27 through June 30, 2025, inclusive. The preceding version
  ends June 26 and the following version starts July 1. The manifest records the
  canonical and version URLs, Ontario jurisdiction, UTC retrieval time, SHA-256,
  and a half-open Unicode span within the subsection.
  [Previous version](https://www.ontario.ca/laws/regulation/220246/v27)
  [Retained citation](https://www.ontario.ca/laws/regulation/220246/v28#BK129)
  [Following version](https://www.ontario.ca/laws/regulation/220246/v29)
- Fetched the three official version pages with `curl`. A Python extraction decoded HTML
  entities and removed tags and outer layout whitespace from the v28 historical notice
  and the subsection paragraph under `BK129`. `source.txt` holds those two blocks,
  separated by a blank line and encoded as UTF-8 with LF. The SHA-256 covers that exact
  excerpt file. The adjacent notice credits the King's Printer and identifies the reproduction.
- The offline command verified the real fixture. Five tests covered the real citation and
  both date boundaries, altered bytes, shifted offsets, and inaccurate or missing effective
  dates. The secret scanner allowed only the exact known public digest after flagging it.
- Local verification passed 80 Python tests and seven web tests, Ruff, mypy, ESLint,
  Prettier, contract drift, all pre-commit hooks, and Python and Next.js production builds.
  GitHub Actions passed 81 Python tests including the live PostgreSQL 17/pgvector test,
  which was skipped locally, and the web and API contract job. The existing TestClient
  deprecation warning appeared in both Python runs. No task blocker remains.
  [GitHub Actions run](https://github.com/Abel356/CareTrace/actions/runs/45045775046)

### Checkpoints

Ten commits cover the task and handoff.

1. `9126bd3` reads a closed e-Laws historical period.
2. `77dc6f6` verifies retained bytes and the effective interval.
3. `d58111c` validates provenance and exact citation spans.
4. `aff2063` exposes the offline verification command.
5. `ee7db76` allowlists the exact public digest in the secret scanner.
6. `f601ddc` retains the attributed snapshot and provenance manifest.
7. `0cebcad` tests the retained citation and version boundaries.
8. `2cd7256` tests checksum rejection.
9. `27046df` tests citation and effective-date rejection.
10. This handoff records verification and the November 23 plan.

## November 21, 2026

- Shipped `GET /api/v1/synthetic/ipac/citations` as an opt-in development and test endpoint.
  The read-only search resolves the two fictional revisions at the June 1 changeover and
  returns exact paragraph spans with source and version metadata. Missing matches and
  uncertain or overlapping effective intervals return `insufficient_evidence`.
- Verified 15 endpoint cases, including both version windows, the shared boundary, Unicode
  offsets, checksum, provenance, abstention, production exclusion, and HTTP behavior.
- Local verification passed 75 Python tests and seven web tests, Ruff, mypy, ESLint,
  Prettier, Python packaging, the Next.js production build, all pre-commit hooks, and
  TypeScript contract drift detection. The live PostgreSQL test was skipped locally.
  GitHub Actions passed 76 Python tests with PostgreSQL 17/pgvector and the web and API
  contract job. The existing TestClient deprecation warning appeared in both Python runs.
  [GitHub Actions run](https://github.com/Abel356/CareTrace/actions/runs/44933546508)

### Checkpoints

1. `9a9a9fa` resolves exactly one known effective version.
2. `d40fff0` extracts exact spans for keyword-matching paragraphs.
3. `cc10ca3` gives the fictional Ontario source a stable identity.
4. `de87918` binds revision metadata and SHA-256 checksums to fixture text.
5. `602ee63` adds two nonoverlapping revisions with a shared boundary.
6. `4c6a0fb` models the cited passages and their provenance.
7. `1793142` assembles cited matches and explicit abstention results.
8. `af741e9` gates the HTTP route and generates its TypeScript contract.
9. `426be91` exercises both version windows and the exact changeover date.
10. `1111e88` verifies provenance, digest, and Unicode citation offsets.
11. `8f88eab` covers absent, uncertain, and overlapping evidence.
12. `6ec643a` verifies development opt-in and production exclusion.
13. `412210f` verifies the read-only method and standard validation error.
14. This handoff records verification and the November 22 plan.

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
