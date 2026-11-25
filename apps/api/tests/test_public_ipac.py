from collections.abc import Iterator
from hashlib import sha256
from pathlib import Path
from shutil import copytree
from typing import Literal

import pytest
from caretrace_api import public_ipac
from caretrace_api.main import create_app
from caretrace_api.settings import Settings
from fastapi.testclient import TestClient
from pydantic import SecretStr

PATH = "/api/v1/public/ipac/citations"
SNAPSHOT = Path(__file__).resolve().parents[3] / "corpus/ontario/220246/v28"


@pytest.fixture
def client() -> Iterator[TestClient]:
    settings = Settings(environment="test", enable_public_ipac=True)
    with TestClient(create_app(settings), base_url="http://localhost") as client:
        yield client


@pytest.mark.parametrize("as_of", ["2025-06-27", "2025-06-30"])
def test_public_citation_returns_the_verified_span_at_both_boundaries(
    client: TestClient, as_of: str
) -> None:
    response = client.get(
        PATH, params={"q": "  STANDARDS and PROTOCOLS  ", "as_of": as_of}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "matched"
    assert body["corpus"] == "public_ipac"
    document, version = body["document"], body["version"]
    assert document["jurisdiction"] == "CA-ON"
    assert document["source_url"] == "https://www.ontario.ca/laws/regulation/220246"
    assert version["version"] == "v28"
    assert (version["effective_from"], version["effective_until"]) == (
        "2025-06-27",
        "2025-07-01",
    )
    assert version["retrieved_at"] == "2026-11-22T16:39:05.770674Z"
    retained = (SNAPSHOT / "source.txt").read_bytes()
    assert version["original_sha256"] == sha256(retained).hexdigest()
    (passage,) = body["passages"]
    assert passage["locator"] == "s. 102 (3)"
    assert passage["citation_url"] == f"{document['source_url']}/v28#BK129"
    span = passage["span"]
    sections = retained.decode("utf-8").strip().split("\n\n")[1:]
    section = next(item for item in sections if span["quote"] in item)
    assert (span["start"], span["end"]) == (4, 143)
    assert span["quote"] == section[span["start"] : span["end"]]
    assert span["source_version_id"] == version["id"]


def test_public_citation_finds_the_added_surveillance_passage(
    client: TestClient,
) -> None:
    response = client.get(
        PATH, params={"q": "surveillance", "as_of": "2025-06-27"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "matched"
    (passage,) = body["passages"]
    assert passage["locator"] == "s. 102 (2)"
    assert passage["citation_url"].endswith("/v28#BK129")
    assert "particular communicable disease" in passage["span"]["quote"]


@pytest.mark.parametrize(
    ("query", "as_of"),
    [
        ("protocols", "2025-06-26"),
        ("protocols", "2025-07-01"),
        ("surveillance", "2025-06-26"),
        ("surveillance", "2025-07-01"),
        ("unlisted", "2025-06-27"),
        ("Historical version", "2025-06-27"),
        ("  ", "2025-06-27"),
    ],
)
def test_public_lookup_abstains_outside_the_verified_quote_and_dates(
    client: TestClient, query: str, as_of: str
) -> None:
    response = client.get(PATH, params={"q": query, "as_of": as_of})
    assert response.status_code == 200
    assert response.json() == {"status": "insufficient_evidence"}


@pytest.mark.parametrize(
    ("environment", "enabled", "expected"),
    [
        ("development", False, 404),
        ("development", True, 200),
        ("production", True, 404),
    ],
)
def test_public_lookup_requires_local_opt_in(
    environment: Literal["development", "production"], enabled: bool, expected: int
) -> None:
    settings = Settings(
        environment=environment,
        enable_public_ipac=enabled,
        enable_synthetic_ipac=True,
        allowed_hosts=("localhost",),
        database_url=SecretStr("postgresql+psycopg://db.example.test/caretrace"),
    )
    with TestClient(create_app(settings), base_url="http://localhost") as client:
        response = client.get(PATH, params={"q": "protocols", "as_of": "2025-06-27"})
        assert response.status_code == expected


def test_public_lookup_rejects_writes_and_invalid_dates(client: TestClient) -> None:
    assert client.post(PATH).status_code == 405
    response = client.get(PATH, params={"q": "protocols", "as_of": "invalid-date"})
    assert response.status_code == 422
    assert response.json() == {
        "error": {"code": "invalid_request", "message": "Request validation failed"},
        "request_id": response.headers["X-Request-ID"],
    }


@pytest.mark.parametrize("missing", [True, False], ids=["missing", "changed"])
@pytest.mark.parametrize("query", ["protocols", "surveillance"])
def test_public_lookup_abstains_for_unavailable_or_invalid_snapshot(
    client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    missing: bool, query: str,
) -> None:
    if not missing:
        copytree(SNAPSHOT, tmp_path, dirs_exist_ok=True)
        source = tmp_path / "source.txt"
        source.write_bytes(source.read_bytes() + b"\n")
    monkeypatch.setattr(public_ipac, "_SNAPSHOT", tmp_path)

    response = client.get(PATH, params={"q": query, "as_of": "2025-06-27"})
    assert response.status_code == 200
    assert response.json() == {"status": "insufficient_evidence"}
