from datetime import date
from enum import StrEnum
from typing import Annotated, Self
from uuid import UUID

from pydantic import AwareDatetime, Field, model_validator

from caretrace_contracts.common import Contract, Label, Sha256, TextSpan
from caretrace_contracts.sources import CitationSpan


class ReviewRecord(Contract):
    reviewer_id: UUID
    reviewed_at: AwareDatetime
    reason: Label


class ObligationReviewStatus(StrEnum):
    PROVISIONAL = "provisional"
    REVIEWED = "reviewed"
    REJECTED = "rejected"


class ObligationCandidate(Contract):
    obligation_id: UUID
    source: CitationSpan
    actor: Label
    action: Label
    condition: Label | None = None
    frequency: Label | None = None
    effective_date: date | None = None
    review_status: ObligationReviewStatus = ObligationReviewStatus.PROVISIONAL
    review: ReviewRecord | None = None

    @model_validator(mode="after")
    def validate_review(self) -> Self:
        if (self.review is None) != (
            self.review_status is ObligationReviewStatus.PROVISIONAL
        ):
            raise ValueError(
                "reviewed or rejected obligations require a reviewer record"
            )
        return self


class PolicyClassification(StrEnum):
    SYNTHETIC = "synthetic"
    AUTHORIZED_DE_IDENTIFIED = "authorized_de_identified"


class PolicyAttestation(Contract):
    attested_by: UUID
    attested_at: AwareDatetime
    authorization_reference: Label
    de_identification_confirmed: Annotated[bool, Field(strict=True)]

    @model_validator(mode="after")
    def validate_confirmation(self) -> Self:
        if not self.de_identification_confirmed:
            raise ValueError("de-identification must be confirmed")
        return self


class PolicyDocument(Contract):
    tenant_id: UUID
    version_id: UUID
    document_id: UUID
    title: Label
    version: Label
    classification: PolicyClassification
    registered_at: AwareDatetime
    original_sha256: Sha256
    attestation: PolicyAttestation | None = None

    @model_validator(mode="after")
    def validate_attestation(self) -> Self:
        if self.classification is PolicyClassification.AUTHORIZED_DE_IDENTIFIED:
            if (
                self.attestation is None
                or self.attestation.attested_at > self.registered_at
            ):
                raise ValueError(
                    "authorized policies require a prior or concurrent attestation"
                )
        elif self.attestation is not None:
            raise ValueError("synthetic policies do not use authorization attestations")
        return self


class PolicyExcerpt(TextSpan):
    id: UUID
    tenant_id: UUID
    policy_version_id: UUID

    def matches(self, document: PolicyDocument, text: str) -> bool:
        return (
            self.tenant_id == document.tenant_id
            and self.policy_version_id == document.version_id
            and self.matches_text(text)
        )


class CoverageLabel(StrEnum):
    ADDRESSED = "addressed in document"
    PARTIAL = "partially addressed"
    NO_SUPPORT = "no supporting passage found"
    NEEDS_REVIEW = "needs review"


class CoverageAssessment(Contract):
    id: UUID
    tenant_id: UUID
    obligation_id: UUID
    policy_version_id: UUID
    as_of: date
    assessed_at: AwareDatetime
    label: CoverageLabel
    searched_excerpt_ids: tuple[UUID, ...] = ()
    supporting_passages: tuple[PolicyExcerpt, ...] = ()

    @model_validator(mode="after")
    def validate_evidence(self) -> Self:
        searched = set(self.searched_excerpt_ids)
        if len(searched) != len(self.searched_excerpt_ids):
            raise ValueError("searched excerpt IDs must be unique")
        supporting_ids = {passage.id for passage in self.supporting_passages}
        if len(supporting_ids) != len(self.supporting_passages):
            raise ValueError("supporting passage IDs must be unique")
        if not supporting_ids <= searched or any(
            passage.tenant_id != self.tenant_id
            or passage.policy_version_id != self.policy_version_id
            for passage in self.supporting_passages
        ):
            raise ValueError(
                "supporting passages must be searched in the same tenant and policy version"
            )
        if (
            self.label in {CoverageLabel.ADDRESSED, CoverageLabel.PARTIAL}
            and not supporting_ids
        ):
            raise ValueError("positive coverage requires a supporting passage")
        if self.label is CoverageLabel.NO_SUPPORT and (not searched or supporting_ids):
            raise ValueError(
                "no supporting passage requires a documented search without matches"
            )
        return self
