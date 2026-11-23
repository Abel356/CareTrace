# November 24, 2026

## Display verified public IPAC citations in the local web workspace

Add an opt-in, read-only citation panel with a query field and an as-of date. Use the existing
server-side API origin and generated contract for `GET /api/v1/public/ipac/citations`. Show
the exact quote, subsection link, jurisdiction, version, and effective dates for a match.
Show an insufficient-evidence state for abstention and a separate unavailable state for API
failures. Keep the panel local to development and test.

Verify a June 27, 2025 match against the running API, an out-of-range date, an unavailable
API, and production exclusion. Run the web tests, lint, typecheck, production build, and
API contract drift check. Commit and push at the repository's 10-line checkpoints.
