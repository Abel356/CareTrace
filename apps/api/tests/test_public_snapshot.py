from datetime import date
from pathlib import Path

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
