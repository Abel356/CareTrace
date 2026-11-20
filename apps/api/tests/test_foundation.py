from importlib.metadata import version
from os import environ
from pathlib import Path

import pytest
from caretrace_api.main import create_app
from caretrace_api.settings import Settings
from fastapi.testclient import TestClient
from pydantic import ValidationError


@pytest.fixture(autouse=True)
def isolate_settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    for name in tuple(environ):
        if name.upper().startswith("CARETRACE_"):
            monkeypatch.delenv(name)


def test_health_and_build_information() -> None:
    with TestClient(
        create_app(Settings(environment="test")), base_url="http://localhost"
    ) as client:
        assert client.get("/livez").json() == {"status": "alive"}
        response = client.get("/readyz")
        assert response.status_code == 200
        assert response.json() == {"status": "ready"}
        assert client.get("/api/v1/build").json() == {
            "service": "caretrace-api",
            "version": version("caretrace-api"),
        }
        schema = client.get("/openapi.json").json()
        assert "/api/v1/build" in schema["paths"]
        assert "503" in schema["paths"]["/readyz"]["get"]["responses"]
        assert "Qualified human review is required" in schema["info"]["description"]


def test_readiness_can_distinguish_process_from_dependency_failure() -> None:
    app = create_app(Settings(environment="test"), readiness_check=lambda: False)
    with TestClient(app, base_url="http://localhost") as client:
        assert client.get("/livez").status_code == 200
        response = client.get("/readyz")
        assert response.status_code == 503
        assert response.json() == {"status": "unavailable"}


def test_settings_load_env_file_and_environment_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        'CARETRACE_ALLOWED_HOSTS=["review.local"]\nCARETRACE_MAX_REQUEST_BYTES=128\n'
    )
    monkeypatch.setenv("CARETRACE_MAX_REQUEST_BYTES", "256")
    settings = Settings()
    assert settings.allowed_hosts == ("review.local",)
    assert settings.max_request_bytes == 256


@pytest.mark.parametrize(
    "hosts", [(), ("*",), ("https://example.test",), ("example.test:80",)]
)
def test_rejects_invalid_host_patterns(hosts: tuple[str, ...]) -> None:
    with pytest.raises(ValidationError, match="explicit lowercase"):
        Settings(allowed_hosts=hosts)


@pytest.mark.parametrize(
    "origin",
    [
        "*",
        "https://example.test/",
        "https://person@example.test",
        "http://localhost:65536",
    ],
)
def test_rejects_invalid_origins(origin: str) -> None:
    with pytest.raises(ValidationError):
        Settings(allowed_origins=(origin,))


def test_production_requires_explicit_hosts_and_secure_cross_origin_access() -> None:
    with pytest.raises(ValidationError, match="explicitly configured"):
        Settings(environment="production")
    with pytest.raises(ValidationError, match="HTTPS"):
        Settings(
            environment="production",
            allowed_hosts=("api.example.test",),
            allowed_origins=("http://app.example.test",),
        )

    settings = Settings(
        environment="production",
        allowed_hosts=("api.example.test",),
        allowed_origins=("https://app.example.test",),
    )
    with TestClient(
        create_app(settings), base_url="https://api.example.test"
    ) as client:
        assert client.get("/livez").status_code == 200
        assert client.get("/docs").status_code == 404
        assert client.get("/openapi.json").status_code == 404


@pytest.mark.parametrize("limit", [0, 2**24 + 1])
def test_rejects_invalid_request_size_limit(limit: int) -> None:
    with pytest.raises(ValidationError):
        Settings(max_request_bytes=limit)
