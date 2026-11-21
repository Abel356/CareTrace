from collections.abc import Iterator

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
