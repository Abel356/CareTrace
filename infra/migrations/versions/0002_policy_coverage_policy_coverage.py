"""policy coverage"""

import sqlalchemy as sa
from alembic import op

revision = "0002_policy_coverage"
down_revision = "0001_source_provenance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "policy_versions",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Text(), nullable=False),
        sa.Column("original_sha256", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.CheckConstraint(
            "length(original_sha256) = 64",
            name=op.f("ck_policy_versions_checksum_length"),
        ),
        sa.PrimaryKeyConstraint("tenant_id", "id", name=op.f("pk_policy_versions")),
        sa.UniqueConstraint(
            "tenant_id",
            "document_id",
            "version",
            name="uq_policy_versions_document_version",
        ),
        sa.UniqueConstraint(
            "tenant_id", "original_sha256", name="uq_policy_versions_checksum"
        ),
    )
    op.create_table(
        "policy_excerpts",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("policy_version_id", sa.Uuid(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id", "policy_version_id"],
            ["policy_versions.tenant_id", "policy_versions.id"],
            name=op.f("fk_policy_excerpts_tenant_id_policy_versions"),
        ),
        sa.PrimaryKeyConstraint("tenant_id", "id", name=op.f("pk_policy_excerpts")),
    )
    op.create_table(
        "obligation_candidates",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("citation_id", sa.Uuid(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["citation_id"],
            ["citation_spans.id"],
            name=op.f("fk_obligation_candidates_citation_id_citation_spans"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_obligation_candidates")),
    )
    op.create_table(
        "coverage_assessments",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("policy_version_id", sa.Uuid(), nullable=False),
        sa.Column("obligation_id", sa.Uuid(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["obligation_id"],
            ["obligation_candidates.id"],
            name=op.f("fk_coverage_assessments_obligation_id_obligation_candidates"),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "policy_version_id"],
            ["policy_versions.tenant_id", "policy_versions.id"],
            name=op.f("fk_coverage_assessments_tenant_id_policy_versions"),
        ),
        sa.PrimaryKeyConstraint(
            "tenant_id", "id", name=op.f("pk_coverage_assessments")
        ),
    )
    dialect = op.get_context().dialect.name
    if dialect == "postgresql":
        op.execute(
            "CREATE TRIGGER policy_versions_immutable BEFORE UPDATE ON policy_versions "
            "FOR EACH ROW EXECUTE FUNCTION caretrace_reject_provenance_update()"
        )
    elif dialect == "sqlite":
        op.execute(
            "CREATE TRIGGER policy_versions_immutable BEFORE UPDATE ON policy_versions "
            "BEGIN SELECT RAISE(ABORT, 'Policy version is immutable'); END"
        )


def downgrade() -> None:
    op.drop_table("coverage_assessments")
    op.drop_table("obligation_candidates")
    op.drop_table("policy_excerpts")
    op.drop_table("policy_versions")
