import json
from collections.abc import Iterator
from hashlib import sha256
from pathlib import Path
from shutil import copytree
from typing import Literal

import pytest
from caretrace_api import public_ipac
from caretrace_api.main import create_app
from caretrace_api.public_snapshot import verify_snapshot
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


@pytest.mark.parametrize(
    ("as_of", "revision", "start", "until", "retrieved"),
    [
        (
            "2025-06-27",
            "v28",
            "2025-06-27",
            "2025-07-01",
            "2026-11-22T16:39:05.770674Z",
        ),
        (
            "2025-06-30",
            "v28",
            "2025-06-27",
            "2025-07-01",
            "2026-11-22T16:39:05.770674Z",
        ),
        (
            "2025-07-01",
            "v29",
            "2025-07-01",
            "2025-08-01",
            "2026-11-22T16:39:34.052961Z",
        ),
        (
            "2025-07-31",
            "v29",
            "2025-07-01",
            "2025-08-01",
            "2026-11-22T16:39:34.052961Z",
        ),
    ],
)
def test_public_citation_returns_the_verified_span_at_both_boundaries(
    client: TestClient,
    as_of: str,
    revision: str,
    start: str,
    until: str,
    retrieved: str,
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
    assert version["version"] == revision
    assert (version["effective_from"], version["effective_until"]) == (
        start,
        until,
    )
    assert version["retrieved_at"] == retrieved
    retained = (SNAPSHOT.parent / revision / "source.txt").read_bytes()
    assert version["original_sha256"] == sha256(retained).hexdigest()
    (passage,) = body["passages"]
    assert passage["locator"] == "s. 102 (3)"
    assert passage["citation_url"] == f"{document['source_url']}/{revision}#BK129"
    span = passage["span"]
    sections = retained.decode("utf-8").strip().split("\n\n")[1:]
    section = next(item for item in sections if span["quote"] in item)
    assert (span["start"], span["end"]) == (4, 143)
    assert span["quote"] == section[span["start"] : span["end"]]
    assert span["source_version_id"] == version["id"]


def test_public_citation_finds_the_added_surveillance_passage(
    client: TestClient,
) -> None:
    response = client.get(PATH, params={"q": "surveillance", "as_of": "2025-06-27"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "matched"
    (passage,) = body["passages"]
    assert passage["locator"] == "s. 102 (2)"
    assert passage["citation_url"].endswith("/v28#BK129")
    assert "particular communicable disease" in passage["span"]["quote"]


@pytest.mark.parametrize("as_of", ["2025-06-27", "2025-06-30"])
def test_public_lookup_returns_both_passages_for_a_shared_query(
    client: TestClient, as_of: str
) -> None:
    response = client.get(PATH, params={"q": "protocols", "as_of": as_of})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "matched"
    assert [passage["locator"] for passage in body["passages"]] == [
        "s. 102 (2)",
        "s. 102 (3)",
    ]


@pytest.mark.parametrize(
    ("query", "as_of"),
    [
        ("protocols", "2025-06-26"),
        ("protocols", "2025-08-01"),
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
@pytest.mark.parametrize(
    ("revision", "query", "as_of"),
    [
        ("v28", "protocols", "2025-06-27"),
        ("v28", "surveillance", "2025-06-27"),
        ("v29", "protocols", "2025-07-01"),
        ("v29", "protocols", "2025-06-30"),
    ],
)
def test_public_lookup_abstains_for_unavailable_or_invalid_snapshot(
    client: TestClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    missing: bool,
    revision: str,
    query: str,
    as_of: str,
) -> None:
    if not missing:
        copytree(SNAPSHOT.parent / revision, tmp_path, dirs_exist_ok=True)
        source = tmp_path / "source.txt"
        source.write_bytes(source.read_bytes() + b"\n")
    snapshots = tuple(
        tmp_path if path.name == revision else path for path in public_ipac._SNAPSHOTS
    )
    monkeypatch.setattr(public_ipac, "_SNAPSHOTS", snapshots)

    response = client.get(PATH, params={"q": query, "as_of": as_of})
    assert response.status_code == 200
    assert response.json() == {"status": "insufficient_evidence"}


@pytest.mark.parametrize("query", ["protocols", "surveillance"])
def test_public_lookup_abstains_when_verified_intervals_overlap(
    client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, query: str
) -> None:
    copytree(SNAPSHOT.parent / "v29", tmp_path, dirs_exist_ok=True)
    source = tmp_path / "source.txt"
    retained = source.read_bytes().replace(b"July 1, 2025", b"June 30, 2025", 1)
    source.write_bytes(retained)
    manifest = tmp_path / "manifest.json"
    data = json.loads(manifest.read_bytes())
    data["version"]["effective_from"] = "2025-06-30"
    data["version"]["original_sha256"] = sha256(retained).hexdigest()
    manifest.write_text(json.dumps(data), encoding="utf-8")
    verify_snapshot(tmp_path)
    monkeypatch.setattr(public_ipac, "_SNAPSHOTS", (SNAPSHOT, tmp_path))

    response = client.get(PATH, params={"q": query, "as_of": "2025-06-30"})
    assert response.status_code == 200
    assert response.json() == {"status": "insufficient_evidence"}
