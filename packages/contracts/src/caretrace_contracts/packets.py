import json
from datetime import date
from hashlib import sha256
from typing import Annotated, Self
from uuid import UUID

from pydantic import AwareDatetime, Field, model_validator

from caretrace_contracts.assessment import ReviewRecord
from caretrace_contracts.common import Contract, Label, Sha256
from caretrace_contracts.review import EvidenceChecklistItem
from caretrace_contracts.sources import (
    SourceDocument,
    SourceKind,
    SourceSection,
    SourceVersion,
)


class PacketSource(Contract):
    document: SourceDocument
    version: SourceVersion
    sections: Annotated[tuple[SourceSection, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def validate_provenance(self) -> Self:
        if self.version.document_id != self.document.id or any(
            section.source_version_id != self.version.id for section in self.sections
        ):
            raise ValueError(
                "packet source sections must belong to the stated document version"
            )
        return self


class UnresolvedItem(Contract):
    id: UUID
    description: Label
    owner_id: UUID | None = None


class GenerationVersions(Contract):
    prompt_version: Label
    model_version: Label


class PacketContent(Contract):
    id: UUID
    tenant_id: UUID
    as_of: date
    created_at: AwareDatetime
    corpus_version: Label
    generation: GenerationVersions | None = None
    sources: Annotated[tuple[PacketSource, ...], Field(min_length=1)]
    checklist: Annotated[tuple[EvidenceChecklistItem, ...], Field(min_length=1)]
    unresolved_items: tuple[UnresolvedItem, ...] = ()

    @model_validator(mode="after")
    def validate_checklist(self) -> Self:
        sections: dict[UUID, SourceSection] = {}
        source_version_ids: set[UUID] = set()
        for source in self.sources:
            if source.version.id in source_version_ids:
                raise ValueError("packet source version IDs must be unique")
            if (
                source.document.kind is not SourceKind.INSPECTION_REPORT
                and source.version.is_effective_on(self.as_of) is not True
            ):
                raise ValueError(
                    "packet legislation must have a version applicable on the review date"
                )
            source_version_ids.add(source.version.id)
            for section in source.sections:
                if section.id in sections:
                    raise ValueError("packet section IDs must be unique")
                sections[section.id] = section

        if len({item.id for item in self.checklist}) != len(self.checklist):
            raise ValueError("checklist item IDs must be unique")
        if len({item.id for item in self.unresolved_items}) != len(
            self.unresolved_items
        ):
            raise ValueError("unresolved item IDs must be unique")
        for item in self.checklist:
            cited_section = sections.get(item.source.section_id)
            if item.tenant_id != self.tenant_id:
                raise ValueError("checklist items must belong to the packet tenant")
            if cited_section is None or not item.source.matches(cited_section):
                raise ValueError(
                    "each checklist rationale requires an exact packet citation"
                )
            if item.review is not None and item.review.reviewed_at > self.created_at:
                raise ValueError("checklist review cannot follow packet creation")
        return self

    def content_sha256(self) -> str:
        payload = json.dumps(
            self.model_dump(mode="json"),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return sha256(payload.encode("utf-8")).hexdigest()


class ExportApproval(Contract):
    id: UUID
    packet_sha256: Sha256
    review_protocol_version: Label
    review: ReviewRecord


class ApprovedPacket(Contract):
    content: PacketContent
    approval: ExportApproval

    @model_validator(mode="after")
    def validate_approval(self) -> Self:
        if self.approval.review.reviewed_at < self.content.created_at:
            raise ValueError("export approval cannot precede packet creation")
        if self.approval.packet_sha256 != self.content.content_sha256():
            raise ValueError("export approval must match the exact packet content")
        return self
