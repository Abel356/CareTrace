from caretrace_api.main import create_app
from caretrace_api.settings import Settings
from fastapi import Request
from fastapi.testclient import TestClient


def test_requests_require_an_allowed_host() -> None:
    app = create_app(Settings(environment="test", allowed_hosts=("localhost",)))
    with TestClient(app, base_url="http://localhost:8000") as client:
        allowed = client.get("/livez")
        invalid = client.get("/livez", headers={"Host": "other.example.test"})

    assert allowed.status_code == 200
    assert invalid.status_code == 400
    assert invalid.json()["error"]["code"] == "invalid_host"
    assert invalid.json()["request_id"] == invalid.headers["X-Request-ID"]


def test_request_size_limit_checks_declared_and_streamed_bodies() -> None:
    app = create_app(Settings(environment="test", max_request_bytes=8))

    @app.post("/fixture")
    async def size(request: Request) -> int:
        return len(await request.body())

    with TestClient(app, base_url="http://localhost") as client:
        allowed = client.post("/fixture", content=b"12345678")
        declared = client.post("/fixture", content=b"123456789")
        streamed = client.post("/fixture", content=iter((b"12345678", b"9")))
        assert "Content-Length" not in streamed.request.headers

    assert allowed.status_code == 200
    assert allowed.json() == 8
    for rejected in (declared, streamed):
        assert rejected.status_code == 413
        assert rejected.json()["error"]["code"] == "request_too_large"


def test_cors_exposes_request_id_only_to_allowed_origins() -> None:
    origin = "https://app.example.test"
    app = create_app(Settings(environment="test", allowed_origins=(origin,)))
    with TestClient(app, base_url="http://localhost") as client:
        allowed = client.get("/readyz", headers={"Origin": origin})
        rejected = client.get(
            "/readyz", headers={"Origin": "https://other.example.test"}
        )
        preflight = client.options(
            "/readyz",
            headers={"Origin": origin, "Access-Control-Request-Method": "GET"},
        )

    assert allowed.headers["Access-Control-Allow-Origin"] == origin
    assert allowed.headers["Access-Control-Expose-Headers"] == "X-Request-ID"
    assert "Access-Control-Allow-Credentials" not in allowed.headers
    assert "Access-Control-Allow-Origin" not in rejected.headers
    assert preflight.status_code == 200
    assert preflight.headers["Access-Control-Allow-Methods"] == "GET"
