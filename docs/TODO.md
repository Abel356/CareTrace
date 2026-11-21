# November 22, 2026

## Curate and verify the first public Ontario IPAC source snapshot

Select one Ontario long-term-care IPAC provision from Ontario e-Laws. Verify the provision
and its effective interval against the official version pages. Retain an eligible public
source snapshot with the title, jurisdiction, section locator, canonical and version URLs,
retrieval time, effective interval, and SHA-256 checksum of the retained source bytes.

Use the existing source contracts to record one exact passage and its section-relative
Unicode offsets. Add an offline verification command that checks the saved bytes, passage,
and effective interval and fails on a changed checksum, a mismatched span, or an
unverified effective date.

Verify the saved snapshot and rejection cases with the relevant Python lint, type, and
test checks. Commit at the repository's 10-line checkpoints and push each.
