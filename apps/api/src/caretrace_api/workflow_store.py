from datetime import datetime
from uuid import UUID

from caretrace_contracts.packets import ApprovedPacket
from caretrace_contracts.review import (
    AuditAction,
    AuditEvent,
    EvidenceChecklistItem,
    ReviewerOverride,
)
from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    Table,
    UniqueConstraint,
    Uuid,
    insert,
    select,
)
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from caretrace_api.review_store import ReviewStore
from caretrace_api.review_store import metadata as metadata
from caretrace_api.source_store import SourceStore, UtcTimestamp

checklist_items = Table(
    "checklist_items",
    metadata,
    Column("tenant_id", Uuid(), primary_key=True),
    Column("id", Uuid(), primary_key=True),
    Column("citation_id", Uuid(), ForeignKey("citation_spans.id"), nullable=False),
    Column("payload", JSON(), nullable=False),
)
reviewer_overrides = Table(
    "reviewer_overrides",
    metadata,
    Column("tenant_id", Uuid(), primary_key=True),
    Column("original_id", Uuid(), primary_key=True),
    Column("revised_id", Uuid(), nullable=False),
    Column("payload", JSON(), nullable=False),
    ForeignKeyConstraint(
        ["tenant_id", "original_id"],
        ["coverage_assessments.tenant_id", "coverage_assessments.id"],
        name="fk_reviewer_overrides_original",
    ),
    ForeignKeyConstraint(
        ["tenant_id", "revised_id"],
        ["coverage_assessments.tenant_id", "coverage_assessments.id"],
        name="fk_reviewer_overrides_revised",
    ),
    UniqueConstraint("tenant_id", "revised_id", name="uq_reviewer_overrides_revision"),
)
export_approvals = Table(
    "export_approvals",
    metadata,
    Column("tenant_id", Uuid(), primary_key=True),
    Column("packet_id", Uuid(), primary_key=True),
    Column("approval_id", Uuid(), nullable=False),
    Column("packet_sha256", String(64), nullable=False),
    Column("payload", JSON(), nullable=False),
    UniqueConstraint(
        "tenant_id", "approval_id", name="uq_export_approvals_approval_id"
    ),
    CheckConstraint("length(packet_sha256) = 64", name="checksum_length"),
)
audit_heads = Table(
    "audit_heads",
    metadata,
    Column("tenant_id", Uuid(), primary_key=True),
    Column("sequence", Integer(), nullable=False),
    CheckConstraint("sequence > 0", name="positive_sequence"),
)
audit_events = Table(
    "audit_events",
    metadata,
    Column("tenant_id", Uuid(), ForeignKey("audit_heads.tenant_id"), primary_key=True),
    Column("sequence", Integer(), primary_key=True),
    Column("id", Uuid(), nullable=False),
    Column("action", String(30), nullable=False),
    Column("subject_id", Uuid(), nullable=False),
    Column("occurred_at", UtcTimestamp(), nullable=False),
    Column("actor_id", Uuid()),
    UniqueConstraint("tenant_id", "id", name="uq_audit_events_tenant_event"),
    CheckConstraint("sequence > 0", name="positive_sequence"),
)


class WorkflowStore(ReviewStore):
    def add_checklist_item(
        self, item: EvidenceChecklistItem, citation_id: UUID
    ) -> None:
        item = EvidenceChecklistItem.model_validate(item)
        self._check_tenant(item.tenant_id)
        if SourceStore(self.session).get_citation(citation_id) != item.source:
            raise ValueError("checklist item must refer to the exact stored citation")
        self.session.execute(
            insert(checklist_items).values(
                tenant_id=self.tenant_id,
                id=item.id,
                citation_id=citation_id,
                payload=item.model_dump(mode="json"),
            )
        )

    def get_checklist_item(self, item_id: UUID) -> EvidenceChecklistItem | None:
        payload = self.session.execute(
            select(checklist_items.c.payload).where(
                checklist_items.c.tenant_id == self.tenant_id,
                checklist_items.c.id == item_id,
            )
        ).scalar_one_or_none()
        return (
            EvidenceChecklistItem.model_validate(payload)
            if payload is not None
            else None
        )

    def record_override(self, decision: ReviewerOverride, event_id: UUID) -> AuditEvent:
        decision = ReviewerOverride.model_validate(decision)
        self._check_tenant(decision.original.tenant_id)
        if self.get_assessment(decision.original.id) != decision.original:
            raise ValueError(
                "override must refer to the exact stored original assessment"
            )
        with self.session.begin_nested():
            self.add_assessment(decision.revised)
            self.session.execute(
                insert(reviewer_overrides).values(
                    tenant_id=self.tenant_id,
                    original_id=decision.original.id,
                    revised_id=decision.revised.id,
                    payload=decision.model_dump(mode="json"),
                )
            )
            return self._append_event(
                event_id,
                AuditAction.COVERAGE_OVERRIDDEN,
                decision.revised.id,
                decision.review.reviewed_at,
                decision.review.reviewer_id,
            )

    def get_override(self, original_id: UUID) -> ReviewerOverride | None:
        payload = self.session.execute(
            select(reviewer_overrides.c.payload).where(
                reviewer_overrides.c.tenant_id == self.tenant_id,
                reviewer_overrides.c.original_id == original_id,
            )
        ).scalar_one_or_none()
        return ReviewerOverride.model_validate(payload) if payload is not None else None

    def record_approval(self, packet: ApprovedPacket, event_id: UUID) -> AuditEvent:
        packet = ApprovedPacket.model_validate(packet)
        self._check_tenant(packet.content.tenant_id)
        sources = SourceStore(self.session)
        for source in packet.content.sources:
            if (
                sources.get_document(source.document.id) != source.document
                or sources.get_version(source.version.id) != source.version
                or any(
                    sources.get_section(section.id) != section
                    for section in source.sections
                )
            ):
                raise ValueError("approval requires exact stored source provenance")
        if any(
            self.get_checklist_item(item.id) != item
            for item in packet.content.checklist
        ):
            raise ValueError("approval requires exact stored checklist items")
        with self.session.begin_nested():
            self.session.execute(
                insert(export_approvals).values(
                    tenant_id=self.tenant_id,
                    packet_id=packet.content.id,
                    approval_id=packet.approval.id,
                    packet_sha256=packet.approval.packet_sha256,
                    payload=packet.model_dump(mode="json"),
                )
            )
            return self._append_event(
                event_id,
                AuditAction.EXPORT_APPROVED,
                packet.content.id,
                packet.approval.review.reviewed_at,
                packet.approval.review.reviewer_id,
            )

    def get_approval(self, packet_id: UUID) -> ApprovedPacket | None:
        payload = self.session.execute(
            select(export_approvals.c.payload).where(
                export_approvals.c.tenant_id == self.tenant_id,
                export_approvals.c.packet_id == packet_id,
            )
        ).scalar_one_or_none()
        return ApprovedPacket.model_validate(payload) if payload is not None else None

    def list_events(self) -> tuple[AuditEvent, ...]:
        rows = self.session.execute(
            select(audit_events)
            .where(
                audit_events.c.tenant_id == self.tenant_id,
            )
            .order_by(audit_events.c.sequence)
        ).mappings()
        return tuple(map(AuditEvent.model_validate, rows))

    def _append_event(
        self,
        event_id: UUID,
        action: AuditAction,
        subject_id: UUID,
        occurred_at: datetime,
        actor_id: UUID,
    ) -> AuditEvent:
        insert_head = (
            pg_insert
            if self.session.get_bind().dialect.name == "postgresql"
            else sqlite_insert
        )
        statement = insert_head(audit_heads).values(
            tenant_id=self.tenant_id, sequence=1
        )
        advance = statement.on_conflict_do_update(
            index_elements=[audit_heads.c.tenant_id],
            set_={"sequence": audit_heads.c.sequence + 1},
        )
        sequence = self.session.execute(
            advance.returning(audit_heads.c.sequence)
        ).scalar_one()
        event = AuditEvent(
            id=event_id,
            tenant_id=self.tenant_id,
            sequence=sequence,
            action=action,
            subject_id=subject_id,
            occurred_at=occurred_at,
            actor_id=actor_id,
        )
        self.session.execute(insert(audit_events).values(event.model_dump()))
        return event
