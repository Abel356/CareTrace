from uuid import UUID

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    LargeBinary,
    String,
    Table,
    UniqueConstraint,
    Uuid,
    select,
)
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from caretrace_api.ingestion import IngestionManifest, content_sha256
from caretrace_api.workflow_store import metadata as metadata

original_inputs = Table(
    "original_inputs",
    metadata,
    Column("tenant_id", Uuid(), primary_key=True),
    Column("id", Uuid(), primary_key=True),
    Column("original_sha256", String(64), nullable=False),
    Column("original", LargeBinary(), nullable=False),
    Column("manifest", JSON(), nullable=False),
    UniqueConstraint(
        "tenant_id", "original_sha256", name="uq_original_inputs_tenant_digest"
    ),
    CheckConstraint(
        "length(original_sha256) = 64 AND length(original) > 0", name="original_data"
    ),
)


class DatabaseOriginalStore:
    def __init__(self, session: Session, tenant_id: UUID) -> None:
        self.session = session
        self.tenant_id = tenant_id

    def save_once(self, manifest: IngestionManifest, original: bytes) -> bool:
        if manifest.request.tenant_id != self.tenant_id:
            raise ValueError("original is outside the repository tenant")
        if (
            len(original) != manifest.size_bytes
            or content_sha256(original) != manifest.original_sha256
        ):
            raise ValueError("original bytes must match the manifest")
        insert_original = (
            pg_insert
            if self.session.get_bind().dialect.name == "postgresql"
            else sqlite_insert
        )
        statement = insert_original(original_inputs).values(
            tenant_id=self.tenant_id,
            id=manifest.request.id,
            original_sha256=manifest.original_sha256,
            original=original,
            manifest=manifest.model_dump(mode="json"),
        )
        insert_once = statement.on_conflict_do_nothing(
            index_elements=[
                original_inputs.c.tenant_id,
                original_inputs.c.original_sha256,
            ]
        )
        return (
            self.session.execute(
                insert_once.returning(original_inputs.c.id)
            ).scalar_one_or_none()
            is not None
        )

    def get_original(self, manifest_id: UUID) -> tuple[IngestionManifest, bytes] | None:
        row = self.session.execute(
            select(original_inputs.c.manifest, original_inputs.c.original).where(
                original_inputs.c.tenant_id == self.tenant_id,
                original_inputs.c.id == manifest_id,
            )
        ).one_or_none()
        if row is None:
            return None
        manifest, original = row
        return IngestionManifest.model_validate(manifest), bytes(original)
