from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, HttpUrl, StringConstraints


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


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
