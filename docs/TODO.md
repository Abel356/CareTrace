# November 21, 2026

## Implement a date-qualified citation lookup for a synthetic IPAC corpus

Add one versioned, read-only API route that takes a keyword query and an as-of date.
Search a clearly marked synthetic fixture with two nonoverlapping versions of the same
source. Return exact cited passages with their document title, jurisdiction, source URL,
version, effective interval, retrieval time, checksum, and character offsets.

Return an explicit `insufficient_evidence` result when the query has no matching passage,
the effective interval is uncertain, or multiple versions qualify. Keep the fixture
restricted to explicit development and test use.

Test both version windows, their shared date boundary, Unicode span verification,
and abstention. Regenerate the TypeScript contract and verify contract drift, lint,
types, tests, and builds. Commit at the repository's 10-line checkpoints and push each.
