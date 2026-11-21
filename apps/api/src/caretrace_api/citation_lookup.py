import re
from collections.abc import Iterable
from datetime import date
from typing import Annotated, Literal

from caretrace_contracts.common import Contract, Label, SourceUrl
from caretrace_contracts.sources import (
    CitationSpan,
    SourceDocument,
    SourceSection,
    SourceVersion,
)
from pydantic import Field


class CitedPassage(Contract):
    locator: Label
    citation_url: SourceUrl
    span: CitationSpan


class CitationMatch(Contract):
    status: Literal["matched"]
    corpus: Literal["synthetic_ipac"] = "synthetic_ipac"
    document: SourceDocument
    version: SourceVersion
    passages: Annotated[tuple[CitedPassage, ...], Field(min_length=1)]


class InsufficientEvidence(Contract):
    status: Literal["insufficient_evidence"]


type CitationLookup = Annotated[
    CitationMatch | InsufficientEvidence, Field(discriminator="status")
]


def resolve_version(
    versions: Iterable[SourceVersion], as_of: date
) -> SourceVersion | None:
    effective = []
    for version in versions:
        status = version.is_effective_on(as_of)
        if status is None:
            return None
        if status:
            effective.append(version)
    return effective[0] if len(effective) == 1 else None


def matching_spans(section: SourceSection, query: str) -> tuple[CitationSpan, ...]:
    keyword = query.strip().casefold()
    if not keyword:
        return ()
    return tuple(
        section.cite(passage.start(), passage.end())
        for passage in re.finditer(r"[^\n]+", section.text)
        if keyword in passage[0].casefold()
    )
