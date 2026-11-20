from datetime import UTC, date, datetime
from io import StringIO
from os import environ
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from caretrace_api.database import Database
from caretrace_api.source_store import SourceStore, source_versions
from caretrace_contracts.sources import (
    Jurisdiction,
    SourceDocument,
    SourceKind,
    SourceSection,
    SourceVersion,
)
from pydantic import HttpUrl
from sqlalchemy import inspect, text, update
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError

ALEMBIC_CONFIG = Path(__file__).resolve().parents[3] / "infra" / "alembic.ini"


def test_postgres_migration_renders_vector_extension_and_immutability(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "CARETRACE_DATABASE_URL", "postgresql+psycopg://db.example.test/caretrace"
    )
    monkeypatch.setenv("CARETRACE_ENVIRONMENT", "test")
    output = StringIO()
    command.upgrade(Config(ALEMBIC_CONFIG, output_buffer=output), "head", sql=True)
    sql = output.getvalue()
    assert "CREATE EXTENSION IF NOT EXISTS vector;" in sql
    assert (
        "CREATE TRIGGER source_versions_immutable BEFORE UPDATE ON source_versions"
        in sql
    )


@pytest.mark.parametrize("backend", ["sqlite", "postgresql"])
def test_migration_and_provenance_repository(backend: str) -> None:
    url = "sqlite+pysqlite:///:memory:"
    if backend == "postgresql":
        url = environ.get("CARETRACE_TEST_POSTGRES_URL", "")
        if not url:
            pytest.skip(
                "CARETRACE_TEST_POSTGRES_URL is not configured for a disposable database"
            )
    database = Database(make_url(url))
    config = Config(ALEMBIC_CONFIG)

    try:
        with database.engine.begin() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
            command.check(config)
            if backend == "postgresql":
                assert (
                    connection.execute(
                        text(
                            "SELECT extname FROM pg_extension WHERE extname = 'vector'"
                        )
                    ).scalar_one()
                    == "vector"
                )

        document = SourceDocument(
            id=uuid4(),
            title="Synthetic source",
            jurisdiction=Jurisdiction.ONTARIO,
            kind=SourceKind.REGULATION,
            source_url=HttpUrl("https://sources.example.test/fixture"),
        )
        version = SourceVersion(
            id=uuid4(),
            document_id=document.id,
            version="sample-1",
            version_url=document.source_url,
            retrieved_at=datetime(2026, 11, 20, tzinfo=UTC),
            original_sha256="b" * 64,
            effective_from=date(2026, 11, 1),
        )
        section = SourceSection(
            id=uuid4(),
            source_version_id=version.id,
            locator="Example §1",
            citation_url=document.source_url,
            text="  Synthetic 🧪 sample.  ",
        )
        citation_id = uuid4()
        citation = section.cite(2, 13)
        with database.session() as session:
            store = SourceStore(session)
            store.add_document(document)
            store.add_version(version)
            store.add_section(section)
            store.add_citation(citation_id, citation)

        with database.session() as session:
            store = SourceStore(session)
            assert store.get_document(document.id) == document
            assert store.get_version(version.id) == version
            assert store.get_section(section.id) == section
            assert store.get_citation(citation_id) == citation
            assert store.get_citation(uuid4()) is None
            with pytest.raises(ValueError, match="exact section text"):
                store.add_citation(
                    uuid4(), citation.model_copy(update={"source_version_id": uuid4()})
                )

        with (
            pytest.raises(IntegrityError, match="provenance is immutable"),
            database.session() as session,
        ):
            session.execute(
                update(source_versions)
                .where(source_versions.c.id == version.id)
                .values(original_sha256="a" * 64)
            )

        with pytest.raises(IntegrityError), database.session() as session:
            SourceStore(session).add_version(version.model_copy(update={"id": uuid4()}))

        with database.engine.begin() as connection:
            config.attributes["connection"] = connection
            command.downgrade(config, "base")
            assert not inspect(connection).has_table("source_versions")
            command.upgrade(config, "head")
            assert inspect(connection).has_table("citation_spans")
    finally:
        database.dispose()
