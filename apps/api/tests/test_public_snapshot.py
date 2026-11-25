import json
from datetime import date
from pathlib import Path
from shutil import copytree

import pytest
from caretrace_api.public_snapshot import verify_snapshot

_SNAPSHOT = Path(__file__).resolve().parents[3] / "corpus/ontario/220246/v28"


def test_retained_ontario_snapshot() -> None:
    manifest = verify_snapshot(_SNAPSHOT)
    retained = manifest.listed_passages()
    assert [passage.locator for passage in retained] == ["s. 102 (2)", "s. 102 (3)"]
    assert str(retained[-1].citation_url) == (
        "https://www.ontario.ca/laws/regulation/220246/v28#BK129"
    )
    sections = (
        (_SNAPSHOT / "source.txt").read_text(encoding="utf-8").strip().split("\n\n")[1:]
    )
    for passage, section in zip(retained, sections, strict=True):
        span = passage.citation
        assert span.quote == section[span.start : span.end]
    assert manifest.version.is_effective_on(date(2025, 6, 26)) is False
    assert manifest.version.is_effective_on(date(2025, 6, 27)) is True
    assert manifest.version.is_effective_on(date(2025, 6, 30)) is True
    assert manifest.version.is_effective_on(date(2025, 7, 1)) is False


def test_cannot_verify_changed_source_bytes(tmp_path: Path) -> None:
    copytree(_SNAPSHOT, tmp_path, dirs_exist_ok=True)
    source = tmp_path / "source.txt"
    source.write_bytes(source.read_bytes() + b"\n")

    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        verify_snapshot(tmp_path)


def test_cannot_verify_duplicate_passage_identifiers(tmp_path: Path) -> None:
    copytree(_SNAPSHOT, tmp_path, dirs_exist_ok=True)
    manifest = tmp_path / "manifest.json"
    data = json.loads(manifest.read_bytes())
    data["passages"].append(data["passages"][0])
    manifest.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ValueError, match="section IDs must be unique"):
        verify_snapshot(tmp_path)


@pytest.mark.parametrize(
    ("group", "changes", "message"),
    [
        ("citation", {"start": 5, "end": 144}, "citation does not match"),
        (
            "version",
            {"effective_until": "2025-07-02"},
            "effective interval does not match",
        ),
        ("version", {"effective_until": None}, "effective interval does not match"),
    ],
)
def test_cannot_verify_unsupported_manifest_claims(
    tmp_path: Path, group: str, changes: dict[str, str | int | None], message: str
) -> None:
    copytree(_SNAPSHOT, tmp_path, dirs_exist_ok=True)
    manifest = tmp_path / "manifest.json"
    data = json.loads(manifest.read_bytes())
    if group == "citation" and data.get("passages"):
        target = data["passages"][-1]["citation"]
    else:
        target = data[group]
    target.update(changes)
    manifest.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        verify_snapshot(tmp_path)
