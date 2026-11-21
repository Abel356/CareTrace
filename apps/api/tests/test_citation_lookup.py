from collections.abc import Iterator
from datetime import date
from hashlib import sha256
from typing import Literal

import pytest
from caretrace_api import synthetic_ipac
from caretrace_api.main import create_app
from caretrace_api.settings import Settings
from fastapi.testclient import TestClient
from pydantic import SecretStr

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


@pytest.mark.parametrize(
    ("query", "as_of"),
    [
        ("unlisted", "2026-06-01"),
        ("  ", "2026-06-01"),
        ("checklist", "2025-12-31"),
    ],
)
def test_lookup_abstains_without_an_effective_matching_passage(
    client: TestClient, query: str, as_of: str
) -> None:
    response = client.get(PATH, params={"q": query, "as_of": as_of})
    assert response.status_code == 200
    assert response.json() == {"status": "insufficient_evidence"}


@pytest.mark.parametrize(
    "prior_start", [None, date(2026, 1, 1)], ids=["uncertain", "overlap"]
)
def test_lookup_abstains_if_a_second_version_could_apply(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, prior_start: date | None
) -> None:
    (prior, section), current = synthetic_ipac.REVISIONS
    conflicting = prior.model_copy(
        update={"effective_from": prior_start, "effective_until": None}
    )
    monkeypatch.setattr(synthetic_ipac, "REVISIONS", ((conflicting, section), current))

    response = client.get(PATH, params={"q": "green", "as_of": "2026-06-01"})
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
def test_lookup_requires_explicit_local_activation(
    environment: Literal["development", "production"], enabled: bool, expected: int
) -> None:
    settings = Settings(
        environment=environment,
        enable_synthetic_ipac=enabled,
        allowed_hosts=("localhost",),
        database_url=SecretStr("postgresql+psycopg://db.example.test/caretrace"),
    )
    with TestClient(create_app(settings), base_url="http://localhost") as client:
        response = client.get(PATH, params={"q": "checklist", "as_of": "2026-06-01"})
        assert response.status_code == expected
