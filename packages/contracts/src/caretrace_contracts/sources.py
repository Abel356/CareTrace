from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Self
from uuid import UUID

from pydantic import AwareDatetime, field_validator, model_validator

from caretrace_contracts.common import Contract, Label, Sha256, SourceUrl, TextSpan


class Jurisdiction(StrEnum):
    ONTARIO = "CA-ON"


class SourceKind(StrEnum):
    STATUTE = "statute"
    REGULATION = "regulation"
    INSPECTION_REPORT = "inspection_report"


class SourceDocument(Contract):
    id: UUID
    title: Label
    jurisdiction: Jurisdiction
    kind: SourceKind
    source_url: SourceUrl


class SourceVersion(Contract):
    id: UUID
    document_id: UUID
    version: Label
    version_url: SourceUrl
    retrieved_at: AwareDatetime
    original_sha256: Sha256
    effective_from: date | None = None
    effective_until: date | None = None

    @model_validator(mode="after")
    def validate_effective_interval(self) -> Self:
        if self.effective_until is not None and (
            self.effective_from is None or self.effective_until <= self.effective_from
        ):
            raise ValueError(
                "exclusive effective_until must follow a known effective_from"
            )
        return self

    def is_effective_on(self, as_of: date) -> bool | None:
        if self.effective_from is None:
            return None
        return self.effective_from <= as_of and (
            self.effective_until is None or as_of < self.effective_until
        )


class CitationSpan(TextSpan):
    source_version_id: UUID
    section_id: UUID

    def matches(self, section: SourceSection) -> bool:
        return (
            self.source_version_id == section.source_version_id
            and self.section_id == section.id
            and self.matches_text(section.text)
        )


class SourceSection(Contract):
    id: UUID
    source_version_id: UUID
    locator: Label
    citation_url: SourceUrl
    text: str

    @field_validator("text")
    @classmethod
    def validate_text(cls, text: str) -> str:
        if not text.strip():
            raise ValueError("section text must contain a non-whitespace character")
        return text

    def cite(self, start: int, end: int) -> CitationSpan:
        if not 0 <= start < end <= len(self.text):
            raise ValueError("citation range is outside the section text")
        return CitationSpan(
            source_version_id=self.source_version_id,
            section_id=self.id,
            start=start,
            end=end,
            quote=self.text[start:end],
        )
