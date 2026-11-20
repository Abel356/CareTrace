from pathlib import Path

import pytest
from caretrace_api.database import Database
from caretrace_api.main import create_app
from caretrace_api.settings import Settings
from fastapi.testclient import TestClient
from pydantic import SecretStr, ValidationError
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError


def test_sessions_commit_and_roll_back_database_writes() -> None:
    database = Database(make_url("sqlite+pysqlite:///:memory:"))
    try:
        with database.session() as session:
            session.execute(text("CREATE TABLE example (id INTEGER PRIMARY KEY)"))
            session.execute(text("INSERT INTO example VALUES (1)"))
            session.execute(
                text("CREATE TABLE related (id INTEGER REFERENCES example(id))")
            )
        with pytest.raises(IntegrityError), database.session() as session:
            session.execute(text("INSERT INTO example VALUES (2)"))
            session.execute(text("INSERT INTO related VALUES (3)"))
        with database.session() as session:
            assert session.execute(text("SELECT id FROM example")).scalars().all() == [
                1
            ]
    finally:
        database.dispose()


def test_health_reports_configured_database_status(tmp_path: Path) -> None:
    ready = Settings(
        environment="test", database_url=SecretStr("sqlite+pysqlite:///:memory:")
    )
    unavailable = Settings(
        environment="test",
        database_url=SecretStr(
            f"sqlite+pysqlite:///{(tmp_path / 'missing' / 'test.db').as_posix()}"
        ),
    )
    with TestClient(create_app(ready), base_url="http://localhost") as client:
        assert client.get("/readyz").status_code == 200
    with TestClient(create_app(unavailable), base_url="http://localhost") as client:
        assert client.get("/livez").status_code == 200
        response = client.get("/readyz")
        assert response.json() == {"status": "unavailable"}
        assert response.status_code == 503


def test_database_url_validation_redacts_secrets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CARETRACE_DATABASE_URL", "synthetic-invalid-dsn")
    with pytest.raises(ValidationError, match="invalid database URL") as error:
        Settings()
    assert "synthetic-invalid-dsn" not in str(error.value)
