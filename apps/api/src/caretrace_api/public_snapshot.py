import argparse
import re
from datetime import date, timedelta
from hashlib import sha256
from pathlib import Path
from uuid import UUID

from caretrace_contracts.common import Contract, Label, SourceUrl
from caretrace_contracts.sources import (
    CitationSpan,
    SourceDocument,
    SourceSection,
    SourceVersion,
)

_MONTHS = "January February March April May June July August September October November December".split()
_DATE = r"([A-Z][a-z]+) ([1-9][0-9]?), ([0-9]{4})"
_HISTORICAL_PERIOD = re.compile(
    rf"Historical version for the period {_DATE} to {_DATE}\."
)


def historical_interval(notice: str) -> tuple[date, date]:
    match = _HISTORICAL_PERIOD.fullmatch(notice)
    if match is None:
        raise ValueError("snapshot has no verified historical period")
    first_month, first_day, first_year, last_month, last_day, last_year = match.groups()
    start = date(int(first_year), _MONTHS.index(first_month) + 1, int(first_day))
    end = date(int(last_year), _MONTHS.index(last_month) + 1, int(last_day))
    if end < start:
        raise ValueError("snapshot historical period is reversed")
    return start, end + timedelta(days=1)


def read_snapshot_text(source: Path, version: SourceVersion) -> str:
    retained = source.read_bytes()
    if sha256(retained).hexdigest() != version.original_sha256:
        raise ValueError("snapshot SHA-256 mismatch")

    notice, separator, section = retained.decode("utf-8").partition("\n\n")
    if not separator or not section.strip():
        raise ValueError("snapshot must contain a historical notice and section text")
    if historical_interval(notice) != (version.effective_from, version.effective_until):
        raise ValueError(
            "snapshot effective interval does not match the historical period"
        )
    return section.removesuffix("\n")


def read_snapshot_sections(source: Path, version: SourceVersion) -> tuple[str, ...]:
    sections = tuple(read_snapshot_text(source, version).split("\n\n"))
    if not all(section.strip() for section in sections):
        raise ValueError("snapshot contains an empty section")
    return sections


class SnapshotPassage(Contract):
    section_id: UUID
    locator: Label
    citation_url: SourceUrl
    citation: CitationSpan


class SnapshotManifest(Contract):
    document: SourceDocument
    version: SourceVersion
    section_id: UUID
    locator: Label
    citation_url: SourceUrl
    citation: CitationSpan
    passages: tuple[SnapshotPassage, ...] = ()

    def listed_passages(self) -> tuple[SnapshotPassage, ...]:
        if self.passages:
            return self.passages
        return (
            SnapshotPassage(
                section_id=self.section_id,
                locator=self.locator,
                citation_url=self.citation_url,
                citation=self.citation,
            ),
        )


def verify_snapshot(directory: Path) -> SnapshotManifest:
    manifest = SnapshotManifest.model_validate_json(
        (directory / "manifest.json").read_bytes()
    )
    if manifest.version.document_id != manifest.document.id:
        raise ValueError("snapshot version refers to a different document")
    passages = manifest.listed_passages()
    sections = read_snapshot_sections(directory / "source.txt", manifest.version)
    if len(sections) != len(passages):
        raise ValueError("snapshot section count does not match its manifest")
    for passage, text in zip(passages, sections, strict=True):
        if str(passage.citation_url).partition("#")[0] != str(
            manifest.version.version_url
        ):
            raise ValueError("snapshot citation URL refers to a different version")
        section = SourceSection(
            id=passage.section_id,
            source_version_id=manifest.version.id,
            locator=passage.locator,
            citation_url=passage.citation_url,
            text=text,
        )
        if not passage.citation.matches(section):
            raise ValueError(
                "snapshot citation does not match its section or identifiers"
            )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify a retained public source snapshot"
    )
    parser.add_argument(
        "directory", type=Path, help="directory with the source and manifest"
    )
    args = parser.parse_args()
    try:
        manifest = verify_snapshot(args.directory)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(
        f"Verified {manifest.document.title}, {manifest.locator} ({manifest.version.version})."
    )


if __name__ == "__main__":
    main()
