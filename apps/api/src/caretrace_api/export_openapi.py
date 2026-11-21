import json
import sys
from pathlib import Path

from caretrace_api.main import create_app
from caretrace_api.settings import Settings


def export_openapi(destination: Path) -> None:
    settings = Settings(
        environment="test",
        enable_synthetic_ipac=True,
        allowed_hosts=("localhost",),
        allowed_origins=(),
        max_request_bytes=1_048_576,
        database_url=None,
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="\n") as output:
        json.dump(create_app(settings).openapi(), output, indent=2, sort_keys=True)
        output.write("\n")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python -m caretrace_api.export_openapi OUTPUT.json")
    export_openapi(Path(sys.argv[1]))
