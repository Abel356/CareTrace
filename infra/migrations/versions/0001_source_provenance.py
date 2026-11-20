"""Store versioned sources and immutable citation provenance."""

import sqlalchemy as sa
from alembic import op

revision = "0001_source_provenance"
down_revision = None
branch_labels = None
depends_on = None

IMMUTABLE_TABLES = ("source_versions", "source_sections", "citation_spans")


def upgrade() -> None:
    dialect = op.get_context().dialect.name
    if dialect == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "source_documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("jurisdiction", sa.String(12), nullable=False),
        sa.Column("kind", sa.String(30), nullable=False),
        sa.Column("source_url", sa.String(2083), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_source_documents"),
        sa.UniqueConstraint("source_url", name="uq_source_documents_source_url"),
    )
    op.create_table(
        "source_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Text(), nullable=False),
        sa.Column("version_url", sa.String(2083), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("original_sha256", sa.String(64), nullable=False),
        sa.Column("effective_from", sa.Date()),
        sa.Column("effective_until", sa.Date()),
        sa.PrimaryKeyConstraint("id", name="pk_source_versions"),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["source_documents.id"],
            name="fk_source_versions_document_id_source_documents",
        ),
        sa.UniqueConstraint(
            "document_id", "version", name="uq_source_versions_document_id"
        ),
        sa.CheckConstraint(
            "length(original_sha256) = 64",
            name=op.f("ck_source_versions_checksum_length"),
        ),
        sa.CheckConstraint(
            "effective_until IS NULL OR (effective_from IS NOT NULL AND effective_until > effective_from)",
            name=op.f("ck_source_versions_effective_interval"),
        ),
    )
    op.create_table(
        "source_sections",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_version_id", sa.Uuid(), nullable=False),
        sa.Column("locator", sa.Text(), nullable=False),
        sa.Column("citation_url", sa.String(2083), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_source_sections"),
        sa.ForeignKeyConstraint(
            ["source_version_id"],
            ["source_versions.id"],
            name="fk_source_sections_source_version_id_source_versions",
        ),
        sa.UniqueConstraint(
            "source_version_id", "locator", name="uq_source_sections_version_locator"
        ),
        sa.UniqueConstraint(
            "source_version_id", "id", name="uq_source_sections_version_id"
        ),
    )
    op.create_table(
        "citation_spans",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_version_id", sa.Uuid(), nullable=False),
        sa.Column("section_id", sa.Uuid(), nullable=False),
        sa.Column("start_offset", sa.Integer(), nullable=False),
        sa.Column("end_offset", sa.Integer(), nullable=False),
        sa.Column("quote", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_citation_spans"),
        sa.ForeignKeyConstraint(
            ["source_version_id", "section_id"],
            ["source_sections.source_version_id", "source_sections.id"],
            name="fk_citation_spans_source_version_id_source_sections",
        ),
        sa.CheckConstraint(
            "start_offset >= 0 AND end_offset > start_offset",
            name=op.f("ck_citation_spans_offset_range"),
        ),
    )

    if dialect == "postgresql":
        op.execute(
            "CREATE FUNCTION caretrace_reject_provenance_update() RETURNS trigger LANGUAGE plpgsql AS $$ "
            "BEGIN RAISE EXCEPTION 'Source provenance is immutable' USING ERRCODE = '23514'; END; $$"
        )
        for table in IMMUTABLE_TABLES:
            op.execute(
                f"CREATE TRIGGER {table}_immutable BEFORE UPDATE ON {table} "
                "FOR EACH ROW EXECUTE FUNCTION caretrace_reject_provenance_update()"
            )
    elif dialect == "sqlite":
        for table in IMMUTABLE_TABLES:
            op.execute(
                f"CREATE TRIGGER {table}_immutable BEFORE UPDATE ON {table} "
                "BEGIN SELECT RAISE(ABORT, 'Source provenance is immutable'); END"
            )


def downgrade() -> None:
    op.drop_table("citation_spans")
    op.drop_table("source_sections")
    op.drop_table("source_versions")
    op.drop_table("source_documents")
    if op.get_context().dialect.name == "postgresql":
        op.execute("DROP FUNCTION caretrace_reject_provenance_update()")
