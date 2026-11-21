from collections.abc import Iterator
from hashlib import sha256

import pytest
from caretrace_api.main import create_app
from caretrace_api.settings import Settings
from fastapi.testclient import TestClient

PATH = "/api/v1/synthetic/ipac/citations"


@pytest.fixture
def client() -> Iterator[TestClient]:
    settings = Settings(environment="test", enable_synthetic_ipac=True)
    with TestClient(create_app(settings), base_url="http://localhost") as client:
        yield client


@pytest.mark.parametrize(
    ("as_of", "version", "binder"),
    [
        ("2026-01-01", "v1", "blue"),
        ("2026-05-31", "v1", "blue"),
        ("2026-06-01", "v2", "green"),
        ("2026-11-21", "v2", "green"),
    ],
)
def test_lookup_uses_the_version_effective_on_the_selected_date(
    client: TestClient, as_of: str, version: str, binder: str
) -> None:
    response = client.get(PATH, params={"q": "CAFÉ", "as_of": as_of})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "matched"
    assert body["version"]["version"] == version
    assert [item["span"]["quote"] for item in body["passages"]] == [
        f"File the café station checklist in the {binder} binder."
    ]


def test_lookup_returns_verifiable_provenance_and_unicode_offsets(
    client: TestClient,
) -> None:
    response = client.get(PATH, params={"q": "checklist", "as_of": "2026-05-31"})
    assert response.status_code == 200
    body = response.json()
    assert body["corpus"] == "synthetic_ipac"
    document, version = body["document"], body["version"]
    assert document["title"] == "Synthetic IPAC training drill"
    assert document["jurisdiction"] == "CA-ON"
    assert document["source_url"] == "https://caretrace.invalid/synthetic/ipac"
    assert version["document_id"] == document["id"]
    assert version["retrieved_at"] == "2026-11-21T00:00:00Z"
    assert (version["effective_from"], version["effective_until"]) == (
        "2026-01-01",
        "2026-06-01",
    )

    prefix = "Drill notes 🧼\n\n"
    original = prefix + "File the café station checklist in the blue binder."
    assert version["original_sha256"] == sha256(original.encode("utf-8")).hexdigest()
    (passage,) = body["passages"]
    assert passage["locator"] == "Drill records"
    assert passage["citation_url"] == f"{version['version_url']}#drill-records"
    span = passage["span"]
    assert span["source_version_id"] == version["id"]
    assert (span["start"], span["end"]) == (len(prefix), len(original))
    assert span["quote"] == original[span["start"] : span["end"]]
