from uuid import UUID

from caretrace_contracts.assessment import (
    CoverageAssessment,
    ObligationCandidate,
    PolicyDocument,
    PolicyExcerpt,
)
from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    ForeignKey,
    ForeignKeyConstraint,
    String,
    Table,
    Text,
    UniqueConstraint,
    Uuid,
    insert,
    select,
)
from sqlalchemy.orm import Session

from caretrace_api.source_store import SourceStore
from caretrace_api.source_store import metadata as metadata

obligation_candidates = Table(
    "obligation_candidates",
    metadata,
    Column("id", Uuid(), primary_key=True),
    Column("citation_id", Uuid(), ForeignKey("citation_spans.id"), nullable=False),
    Column("payload", JSON(), nullable=False),
)
policy_versions = Table(
    "policy_versions",
    metadata,
    Column("tenant_id", Uuid(), primary_key=True),
    Column("id", Uuid(), primary_key=True),
    Column("document_id", Uuid(), nullable=False),
    Column("version", Text(), nullable=False),
    Column("original_sha256", String(64), nullable=False),
    Column("payload", JSON(), nullable=False),
    UniqueConstraint(
        "tenant_id",
        "document_id",
        "version",
        name="uq_policy_versions_document_version",
    ),
    UniqueConstraint(
        "tenant_id", "original_sha256", name="uq_policy_versions_checksum"
    ),
    CheckConstraint("length(original_sha256) = 64", name="checksum_length"),
)
policy_excerpts = Table(
    "policy_excerpts",
    metadata,
    Column("tenant_id", Uuid(), primary_key=True),
    Column("id", Uuid(), primary_key=True),
    Column("policy_version_id", Uuid(), nullable=False),
    Column("payload", JSON(), nullable=False),
    ForeignKeyConstraint(
        ["tenant_id", "policy_version_id"],
        ["policy_versions.tenant_id", "policy_versions.id"],
    ),
)
coverage_assessments = Table(
    "coverage_assessments",
    metadata,
    Column("tenant_id", Uuid(), primary_key=True),
    Column("id", Uuid(), primary_key=True),
    Column("policy_version_id", Uuid(), nullable=False),
    Column(
        "obligation_id", Uuid(), ForeignKey("obligation_candidates.id"), nullable=False
    ),
    Column("payload", JSON(), nullable=False),
    ForeignKeyConstraint(
        ["tenant_id", "policy_version_id"],
        ["policy_versions.tenant_id", "policy_versions.id"],
    ),
)


class ReviewStore:
    def __init__(self, session: Session, tenant_id: UUID) -> None:
        self.session = session
        self.tenant_id = tenant_id

    def _check_tenant(self, tenant_id: UUID) -> None:
        if tenant_id != self.tenant_id:
            raise ValueError("record is outside the repository tenant")

    def add_obligation(
        self, obligation: ObligationCandidate, citation_id: UUID
    ) -> None:
        obligation = ObligationCandidate.model_validate(obligation)
        stored_citation = SourceStore(self.session).get_citation(citation_id)
        if stored_citation is None or stored_citation != obligation.source:
            raise ValueError("obligation must refer to the exact stored citation")
        self.session.execute(
            insert(obligation_candidates).values(
                id=obligation.obligation_id,
                citation_id=citation_id,
                payload=obligation.model_dump(mode="json"),
            )
        )

    def get_obligation(self, obligation_id: UUID) -> ObligationCandidate | None:
        payload = self.session.execute(
            select(obligation_candidates.c.payload).where(
                obligation_candidates.c.id == obligation_id,
            )
        ).scalar_one_or_none()
        return (
            ObligationCandidate.model_validate(payload) if payload is not None else None
        )

    def add_policy(self, policy: PolicyDocument) -> None:
        policy = PolicyDocument.model_validate(policy)
        self._check_tenant(policy.tenant_id)
        self.session.execute(
            insert(policy_versions).values(
                tenant_id=self.tenant_id,
                id=policy.version_id,
                document_id=policy.document_id,
                version=policy.version,
                original_sha256=policy.original_sha256,
                payload=policy.model_dump(mode="json"),
            )
        )

    def get_policy(self, version_id: UUID) -> PolicyDocument | None:
        payload = self.session.execute(
            select(policy_versions.c.payload).where(
                policy_versions.c.tenant_id == self.tenant_id,
                policy_versions.c.id == version_id,
            )
        ).scalar_one_or_none()
        return PolicyDocument.model_validate(payload) if payload is not None else None

    def add_excerpt(self, excerpt: PolicyExcerpt, parsed_text: str) -> None:
        excerpt = PolicyExcerpt.model_validate(excerpt)
        self._check_tenant(excerpt.tenant_id)
        policy = self.get_policy(excerpt.policy_version_id)
        if policy is None or not excerpt.matches(policy, parsed_text):
            raise ValueError(
                "excerpt must match the tenant policy version and exact parsed text"
            )
        self.session.execute(
            insert(policy_excerpts).values(
                tenant_id=self.tenant_id,
                id=excerpt.id,
                policy_version_id=excerpt.policy_version_id,
                payload=excerpt.model_dump(mode="json"),
            )
        )

    def get_excerpt(self, excerpt_id: UUID) -> PolicyExcerpt | None:
        payload = self.session.execute(
            select(policy_excerpts.c.payload).where(
                policy_excerpts.c.tenant_id == self.tenant_id,
                policy_excerpts.c.id == excerpt_id,
            )
        ).scalar_one_or_none()
        return PolicyExcerpt.model_validate(payload) if payload is not None else None

    def add_assessment(self, assessment: CoverageAssessment) -> None:
        assessment = CoverageAssessment.model_validate(assessment)
        self._check_tenant(assessment.tenant_id)
        rows = self.session.execute(
            select(policy_excerpts.c.payload).where(
                policy_excerpts.c.tenant_id == self.tenant_id,
                policy_excerpts.c.policy_version_id == assessment.policy_version_id,
                policy_excerpts.c.id.in_(assessment.searched_excerpt_ids),
            )
        ).scalars()
        searched = {
            excerpt.id: excerpt for excerpt in map(PolicyExcerpt.model_validate, rows)
        }
        if searched.keys() != set(assessment.searched_excerpt_ids) or any(
            searched.get(passage.id) != passage
            for passage in assessment.supporting_passages
        ):
            raise ValueError(
                "assessment evidence must match stored tenant policy excerpts"
            )
        self.session.execute(
            insert(coverage_assessments).values(
                tenant_id=self.tenant_id,
                id=assessment.id,
                policy_version_id=assessment.policy_version_id,
                obligation_id=assessment.obligation_id,
                payload=assessment.model_dump(mode="json"),
            )
        )

    def get_assessment(self, assessment_id: UUID) -> CoverageAssessment | None:
        payload = self.session.execute(
            select(coverage_assessments.c.payload).where(
                coverage_assessments.c.tenant_id == self.tenant_id,
                coverage_assessments.c.id == assessment_id,
            )
        ).scalar_one_or_none()
        return (
            CoverageAssessment.model_validate(payload) if payload is not None else None
        )
