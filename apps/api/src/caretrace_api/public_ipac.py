from datetime import date
from pathlib import Path

from caretrace_api.citation_lookup import (
    CitedPassage,
    InsufficientEvidence,
    PublicCitationLookup,
    PublicCitationMatch,
    resolve_version,
)
from caretrace_api.public_snapshot import verify_snapshot

_CORPUS = Path(__file__).resolve().parents[4] / "corpus/ontario/220246"
_SNAPSHOTS = (_CORPUS / "v28", _CORPUS / "v29")


def lookup(query: str, as_of: date) -> PublicCitationLookup:
    keyword = query.strip().casefold()
    if not keyword:
        return InsufficientEvidence(status="insufficient_evidence")

    try:
        manifests = tuple(verify_snapshot(path) for path in _SNAPSHOTS)
    except (OSError, ValueError, OverflowError):
        return InsufficientEvidence(status="insufficient_evidence")

    version = resolve_version((manifest.version for manifest in manifests), as_of)
    if version is None:
        return InsufficientEvidence(status="insufficient_evidence")
    manifest = next(manifest for manifest in manifests if manifest.version == version)

    matches = tuple(
        passage
        for passage in manifest.listed_passages()
        if keyword in passage.citation.quote.casefold()
    )
    if not matches:
        return InsufficientEvidence(status="insufficient_evidence")

    return PublicCitationMatch(
        status="matched",
        document=manifest.document,
        version=manifest.version,
        passages=tuple(
            CitedPassage(
                locator=passage.locator,
                citation_url=passage.citation_url,
                span=passage.citation,
            )
            for passage in matches
        ),
    )
