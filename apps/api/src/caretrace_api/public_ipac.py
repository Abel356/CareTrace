from datetime import date
from pathlib import Path

from caretrace_api.citation_lookup import (
    CitedPassage,
    InsufficientEvidence,
    PublicCitationLookup,
    PublicCitationMatch,
)
from caretrace_api.public_snapshot import verify_snapshot

_SNAPSHOT = Path(__file__).resolve().parents[4] / "corpus/ontario/220246/v28"


def lookup(query: str, as_of: date) -> PublicCitationLookup:
    keyword = query.strip().casefold()
    if not keyword:
        return InsufficientEvidence(status="insufficient_evidence")

    try:
        manifest = verify_snapshot(_SNAPSHOT)
    except (OSError, ValueError, OverflowError):
        return InsufficientEvidence(status="insufficient_evidence")

    if (
        manifest.version.is_effective_on(as_of) is not True
        or keyword not in manifest.citation.quote.casefold()
    ):
        return InsufficientEvidence(status="insufficient_evidence")

    passage = CitedPassage(
        locator=manifest.locator,
        citation_url=manifest.citation_url,
        span=manifest.citation,
    )
    return PublicCitationMatch(
        status="matched",
        document=manifest.document,
        version=manifest.version,
        passages=(passage,),
    )
