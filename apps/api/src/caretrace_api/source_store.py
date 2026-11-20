from datetime import UTC, datetime
from uuid import UUID

from caretrace_contracts.sources import (
    CitationSpan,
    SourceDocument,
    SourceSection,
    SourceVersion,
)
from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
    Uuid,
    insert,
    select,
)
from sqlalchemy.engine import Dialect
from sqlalchemy.orm import Session
from sqlalchemy.types import TypeDecorator


class UtcTimestamp(TypeDecorator[datetime]):
    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(
        self, value: datetime | None, dialect: Dialect
    ) -> datetime | None:
        if value is None:
            return None
        if value.utcoffset() is None:
            raise ValueError("database timestamps require a timezone")
        return value.astimezone(UTC)

    def process_result_value(
        self, value: datetime | None, dialect: Dialect
    ) -> datetime | None:
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value


metadata = MetaData(
    naming_convention={
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
    }
)

source_documents = Table(
    "source_documents",
    metadata,
    Column("id", Uuid(), primary_key=True),
    Column("title", Text(), nullable=False),
    Column("jurisdiction", String(12), nullable=False),
    Column("kind", String(30), nullable=False),
    Column("source_url", String(2083), nullable=False, unique=True),
)
source_versions = Table(
    "source_versions",
    metadata,
    Column("id", Uuid(), primary_key=True),
    Column("document_id", Uuid(), ForeignKey("source_documents.id"), nullable=False),
    Column("version", Text(), nullable=False),
    Column("version_url", String(2083), nullable=False),
    Column("retrieved_at", UtcTimestamp(), nullable=False),
    Column("original_sha256", String(64), nullable=False),
    Column("effective_from", Date()),
    Column("effective_until", Date()),
    UniqueConstraint("document_id", "version"),
    CheckConstraint("length(original_sha256) = 64", name="checksum_length"),
    CheckConstraint(
        "effective_until IS NULL OR (effective_from IS NOT NULL AND effective_until > effective_from)",
        name="effective_interval",
    ),
)
source_sections = Table(
    "source_sections",
    metadata,
    Column("id", Uuid(), primary_key=True),
    Column(
        "source_version_id", Uuid(), ForeignKey("source_versions.id"), nullable=False
    ),
    Column("locator", Text(), nullable=False),
    Column("citation_url", String(2083), nullable=False),
    Column("text", Text(), nullable=False),
    UniqueConstraint(
        "source_version_id", "locator", name="uq_source_sections_version_locator"
    ),
    UniqueConstraint("source_version_id", "id", name="uq_source_sections_version_id"),
)
citation_spans = Table(
    "citation_spans",
    metadata,
    Column("id", Uuid(), primary_key=True),
    Column("source_version_id", Uuid(), nullable=False),
    Column("section_id", Uuid(), nullable=False),
    Column("start_offset", Integer(), nullable=False),
    Column("end_offset", Integer(), nullable=False),
    Column("quote", Text(), nullable=False),
    ForeignKeyConstraint(
        ["source_version_id", "section_id"],
        ["source_sections.source_version_id", "source_sections.id"],
    ),
    CheckConstraint(
        "start_offset >= 0 AND end_offset > start_offset", name="offset_range"
    ),
)


class SourceStore:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add_document(self, document: SourceDocument) -> None:
        values = document.model_dump(exclude={"source_url"}) | {
            "source_url": str(document.source_url)
        }
        self.session.execute(insert(source_documents).values(values))

    def add_version(self, version: SourceVersion) -> None:
        values = version.model_dump(exclude={"version_url"}) | {
            "version_url": str(version.version_url)
        }
        self.session.execute(insert(source_versions).values(values))

    def add_section(self, section: SourceSection) -> None:
        values = section.model_dump(exclude={"citation_url"}) | {
            "citation_url": str(section.citation_url)
        }
        self.session.execute(insert(source_sections).values(values))

    def add_citation(self, citation_id: UUID, citation: CitationSpan) -> None:
        section = self.get_section(citation.section_id)
        if section is None or not citation.matches(section):
            raise ValueError(
                "citation must match the stored version and exact section text"
            )
        self.session.execute(
            insert(citation_spans).values(
                id=citation_id,
                source_version_id=citation.source_version_id,
                section_id=citation.section_id,
                start_offset=citation.start,
                end_offset=citation.end,
                quote=citation.quote,
            )
        )

    def get_document(self, document_id: UUID) -> SourceDocument | None:
        row = (
            self.session.execute(
                select(source_documents).where(source_documents.c.id == document_id)
            )
            .mappings()
            .one_or_none()
        )
        return SourceDocument.model_validate(row) if row is not None else None

    def get_version(self, version_id: UUID) -> SourceVersion | None:
        row = (
            self.session.execute(
                select(source_versions).where(source_versions.c.id == version_id)
            )
            .mappings()
            .one_or_none()
        )
        return SourceVersion.model_validate(row) if row is not None else None

    def get_section(self, section_id: UUID) -> SourceSection | None:
        row = (
            self.session.execute(
                select(source_sections).where(source_sections.c.id == section_id)
            )
            .mappings()
            .one_or_none()
        )
        return SourceSection.model_validate(row) if row is not None else None

    def get_citation(self, citation_id: UUID) -> CitationSpan | None:
        fields = (
            citation_spans.c.source_version_id,
            citation_spans.c.section_id,
            citation_spans.c.start_offset.label("start"),
            citation_spans.c.end_offset.label("end"),
            citation_spans.c.quote,
        )
        row = (
            self.session.execute(
                select(*fields).where(citation_spans.c.id == citation_id)
            )
            .mappings()
            .one_or_none()
        )
        return CitationSpan.model_validate(row) if row is not None else None
