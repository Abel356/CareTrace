from typing import Annotated, Self

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    StringConstraints,
    model_validator,
)


class Contract(BaseModel):
    model_config = ConfigDict(
        extra="forbid", frozen=True, revalidate_instances="always"
    )


class TextSpan(Contract):
    """A half-open Unicode code point range within the original stored text."""

    start: Annotated[int, Field(strict=True, ge=0)]
    end: Annotated[int, Field(strict=True, gt=0)]
    quote: str

    @model_validator(mode="after")
    def validate_quote_length(self) -> Self:
        if not self.quote.strip() or len(self.quote) != self.end - self.start:
            raise ValueError("quote must be nonblank and exactly match the span length")
        return self

    def matches_text(self, text: str) -> bool:
        return self.end <= len(text) and self.quote == text[self.start : self.end]


type Label = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
type Sha256 = Annotated[
    str, StringConstraints(pattern=r"^[a-f0-9]{64}$", min_length=64, max_length=64)
]


def _secure_source_url(value: HttpUrl) -> HttpUrl:
    if (
        value.scheme != "https"
        or value.username is not None
        or value.password is not None
    ):
        raise ValueError("source URL must use HTTPS without credentials")
    return value


type SourceUrl = Annotated[HttpUrl, AfterValidator(_secure_source_url)]
