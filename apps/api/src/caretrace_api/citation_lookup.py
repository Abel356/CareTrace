import re
from collections.abc import Iterable
from datetime import date

from caretrace_contracts.sources import CitationSpan, SourceSection, SourceVersion


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


def matching_spans(section: SourceSection, query: str) -> tuple[CitationSpan, ...]:
    keyword = query.strip().casefold()
    if not keyword:
        return ()
    return tuple(
        section.cite(passage.start(), passage.end())
        for passage in re.finditer(r"[^\n]+", section.text)
        if keyword in passage[0].casefold()
    )
