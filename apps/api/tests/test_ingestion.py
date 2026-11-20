from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from alembic import command
from alembic.config import Config
from caretrace_api.database import Database
from caretrace_api.ingestion import (
    IngestionManifest,
    IngestionRejected,
    IngestionRequest,
    PublicSourceInput,
    Utf8TextParser,
    admit_input,
    content_sha256,
)
from caretrace_api.ingestion_store import DatabaseOriginalStore
from caretrace_contracts.assessment import PolicyAttestation
from caretrace_contracts.sources import (
    Jurisdiction,
    SourceDocument,
    SourceKind,
    SourceVersion,
)
from pydantic import HttpUrl, ValidationError
from sqlalchemy.engine import make_url

NOW = datetime(2026, 11, 20, tzinfo=UTC)


class MemoryOriginals:
    def __init__(self) -> None:
        self.saved: dict[tuple[UUID, str], tuple[IngestionManifest, bytes]] = {}

    def save_once(self, manifest: IngestionManifest, original: bytes) -> bool:
        key = manifest.request.tenant_id, manifest.original_sha256
        if key in self.saved:
            return False
        self.saved[key] = manifest, original
        return True


@pytest.fixture
def request_metadata() -> IngestionRequest:
    return IngestionRequest(
        id=uuid4(),
        tenant_id=uuid4(),
        filename="sample.txt",
        media_type="text/plain",
        received_at=NOW,
        classification="synthetic",
    )


def test_admits_only_once_per_tenant_without_changing_original(
    request_metadata: IngestionRequest,
) -> None:
    store = MemoryOriginals()
    original = "  Synthetic 🧪 sample\r\n".encode()
    manifest = admit_input(request_metadata, original, store)
    key = request_metadata.tenant_id, manifest.original_sha256
    assert store.saved[key] == (manifest, original)
    assert manifest.original_sha256 == content_sha256(original)
    assert Utf8TextParser().parse(manifest, original).text == original.decode()
    with pytest.raises(IngestionRejected, match="checksum_mismatch"):
        Utf8TextParser().parse(manifest, b"Changed bytes")
    with pytest.raises(IngestionRejected, match="duplicate_content"):
        admit_input(
            request_metadata.model_copy(update={"id": uuid4()}), original, store
        )
    other = request_metadata.model_copy(update={"id": uuid4(), "tenant_id": uuid4()})
    assert (
        admit_input(other, original, store).original_sha256 == manifest.original_sha256
    )


@pytest.mark.parametrize(
    "filename,media_type,content,code",
    [
        ("sample.pdf", "application/pdf", b"Synthetic text", "unsupported_type"),
        ("sample.txt", "application/pdf", b"Synthetic text", "unsupported_type"),
        ("folder/sample.txt", "text/plain", b"Synthetic text", "unsupported_type"),
        ("sample.txt", "text/plain", b"!" * 17, "size_limit"),
        ("sample.txt", "text/plain", b"\xff\x00", "invalid_text"),
        ("sample.txt", "text/plain", b" \n", "invalid_text"),
    ],
)
def test_admission_rejects_before_storage(
    request_metadata: IngestionRequest,
    filename: str,
    media_type: str,
    content: bytes,
    code: str,
) -> None:
    store = MemoryOriginals()
    request = request_metadata.model_copy(
        update={"filename": filename, "media_type": media_type}
    )
    with pytest.raises(IngestionRejected, match=code):
        admit_input(request, content, store, max_bytes=16)
    assert not store.saved


def test_authorized_input_requires_recorded_attestation(
    request_metadata: IngestionRequest,
) -> None:
    authorized = request_metadata.model_dump() | {
        "classification": "authorized_de_identified"
    }
    with pytest.raises(ValidationError, match="attestation"):
        IngestionRequest.model_validate(authorized)
    attestation = PolicyAttestation(
        attested_by=uuid4(),
        attested_at=NOW,
        authorization_reference="Synthetic authorization",
        de_identification_confirmed=True,
    )
    request = IngestionRequest.model_validate(authorized | {"attestation": attestation})
    assert (
        admit_input(
            request, b"Synthetic fixture", MemoryOriginals()
        ).request.attestation
        == attestation
    )


def test_public_input_requires_provenance_bound_to_original(
    request_metadata: IngestionRequest,
) -> None:
    original = b"Synthetic public source fixture"
    url = HttpUrl("https://sources.example.test/sample")
    document = SourceDocument(
        id=uuid4(),
        title="Synthetic public source",
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
        original_sha256=content_sha256(original),
    )
    public = request_metadata.model_dump() | {"classification": "public_source"}
    with pytest.raises(ValidationError, match="retrieval provenance"):
        IngestionRequest.model_validate(public)
    request = IngestionRequest.model_validate(
        public
        | {"public_source": PublicSourceInput(document=document, version=version)}
    )
    with pytest.raises(IngestionRejected, match="checksum_mismatch"):
        admit_input(request, b"Altered text", MemoryOriginals())
    assert (
        admit_input(request, original, MemoryOriginals()).request.public_source
        is not None
    )


def test_database_original_retention_rejects_tenant_duplicates(
    request_metadata: IngestionRequest,
) -> None:
    database = Database(make_url("sqlite+pysqlite:///:memory:"))
    config = Config(Path(__file__).resolve().parents[3] / "infra" / "alembic.ini")
    original = b"Synthetic original\r\n"
    try:
        with database.engine.begin() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
        with database.session() as session:
            store = DatabaseOriginalStore(session, request_metadata.tenant_id)
            manifest = admit_input(request_metadata, original, store)
            with pytest.raises(IngestionRejected, match="duplicate_content"):
                admit_input(
                    request_metadata.model_copy(update={"id": uuid4()}), original, store
                )
        with database.session() as session:
            store = DatabaseOriginalStore(session, request_metadata.tenant_id)
            assert store.get_original(request_metadata.id) == (manifest, original)
            other = DatabaseOriginalStore(session, uuid4())
            assert other.get_original(request_metadata.id) is None
            with pytest.raises(ValueError, match="outside the repository tenant"):
                other.save_once(manifest, original)
    finally:
        database.dispose()
