from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from caretrace_api.database import Database
from caretrace_api.review_store import ReviewStore, policy_excerpts, policy_versions
from caretrace_api.source_store import SourceStore
from caretrace_contracts.assessment import (
    CoverageAssessment,
    CoverageLabel,
    ObligationCandidate,
    PolicyClassification,
    PolicyDocument,
    PolicyExcerpt,
)
from caretrace_contracts.sources import (
    Jurisdiction,
    SourceDocument,
    SourceKind,
    SourceSection,
    SourceVersion,
)
from pydantic import HttpUrl
from sqlalchemy import insert, update
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
