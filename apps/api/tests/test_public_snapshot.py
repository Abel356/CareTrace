from datetime import date
from pathlib import Path
from shutil import copytree

import pytest
from caretrace_api.public_snapshot import verify_snapshot

_SNAPSHOT = Path(__file__).resolve().parents[3] / "corpus/ontario/220246/v28"


def test_retained_ontario_snapshot() -> None:
    manifest = verify_snapshot(_SNAPSHOT)
    assert manifest.locator == "s. 102 (3)"
    assert str(manifest.citation_url) == (
        "https://www.ontario.ca/laws/regulation/220246/v28#BK129"
    )
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
