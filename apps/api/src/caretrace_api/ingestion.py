from hashlib import sha256
from pathlib import PureWindowsPath
from typing import Annotated, Literal, Protocol, Self
from uuid import UUID

from caretrace_contracts.assessment import PolicyAttestation
from caretrace_contracts.common import Contract, Label, Sha256
from caretrace_contracts.sources import SourceDocument, SourceVersion
from pydantic import AwareDatetime, Field, model_validator

type InputClassification = Literal[
    "public_source", "synthetic", "authorized_de_identified"
]
type RejectionCode = Literal[
    "unsupported_type",
    "size_limit",
    "invalid_text",
    "checksum_mismatch",
    "duplicate_content",
]


class IngestionRejected(ValueError):
    def __init__(self, code: RejectionCode) -> None:
        self.code = code
        super().__init__(code)


class PublicSourceInput(Contract):
    document: SourceDocument
    version: SourceVersion

    @model_validator(mode="after")
    def validate_document(self) -> Self:
        if self.document.id != self.version.document_id:
            raise ValueError("public input version must belong to the source document")
        return self


class IngestionRequest(Contract):
    id: UUID
    tenant_id: UUID
    filename: Label
    media_type: Label
    received_at: AwareDatetime
    classification: InputClassification
    attestation: PolicyAttestation | None = None
    public_source: PublicSourceInput | None = None

    @model_validator(mode="after")
    def validate_classification(self) -> Self:
        if self.classification == "public_source":
            if (
                self.public_source is None
                or self.public_source.version.retrieved_at > self.received_at
            ):
                raise ValueError("public input requires existing retrieval provenance")
        elif self.public_source is not None:
            raise ValueError(
                "public source provenance requires a public source classification"
            )
        if self.classification == "authorized_de_identified":
            if (
                self.attestation is None
                or self.attestation.attested_at > self.received_at
            ):
                raise ValueError(
                    "authorized input requires a prior or concurrent attestation"
                )
        elif self.attestation is not None:
            raise ValueError(
                "authorization attestation requires the authorized classification"
            )
        return self


class IngestionManifest(Contract):
    request: IngestionRequest
    original_sha256: Sha256
    size_bytes: Annotated[int, Field(strict=True, gt=0)]

    @model_validator(mode="after")
    def verify_source_digest(self) -> Self:
        source = self.request.public_source
        if (
            source is not None
            and source.version.original_sha256 != self.original_sha256
        ):
            raise ValueError("public source version checksum must match the original")
        return self


class ParsedText(Contract):
    manifest_id: UUID
    original_sha256: Sha256
    parser_version: Label
    text: str


class OriginalStore(Protocol):
    def save_once(self, manifest: IngestionManifest, original: bytes) -> bool:
        """Retain original bytes and manifest atomically, returning false for an existing tenant digest."""


class TextParser(Protocol):
    def parse(self, manifest: IngestionManifest, original: bytes) -> ParsedText: ...


class OcrReader(Protocol):
    def recognize(self, image: bytes) -> str: ...


def content_sha256(original: bytes) -> str:
    return sha256(original).hexdigest()


def admit_input(
    request: IngestionRequest,
    original: bytes,
    store: OriginalStore,
    *,
    max_bytes: int = 1_048_576,
) -> IngestionManifest:
    request = IngestionRequest.model_validate(request)
    filename = PureWindowsPath(request.filename)
    if (
        filename.name != request.filename
        or filename.suffix.lower() != ".txt"
        or request.media_type.lower() != "text/plain"
        or any(char in request.filename for char in ("/", "\\", ":", "\0"))
    ):
        raise IngestionRejected("unsupported_type")
    if not 0 < len(original) <= max_bytes:
        raise IngestionRejected("size_limit")
    _decode_text(original)
    digest = content_sha256(original)
    source = request.public_source
    if source is not None and source.version.original_sha256 != digest:
        raise IngestionRejected("checksum_mismatch")
    manifest = IngestionManifest(
        request=request, original_sha256=digest, size_bytes=len(original)
    )
    if not store.save_once(manifest, original):
        raise IngestionRejected("duplicate_content")
    return manifest


class Utf8TextParser:
    def parse(self, manifest: IngestionManifest, original: bytes) -> ParsedText:
        if (
            len(original) != manifest.size_bytes
            or content_sha256(original) != manifest.original_sha256
        ):
            raise IngestionRejected("checksum_mismatch")
        return ParsedText(
            manifest_id=manifest.request.id,
            original_sha256=manifest.original_sha256,
            parser_version="utf8-text-1",
            text=_decode_text(original),
        )


def _decode_text(original: bytes) -> str:
    try:
        text = original.decode("utf-8")
    except UnicodeDecodeError:
        raise IngestionRejected("invalid_text") from None
    if not text.strip() or "\0" in text:
        raise IngestionRejected("invalid_text")
    return text
