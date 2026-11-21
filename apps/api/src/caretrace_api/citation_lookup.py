from collections.abc import Iterable
from datetime import date

from caretrace_contracts.sources import SourceVersion


def resolve_version(
    versions: Iterable[SourceVersion], as_of: date
) -> SourceVersion | None:
    effective = []
    for version in versions:
        status = version.is_effective_on(as_of)
        if status is None:
            return None
        if status:
            effective.append(version)
    return effective[0] if len(effective) == 1 else None
