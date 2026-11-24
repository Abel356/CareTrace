# November 25, 2026

## Add a second verified passage to the historical IPAC lookup

Curate one adjacent subsection of O. Reg. 246/22, s. 102 from the official Ontario
e-Laws v28 page. Extend the retained snapshot and verifier so each passage keeps
its own subsection link and exact Unicode span, with the shared version,
jurisdiction, effective interval, retrieval time, and checksum preserved.

Verify that the existing query still returns its exact quote, a query unique to
the added passage returns the new subsection, and dates outside the verified
interval or a tampered snapshot still produce insufficient evidence. Check the
result through the existing API and local web panel, run contract drift and the
relevant suites, then push at the repository's checkpoints.
