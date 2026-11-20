from enum import StrEnum
from typing import Annotated, Self
from uuid import UUID

from pydantic import AwareDatetime, Field, model_validator

from caretrace_contracts.assessment import CoverageAssessment, ReviewRecord
from caretrace_contracts.common import Contract, Label
from caretrace_contracts.sources import CitationSpan


class ReviewerOverride(Contract):
    original: CoverageAssessment
    revised: CoverageAssessment
    review: ReviewRecord

    @model_validator(mode="after")
    def validate_revision(self) -> Self:
        original = self.original
        revised = self.revised
        if (
            original.tenant_id != revised.tenant_id
            or original.policy_version_id != revised.policy_version_id
            or original.obligation_id != revised.obligation_id
            or original.as_of != revised.as_of
        ):
            raise ValueError("an override must retain the assessment scope")
        if original.id == revised.id or original.label == revised.label:
            raise ValueError(
                "an override requires a new assessment ID and a changed label"
            )
        if not original.assessed_at <= revised.assessed_at <= self.review.reviewed_at:
            raise ValueError(
                "revised assessment and review must follow the original assessment"
            )
        return self


class EvidenceState(StrEnum):
    NEEDED = "needed"
    IN_PROGRESS = "in_progress"
    READY_FOR_REVIEW = "ready_for_review"
    REVIEWED = "reviewed"


class EvidenceChecklistItem(Contract):
    id: UUID
    tenant_id: UUID
    description: Label
    rationale: Label
    source: CitationSpan
    owner_id: UUID | None = None
    state: EvidenceState = EvidenceState.NEEDED
    review: ReviewRecord | None = None

    @model_validator(mode="after")
    def validate_state(self) -> Self:
        if self.state is not EvidenceState.NEEDED and self.owner_id is None:
            raise ValueError("active checklist items require an owner")
        if (self.review is not None) != (self.state is EvidenceState.REVIEWED):
            raise ValueError(
                "checklist review details must correspond to the reviewed state"
            )
        return self


class AuditAction(StrEnum):
    ASSESSMENT_DRAFTED = "assessment_drafted"
    COVERAGE_OVERRIDDEN = "coverage_overridden"
    EVIDENCE_REVIEWED = "evidence_reviewed"
    EXPORT_APPROVED = "export_approved"


class AuditEvent(Contract):
    id: UUID
    tenant_id: UUID
    sequence: Annotated[int, Field(strict=True, gt=0)]
    action: AuditAction
    subject_id: UUID
    occurred_at: AwareDatetime
    actor_id: UUID | None = None

    @model_validator(mode="after")
    def validate_actor(self) -> Self:
        if self.action is not AuditAction.ASSESSMENT_DRAFTED and self.actor_id is None:
            raise ValueError("human review events require an actor")
        return self
