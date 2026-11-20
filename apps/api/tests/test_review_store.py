from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from caretrace_api.database import Database
from caretrace_api.review_store import ReviewStore, policy_excerpts, policy_versions
from caretrace_api.source_store import SourceStore, citation_spans
from caretrace_api.workflow_store import WorkflowStore, audit_events
from caretrace_contracts.assessment import (
    CoverageAssessment,
    CoverageLabel,
    ObligationCandidate,
    PolicyClassification,
    PolicyDocument,
    PolicyExcerpt,
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
    EvidenceChecklistItem,
    ReviewerOverride,
)
from caretrace_contracts.sources import (
    Jurisdiction,
    SourceDocument,
    SourceKind,
    SourceSection,
    SourceVersion,
)
from pydantic import HttpUrl
from sqlalchemy import delete, insert, select, update
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError

NOW = datetime(2026, 11, 20, tzinfo=UTC)


@pytest.fixture
def database() -> Iterator[Database]:
    database = Database(make_url("sqlite+pysqlite:///:memory:"))
    config = Config(Path(__file__).resolve().parents[3] / "infra" / "alembic.ini")
    try:
        with database.engine.begin() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
        yield database
    finally:
        database.dispose()


@pytest.fixture
def policy() -> PolicyDocument:
    return PolicyDocument(
        tenant_id=uuid4(),
        version_id=uuid4(),
        document_id=uuid4(),
        title="Synthetic policy",
        version="1",
        classification=PolicyClassification.SYNTHETIC,
        registered_at=NOW,
        original_sha256="a" * 64,
    )


@pytest.fixture
def obligation(database: Database, policy: PolicyDocument) -> ObligationCandidate:
    url = HttpUrl("https://sources.example.test/example")
    document = SourceDocument(
        id=uuid4(),
        title="Synthetic source",
        jurisdiction=Jurisdiction.ONTARIO,
        kind=SourceKind.REGULATION,
        source_url=url,
    )
    version = SourceVersion(
        id=uuid4(),
        document_id=document.id,
        version="1",
        version_url=url,
        retrieved_at=NOW,
        original_sha256="b" * 64,
        effective_from=NOW.date(),
    )
    section = SourceSection(
        id=uuid4(),
        source_version_id=version.id,
        locator="Example 1",
        citation_url=url,
        text="Fictional text",
    )
    citation = section.cite(0, 9)
    candidate = ObligationCandidate(
        obligation_id=uuid4(), source=citation, actor="Reviewer", action="Check fixture"
    )
    with database.session() as session:
        sources = SourceStore(session)
        sources.add_document(document)
        sources.add_version(version)
        sources.add_section(section)
        citation_id = uuid4()
        sources.add_citation(citation_id, citation)
        ReviewStore(session, policy.tenant_id).add_obligation(candidate, citation_id)
    return candidate


def test_persists_coverage_with_exact_tenant_evidence(
    database: Database,
    policy: PolicyDocument,
    obligation: ObligationCandidate,
) -> None:
    excerpt = PolicyExcerpt(
        id=uuid4(),
        tenant_id=policy.tenant_id,
        policy_version_id=policy.version_id,
        start=0,
        end=9,
        quote="Synthetic",
    )
    assessment = CoverageAssessment(
        id=uuid4(),
        tenant_id=policy.tenant_id,
        policy_version_id=policy.version_id,
        obligation_id=obligation.obligation_id,
        as_of=NOW.date(),
        assessed_at=NOW,
        label=CoverageLabel.ADDRESSED,
        searched_excerpt_ids=(excerpt.id,),
        supporting_passages=(excerpt,),
    )
    with database.session() as session:
        store = ReviewStore(session, policy.tenant_id)
        store.add_policy(policy)
        with pytest.raises(ValueError, match="assessment evidence"):
            store.add_assessment(assessment)
        with pytest.raises(ValueError, match="exact parsed text"):
            store.add_excerpt(excerpt, "Different text")
        store.add_excerpt(excerpt, "Synthetic policy")
        store.add_assessment(assessment)

    with database.session() as session:
        store = ReviewStore(session, policy.tenant_id)
        assert store.get_policy(policy.version_id) == policy
        assert store.get_obligation(obligation.obligation_id) == obligation
        assert store.get_excerpt(excerpt.id) == excerpt
        assert store.get_assessment(assessment.id) == assessment
        different = ReviewStore(session, uuid4())
        assert different.get_policy(policy.version_id) is None
        assert different.get_excerpt(excerpt.id) is None
        assert different.get_assessment(assessment.id) is None
        with pytest.raises(ValueError, match="outside the repository tenant"):
            different.add_policy(policy)


def test_database_rejects_foreign_policy_references_and_mutations(
    database: Database, policy: PolicyDocument
) -> None:
    with database.session() as session:
        ReviewStore(session, policy.tenant_id).add_policy(policy)
    with pytest.raises(IntegrityError), database.session() as session:
        session.execute(
            insert(policy_excerpts).values(
                tenant_id=uuid4(),
                id=uuid4(),
                policy_version_id=policy.version_id,
                payload={},
            )
        )
    with (
        pytest.raises(IntegrityError, match="immutable"),
        database.session() as session,
    ):
        session.execute(update(policy_versions).values(original_sha256="b" * 64))
    with pytest.raises(IntegrityError), database.session() as session:
        duplicate = policy.model_copy(
            update={"document_id": uuid4(), "version_id": uuid4()}
        )
        ReviewStore(session, policy.tenant_id).add_policy(duplicate)


def test_review_and_approval_keep_an_ordered_append_only_audit(
    database: Database,
    policy: PolicyDocument,
    obligation: ObligationCandidate,
) -> None:
    reviewer = ReviewRecord(
        reviewer_id=uuid4(), reviewed_at=NOW, reason="Fixture review"
    )
    original = CoverageAssessment(
        id=uuid4(),
        tenant_id=policy.tenant_id,
        policy_version_id=policy.version_id,
        obligation_id=obligation.obligation_id,
        as_of=NOW.date(),
        assessed_at=NOW,
        label=CoverageLabel.NEEDS_REVIEW,
    )
    excerpt = PolicyExcerpt(
        id=uuid4(),
        tenant_id=policy.tenant_id,
        policy_version_id=policy.version_id,
        start=0,
        end=9,
        quote="Synthetic",
    )
    revised = CoverageAssessment.model_validate(
        original.model_dump()
        | {
            "id": uuid4(),
            "label": CoverageLabel.NO_SUPPORT,
            "searched_excerpt_ids": (excerpt.id,),
        }
    )
    override = ReviewerOverride(original=original, revised=revised, review=reviewer)
    event_id = uuid4()
    with database.session() as session:
        store = WorkflowStore(session, policy.tenant_id)
        store.add_policy(policy)
        store.add_excerpt(excerpt, "Synthetic text")
        store.add_assessment(original)
        assert store.record_override(override, event_id).sequence == 1
        assert store.get_override(original.id) == override

        sources = SourceStore(session)
        version = sources.get_version(obligation.source.source_version_id)
        section = sources.get_section(obligation.source.section_id)
        assert version is not None and section is not None
        document = sources.get_document(version.document_id)
        assert document is not None
        item = EvidenceChecklistItem(
            id=uuid4(),
            tenant_id=policy.tenant_id,
            description="Collect synthetic fixture",
            rationale="Document the synthetic example",
            source=obligation.source,
        )
        content = PacketContent(
            id=uuid4(),
            tenant_id=policy.tenant_id,
            as_of=NOW.date(),
            created_at=NOW,
            corpus_version="sample-1",
            sources=(
                PacketSource(document=document, version=version, sections=(section,)),
            ),
            checklist=(item,),
        )
        packet = ApprovedPacket(
            content=content,
            approval=ExportApproval(
                id=uuid4(),
                packet_sha256=content.content_sha256(),
                review_protocol_version="1",
                review=reviewer,
            ),
        )
        with pytest.raises(ValueError, match="stored checklist items"):
            store.record_approval(packet, uuid4())
        citation_id = session.execute(select(citation_spans.c.id)).scalar_one()
        store.add_checklist_item(item, citation_id)
        with pytest.raises(IntegrityError):
            store.record_approval(packet, event_id)
        assert store.get_approval(content.id) is None

    with pytest.raises(RuntimeError, match="rollback"), database.session() as session:
        store = WorkflowStore(session, policy.tenant_id)
        assert store.record_approval(packet, uuid4()).sequence == 2
        raise RuntimeError("rollback")
    with database.session() as session:
        store = WorkflowStore(session, policy.tenant_id)
        assert store.get_approval(content.id) is None
        assert store.record_approval(packet, uuid4()).sequence == 2
        assert store.get_approval(content.id) == packet
        assert [event.action for event in store.list_events()] == [
            AuditAction.COVERAGE_OVERRIDDEN,
            AuditAction.EXPORT_APPROVED,
        ]
        other = WorkflowStore(session, uuid4())
        assert other.get_approval(content.id) is None
        assert other.list_events() == ()

    with (
        pytest.raises(IntegrityError, match="append-only"),
        database.session() as session,
    ):
        session.execute(delete(audit_events))
