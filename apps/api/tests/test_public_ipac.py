from collections.abc import Iterator
from hashlib import sha256
from pathlib import Path

import pytest
from caretrace_api.main import create_app
from caretrace_api.settings import Settings
from fastapi.testclient import TestClient

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
    section = retained.decode("utf-8").split("\n\n", maxsplit=1)[1]
    assert (span["start"], span["end"]) == (4, 143)
    assert span["quote"] == section[span["start"] : span["end"]]
    assert span["source_version_id"] == version["id"]
