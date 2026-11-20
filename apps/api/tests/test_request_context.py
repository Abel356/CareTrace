import json
import logging
from uuid import UUID

import pytest
from caretrace_api.main import create_app
from caretrace_api.settings import Settings
from fastapi.testclient import TestClient


def test_server_assigns_correlation_ids_and_privacy_headers() -> None:
    with TestClient(
        create_app(Settings(environment="test")), base_url="http://localhost"
    ) as client:
        first = client.get("/livez", headers={"X-Request-ID": "client-supplied"})
        second = client.get("/readyz")

    assert UUID(first.headers["X-Request-ID"]).version == 4
    assert first.headers["X-Request-ID"] != second.headers["X-Request-ID"]
    assert first.headers["Cache-Control"] == "no-store"
    assert first.headers["Referrer-Policy"] == "no-referrer"
    assert first.headers["X-Frame-Options"] == "DENY"
    assert first.headers["X-Content-Type-Options"] == "nosniff"


def test_http_errors_preserve_safe_protocol_headers() -> None:
    with TestClient(
        create_app(Settings(environment="test")), base_url="http://localhost"
    ) as client:
        missing = client.get("/missing")
        wrong_method = client.post("/livez")

    assert missing.json() == {
        "error": {"code": "http_404", "message": "Not Found"},
        "request_id": missing.headers["X-Request-ID"],
    }
    assert wrong_method.status_code == 405
    assert wrong_method.headers["Allow"] == "GET"


def test_validation_response_omits_input() -> None:
    app = create_app(Settings(environment="test"))

    @app.get("/fixture")
    def fixture_route(count: int) -> int:
        return count

    with TestClient(app, base_url="http://localhost") as client:
        response = client.get("/fixture", params={"count": "synthetic-invalid-value"})

    assert response.status_code == 422
    assert response.json() == {
        "error": {"code": "invalid_request", "message": "Request validation failed"},
        "request_id": response.headers["X-Request-ID"],
    }


def test_unhandled_error_and_structured_log_omit_request_and_exception_text(
    caplog: pytest.LogCaptureFixture,
) -> None:
    request_id = UUID(int=1)

    def fail() -> bool:
        raise RuntimeError("synthetic-exception-detail")

    app = create_app(
        Settings(environment="test"),
        readiness_check=fail,
        id_factory=lambda: request_id,
    )
    with (
        caplog.at_level(logging.INFO, logger="uvicorn.error.caretrace"),
        TestClient(app, base_url="http://localhost") as client,
    ):
        response = client.get("/readyz", params={"example": "synthetic-request-value"})

    assert response.status_code == 500
    assert response.headers["X-Request-ID"] == str(request_id)
    assert response.json() == {
        "error": {"code": "internal_error", "message": "Internal server error"},
        "request_id": str(request_id),
    }
    event = json.loads(caplog.records[-1].getMessage())
    assert event.pop("duration_ms") >= 0
    assert event == {
        "event": "http_request",
        "request_id": str(request_id),
        "status_code": 500,
    }
    assert "synthetic-exception-detail" not in caplog.text
    assert "synthetic-request-value" not in caplog.text
