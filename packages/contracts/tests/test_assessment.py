from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

import pytest
from caretrace_contracts.assessment import (
    CoverageAssessment,
    CoverageLabel,
    ObligationCandidate,
    ObligationReviewStatus,
    PolicyAttestation,
    PolicyClassification,
    PolicyDocument,
    PolicyExcerpt,
    ReviewRecord,
)
from caretrace_contracts.sources import CitationSpan
from pydantic import ValidationError

NOW = datetime(2026, 11, 20, 15, tzinfo=UTC)


def test_obligation_review_requires_actor_timestamp_and_reason() -> None:
    candidate = ObligationCandidate(
        obligation_id=uuid4(),
        source=CitationSpan(
            source_version_id=uuid4(), section_id=uuid4(), start=5, end=9, quote="test"
        ),
        actor="Example reviewer",
        action="Check the synthetic record",
    )
    assert candidate.review_status is ObligationReviewStatus.PROVISIONAL
    reviewed = candidate.model_dump() | {
        "review_status": ObligationReviewStatus.REVIEWED
    }
    with pytest.raises(ValidationError, match="reviewer record"):
        ObligationCandidate.model_validate(reviewed)
    review = ReviewRecord(
        reviewer_id=uuid4(), reviewed_at=NOW, reason="Checked the sample"
    )
    approved = ObligationCandidate.model_validate(reviewed | {"review": review})
    assert (
        ObligationCandidate.model_validate_json(approved.model_dump_json()) == approved
    )


@pytest.fixture
def policy() -> PolicyDocument:
    return PolicyDocument(
        tenant_id=uuid4(),
        version_id=uuid4(),
        document_id=uuid4(),
        title="Synthetic document",
        version="v1",
        classification=PolicyClassification.SYNTHETIC,
        registered_at=NOW,
        original_sha256="b" * 64,
    )


def test_policy_authorization_requires_de_identification_and_timely_attestation(
    policy: PolicyDocument,
) -> None:
    authorized = policy.model_dump() | {
        "classification": PolicyClassification.AUTHORIZED_DE_IDENTIFIED
    }
    with pytest.raises(ValidationError, match="attestation"):
        PolicyDocument.model_validate(authorized)

    attestation = PolicyAttestation(
        attested_by=uuid4(),
        attested_at=NOW,
        authorization_reference="Synthetic approval reference",
        de_identification_confirmed=True,
    )
    assert (
        PolicyDocument.model_validate(
            authorized | {"attestation": attestation}
        ).attestation
        == attestation
    )
    late = attestation.model_copy(update={"attested_at": NOW + timedelta(seconds=1)})
    with pytest.raises(ValidationError, match="prior or concurrent"):
        PolicyDocument.model_validate(authorized | {"attestation": late})
    with pytest.raises(ValidationError, match="de-identification must be confirmed"):
        PolicyAttestation.model_validate(
            attestation.model_dump() | {"de_identification_confirmed": False}
        )


@pytest.fixture
def assessment(policy: PolicyDocument) -> CoverageAssessment:
    return CoverageAssessment(
        id=uuid4(),
        tenant_id=policy.tenant_id,
        obligation_id=uuid4(),
        policy_version_id=policy.version_id,
        as_of=date(2026, 11, 20),
        assessed_at=NOW,
        label=CoverageLabel.NEEDS_REVIEW,
    )


@pytest.mark.parametrize(
    "label", [CoverageLabel.ADDRESSED, CoverageLabel.PARTIAL, CoverageLabel.NO_SUPPORT]
)
def test_requires_evidence_for_non_abstaining_labels(
    assessment: CoverageAssessment, label: CoverageLabel
) -> None:
    with pytest.raises(ValidationError, match="coverage requires|documented search"):
        CoverageAssessment.model_validate(assessment.model_dump() | {"label": label})


def test_coverage_rejects_cross_tenant_and_cross_version_passages(
    policy: PolicyDocument, assessment: CoverageAssessment
) -> None:
    passage = PolicyExcerpt(
        id=uuid4(),
        tenant_id=policy.tenant_id,
        policy_version_id=policy.version_id,
        quote="Synthetic",
        start=0,
        end=9,
    )
    assert passage.matches(policy, "Synthetic text")
    addressed = assessment.model_dump() | {
        "label": CoverageLabel.ADDRESSED,
        "searched_excerpt_ids": (passage.id,),
        "supporting_passages": (passage,),
    }
    assert CoverageAssessment.model_validate(addressed).supporting_passages == (
        passage,
    )
    for field in ("tenant_id", "policy_version_id"):
        foreign = passage.model_dump() | {field: uuid4()}
        with pytest.raises(ValidationError, match="same tenant and policy version"):
            CoverageAssessment.model_validate(
                addressed | {"supporting_passages": (foreign,)}
            )

    with pytest.raises(ValidationError, match="searched in the same tenant"):
        CoverageAssessment.model_validate(addressed | {"searched_excerpt_ids": ()})


def test_no_support_records_searched_text_without_a_match(
    assessment: CoverageAssessment,
) -> None:
    reviewed = CoverageAssessment.model_validate(
        assessment.model_dump()
        | {"label": CoverageLabel.NO_SUPPORT, "searched_excerpt_ids": (uuid4(),)}
    )
    assert (
        CoverageAssessment.model_validate_json(reviewed.model_dump_json()) == reviewed
    )
    with pytest.raises(ValidationError, match="label"):
        CoverageAssessment.model_validate(
            assessment.model_dump() | {"label": "compliant"}
        )
