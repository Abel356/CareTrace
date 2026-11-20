"""workflow audit"""

import sqlalchemy as sa
from alembic import op

revision = "0003_workflow_audit"
down_revision = "0002_policy_coverage"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_heads",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "sequence > 0", name=op.f("ck_audit_heads_positive_sequence")
        ),
        sa.PrimaryKeyConstraint("tenant_id", name=op.f("pk_audit_heads")),
    )
    op.create_table(
        "export_approvals",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("packet_id", sa.Uuid(), nullable=False),
        sa.Column("approval_id", sa.Uuid(), nullable=False),
        sa.Column("packet_sha256", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.CheckConstraint(
            "length(packet_sha256) = 64",
            name=op.f("ck_export_approvals_checksum_length"),
        ),
        sa.PrimaryKeyConstraint(
            "tenant_id", "packet_id", name=op.f("pk_export_approvals")
        ),
        sa.UniqueConstraint(
            "tenant_id", "approval_id", name="uq_export_approvals_approval_id"
        ),
    )
    op.create_table(
        "audit_events",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("action", sa.String(length=30), nullable=False),
        sa.Column("subject_id", sa.Uuid(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.CheckConstraint(
            "sequence > 0", name=op.f("ck_audit_events_positive_sequence")
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["audit_heads.tenant_id"],
            name=op.f("fk_audit_events_tenant_id_audit_heads"),
        ),
        sa.PrimaryKeyConstraint("tenant_id", "sequence", name=op.f("pk_audit_events")),
        sa.UniqueConstraint("tenant_id", "id", name="uq_audit_events_tenant_event"),
    )
    op.create_table(
        "checklist_items",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("citation_id", sa.Uuid(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["citation_id"],
            ["citation_spans.id"],
            name=op.f("fk_checklist_items_citation_id_citation_spans"),
        ),
        sa.PrimaryKeyConstraint("tenant_id", "id", name=op.f("pk_checklist_items")),
    )
    op.create_table(
        "reviewer_overrides",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("original_id", sa.Uuid(), nullable=False),
        sa.Column("revised_id", sa.Uuid(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id", "original_id"],
            ["coverage_assessments.tenant_id", "coverage_assessments.id"],
            name="fk_reviewer_overrides_original",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "revised_id"],
            ["coverage_assessments.tenant_id", "coverage_assessments.id"],
            name="fk_reviewer_overrides_revised",
        ),
        sa.PrimaryKeyConstraint(
            "tenant_id", "original_id", name=op.f("pk_reviewer_overrides")
        ),
        sa.UniqueConstraint(
            "tenant_id", "revised_id", name="uq_reviewer_overrides_revision"
        ),
    )
    dialect = op.get_context().dialect.name
    if dialect == "postgresql":
        op.execute(
            "CREATE FUNCTION caretrace_reject_audit_mutation() RETURNS trigger LANGUAGE plpgsql AS $$ "
            "BEGIN RAISE EXCEPTION 'Audit events are append-only' USING ERRCODE = '23514'; END; $$"
        )
        op.execute(
            "CREATE TRIGGER audit_events_append_only BEFORE UPDATE OR DELETE ON audit_events "
            "FOR EACH ROW EXECUTE FUNCTION caretrace_reject_audit_mutation()"
        )
    elif dialect == "sqlite":
        for action in ("UPDATE", "DELETE"):
            op.execute(
                f"CREATE TRIGGER audit_events_no_{action.lower()} BEFORE {action} ON audit_events "
                "BEGIN SELECT RAISE(ABORT, 'Audit events are append-only'); END"
            )


def downgrade() -> None:
    op.drop_table("reviewer_overrides")
    op.drop_table("checklist_items")
    op.drop_table("audit_events")
    op.drop_table("export_approvals")
    op.drop_table("audit_heads")
    if op.get_context().dialect.name == "postgresql":
        op.execute("DROP FUNCTION caretrace_reject_audit_mutation()")
