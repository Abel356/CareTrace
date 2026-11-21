from datetime import UTC, date, datetime
from hashlib import sha256
from uuid import NAMESPACE_URL, uuid5

from caretrace_contracts.sources import (
    Jurisdiction,
    SourceDocument,
    SourceKind,
    SourceSection,
    SourceVersion,
)
from pydantic import HttpUrl

_DOCUMENT_URL = "https://caretrace.invalid/synthetic/ipac"
DOCUMENT = SourceDocument(
    id=uuid5(NAMESPACE_URL, _DOCUMENT_URL),
    title="Synthetic IPAC training drill",
    jurisdiction=Jurisdiction.ONTARIO,
    kind=SourceKind.REGULATION,
    source_url=HttpUrl(_DOCUMENT_URL),
)


def _revision(
    label: str, start: date, end: date | None, text: str
) -> tuple[SourceVersion, SourceSection]:
    version_url = f"{_DOCUMENT_URL}/{label}"
    version_id = uuid5(NAMESPACE_URL, version_url)
    citation_url = f"{version_url}#drill-records"
    version = SourceVersion(
        id=version_id,
        document_id=DOCUMENT.id,
        version=label,
        version_url=HttpUrl(version_url),
        retrieved_at=datetime(2026, 11, 21, tzinfo=UTC),
        original_sha256=sha256(text.encode("utf-8")).hexdigest(),
        effective_from=start,
        effective_until=end,
    )
    return version, SourceSection(
        id=uuid5(NAMESPACE_URL, citation_url),
        source_version_id=version_id,
        locator="Drill records",
        citation_url=HttpUrl(citation_url),
        text=text,
    )


_CHANGEOVER = date(2026, 6, 1)
_HEADER = "Drill notes 🧼\n\n"
REVISIONS = (
    _revision(
        "v1",
        date(2026, 1, 1),
        _CHANGEOVER,
        _HEADER + "File the café station checklist in the blue binder.",
    ),
    _revision(
        "v2",
        _CHANGEOVER,
        None,
        _HEADER + "File the café station checklist in the green binder.",
    ),
)
