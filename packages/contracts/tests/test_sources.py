from datetime import UTC, date, datetime
from uuid import uuid4

import pytest
from caretrace_contracts.sources import (
    CitationSpan,
    Jurisdiction,
    SourceDocument,
    SourceKind,
    SourceSection,
    SourceVersion,
)
from pydantic import HttpUrl, ValidationError


@pytest.fixture
def section() -> SourceSection:
    return SourceSection(
        id=uuid4(),
        source_version_id=uuid4(),
        locator="Example § 2",
        citation_url=HttpUrl("https://sources.example.test/example#section-2"),
        text="  A 🧪 sample.\nRetain exact characters.  ",
    )


def test_source_document_round_trip_and_immutability() -> None:
    document = SourceDocument(
        id=uuid4(),
        title="Synthetic source",
        jurisdiction=Jurisdiction.ONTARIO,
        kind=SourceKind.STATUTE,
        source_url=HttpUrl("https://sources.example.test/example"),
    )
    assert SourceDocument.model_validate_json(document.model_dump_json()) == document
    with pytest.raises(ValidationError, match="frozen"):
        document.title = "Changed title"


@pytest.mark.parametrize(
    "url", ["http://sources.example.test", "https://user@sources.example.test"]
)
def test_source_url_requires_https_without_credentials(url: str) -> None:
    with pytest.raises(ValidationError, match="HTTPS without credentials"):
        SourceDocument(
            id=uuid4(),
            title="Synthetic source",
            jurisdiction=Jurisdiction.ONTARIO,
            kind=SourceKind.REGULATION,
            source_url=HttpUrl(url),
        )


def test_effective_interval_distinguishes_unknown_from_outside_range() -> None:
    unknown = SourceVersion(
        id=uuid4(),
        document_id=uuid4(),
        version="synthetic-v1",
        version_url=HttpUrl("https://sources.example.test/example/v1"),
        retrieved_at=datetime(2026, 11, 20, tzinfo=UTC),
        original_sha256="a" * 64,
    )
    assert unknown.is_effective_on(date(2026, 11, 20)) is None
    known = SourceVersion.model_validate(
        unknown.model_dump()
        | {"effective_from": date(2026, 9, 1), "effective_until": date(2026, 10, 1)}
    )
    assert known.is_effective_on(date(2026, 9, 1)) is True
    assert known.is_effective_on(date(2026, 10, 1)) is False
    assert known.is_effective_on(date(2026, 8, 31)) is False

    with pytest.raises(ValidationError, match="exclusive effective_until"):
        SourceVersion.model_validate(
            known.model_dump() | {"effective_from": date(2026, 10, 1)}
        )
    with pytest.raises(ValidationError, match="timezone"):
        SourceVersion.model_validate(
            known.model_dump() | {"retrieved_at": datetime(2026, 11, 20)}
        )
    with pytest.raises(ValidationError, match="original_sha256"):
        SourceVersion.model_validate(known.model_dump() | {"original_sha256": "g" * 64})


def test_citation_round_trip_preserves_exact_unicode_and_whitespace(
    section: SourceSection,
) -> None:
    citation = section.cite(2, 6)
    assert citation.quote == "A 🧪 "
    assert citation.matches(section)
    assert CitationSpan.model_validate_json(citation.model_dump_json()) == citation
    updated = SourceSection.model_validate(
        section.model_dump() | {"source_version_id": uuid4()}
    )
    assert not citation.matches(updated)
    altered = CitationSpan.model_validate(citation.model_dump() | {"quote": "A 🧪!"})
    assert not altered.matches(section)


@pytest.mark.parametrize("start,end", [(-1, 2), (3, 3), (0, 200), (0, 2)])
def test_rejects_invalid_or_blank_citation_ranges(
    section: SourceSection, start: int, end: int
) -> None:
    with pytest.raises(ValueError):
        section.cite(start, end)
