from uuid import NAMESPACE_URL, uuid5

from caretrace_contracts.sources import Jurisdiction, SourceDocument, SourceKind
from pydantic import HttpUrl

_DOCUMENT_URL = "https://caretrace.invalid/synthetic/ipac"
DOCUMENT = SourceDocument(
    id=uuid5(NAMESPACE_URL, _DOCUMENT_URL),
    title="Synthetic IPAC training drill",
    jurisdiction=Jurisdiction.ONTARIO,
    kind=SourceKind.REGULATION,
    source_url=HttpUrl(_DOCUMENT_URL),
)
