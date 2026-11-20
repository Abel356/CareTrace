from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

import pytest
from caretrace_contracts.assessment import (
    CoverageAssessment,
    CoverageLabel,
    ReviewRecord,
)
from caretrace_contracts.packets import (
    ApprovedPacket,
    ExportApproval,
    PacketContent,
    PacketSource,
)
from caretrace_contracts.review import (
    AuditAction,
    AuditEvent,
    EvidenceChecklistItem,
    EvidenceState,
    ReviewerOverride,
)
from caretrace_contracts.sources import (
    Jurisdiction,
    SourceDocument,
    SourceKind,
    SourceSection,
    SourceVersion,
)
from pydantic import HttpUrl, ValidationError

NOW = datetime(2026, 11, 20, tzinfo=UTC)


@pytest.fixture
def packet() -> PacketContent:
    url = HttpUrl("https://sources.example.test/synthetic")
    document = SourceDocument(
        id=uuid4(),
        title="Synthetic fixture",
        jurisdiction=Jurisdiction.ONTARIO,
        kind=SourceKind.REGULATION,
        source_url=url,
    )
    version = SourceVersion(
        id=uuid4(),
        document_id=document.id,
        version="sample-1",
        version_url=url,
        retrieved_at=NOW,
        original_sha256="b" * 64,
        effective_from=date(2026, 11, 1),
    )
    section = SourceSection(
        id=uuid4(),
        source_version_id=version.id,
        locator="Example section 1",
        citation_url=url,
        text="Fictional record for the demonstration",
    )
    tenant_id = uuid4()
    return PacketContent(
        id=uuid4(),
        tenant_id=tenant_id,
        as_of=NOW.date(),
        created_at=NOW,
        corpus_version="sample-1",
        sources=(
            PacketSource(document=document, version=version, sections=(section,)),
        ),
        checklist=(
            EvidenceChecklistItem(
                id=uuid4(),
                tenant_id=tenant_id,
                description="Find the sample record",
                rationale="The fixture provides a demonstration record",
                source=section.cite(0, 16),
            ),
        ),
    )


@pytest.fixture
def reviewer() -> ReviewRecord:
    return ReviewRecord(
        reviewer_id=uuid4(), reviewed_at=NOW, reason="Reviewed the synthetic packet"
    )


def test_approval_is_bound_to_exact_packet_and_serializes(
    packet: PacketContent, reviewer: ReviewRecord
) -> None:
    approval = ExportApproval(
        id=uuid4(),
        packet_sha256=packet.content_sha256(),
        review_protocol_version="1",
        review=reviewer,
    )
    approved = ApprovedPacket(content=packet, approval=approval)
    assert ApprovedPacket.model_validate_json(approved.model_dump_json()) == approved
    changed = PacketContent.model_validate(
        packet.model_dump() | {"corpus_version": "sample-2"}
    )
    with pytest.raises(ValidationError, match="exact packet content"):
        ApprovedPacket(content=changed, approval=approval)
    early = reviewer.model_copy(update={"reviewed_at": NOW - timedelta(seconds=1)})
    with pytest.raises(ValidationError, match="cannot precede"):
        ApprovedPacket(
            content=packet, approval=approval.model_copy(update={"review": early})
        )


def test_packet_requires_temporally_applicable_exact_citations(
    packet: PacketContent,
) -> None:
    with pytest.raises(ValidationError, match="applicable on the review date"):
        PacketContent.model_validate(
            packet.model_dump() | {"as_of": date(2026, 10, 31)}
        )
    item = packet.checklist[0]
    incorrect = item.source.model_copy(update={"quote": "Fictional report"})
    with pytest.raises(ValidationError, match="exact packet citation"):
        PacketContent.model_validate(
            packet.model_dump()
            | {"checklist": (item.model_copy(update={"source": incorrect}),)}
        )
    with pytest.raises(ValidationError, match="packet tenant"):
        PacketContent.model_validate(
            packet.model_dump()
            | {"checklist": (item.model_copy(update={"tenant_id": uuid4()}),)}
        )


def test_reviewed_checklist_items_require_an_owner_and_review(
    packet: PacketContent, reviewer: ReviewRecord
) -> None:
    item = packet.checklist[0].model_dump() | {"state": EvidenceState.REVIEWED}
    with pytest.raises(ValidationError, match="require an owner"):
        EvidenceChecklistItem.model_validate(item)
    owned = item | {"owner_id": uuid4()}
    with pytest.raises(ValidationError, match="review details"):
        EvidenceChecklistItem.model_validate(owned)
    assert (
        EvidenceChecklistItem.model_validate(owned | {"review": reviewer}).review
        == reviewer
    )


def test_override_preserves_assessment_scope(reviewer: ReviewRecord) -> None:
    original = CoverageAssessment(
        id=uuid4(),
        tenant_id=uuid4(),
        obligation_id=uuid4(),
        policy_version_id=uuid4(),
        as_of=NOW.date(),
        assessed_at=NOW,
        label=CoverageLabel.NEEDS_REVIEW,
    )
    revised = CoverageAssessment.model_validate(
        original.model_dump()
        | {
            "id": uuid4(),
            "label": CoverageLabel.NO_SUPPORT,
            "searched_excerpt_ids": (uuid4(),),
        }
    )
    decision = ReviewerOverride(original=original, revised=revised, review=reviewer)
    assert decision.original == original
    with pytest.raises(ValidationError, match="retain the assessment scope"):
        ReviewerOverride(
            original=original,
            revised=revised.model_copy(update={"tenant_id": uuid4()}),
            review=reviewer,
        )


def test_human_audit_event_requires_a_recorded_actor() -> None:
    with pytest.raises(ValidationError, match="require an actor"):
        AuditEvent(
            id=uuid4(),
            tenant_id=uuid4(),
            sequence=1,
            action=AuditAction.EXPORT_APPROVED,
            subject_id=uuid4(),
            occurred_at=NOW,
        )
