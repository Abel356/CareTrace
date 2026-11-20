import re
from typing import Literal, Self
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError

HOST_LABEL = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CARETRACE_",
        env_file=".env",
        extra="ignore",
        frozen=True,
        hide_input_in_errors=True,
    )

    environment: Literal["development", "test", "production"] = "development"
    allowed_hosts: tuple[str, ...] = ("localhost", "127.0.0.1")
    allowed_origins: tuple[str, ...] = ()
    max_request_bytes: int = Field(default=1_048_576, gt=0, le=16_777_216)
    database_url: SecretStr | None = None

    @field_validator("allowed_hosts")
    @classmethod
    def validate_hosts(cls, hosts: tuple[str, ...]) -> tuple[str, ...]:
        if not hosts or any(
            len(host) > 253
            or any(not HOST_LABEL.fullmatch(label) for label in host.split("."))
            for host in hosts
        ):
            raise ValueError(
                "allowed_hosts must contain explicit lowercase DNS names or IPv4 hosts"
            )
        return hosts

    @field_validator("allowed_origins")
    @classmethod
    def validate_origins(cls, origins: tuple[str, ...]) -> tuple[str, ...]:
        for origin in origins:
            parts = urlsplit(origin)
            if (
                parts.scheme not in {"http", "https"}
                or not parts.hostname
                or parts.path
                or parts.query
                or parts.fragment
                or parts.username is not None
                or "*" in origin
                or any(char.isspace() for char in origin)
                or origin != f"{parts.scheme}://{parts.netloc}"
            ):
                raise ValueError(
                    "allowed_origins must contain exact HTTP or HTTPS origins"
                )
            # Accessing port also validates syntax and numeric range.
            _ = parts.port
        return origins

    @model_validator(mode="after")
    def validate_production(self) -> Self:
        url = self.get_database_url()
        if self.environment == "production":
            if "allowed_hosts" not in self.model_fields_set:
                raise ValueError(
                    "production requires explicitly configured allowed_hosts"
                )
            if any(
                not origin.startswith("https://") for origin in self.allowed_origins
            ):
                raise ValueError("production requires HTTPS allowed_origins")
            if (
                url is None
                or url.drivername != "postgresql+psycopg"
                or not url.host
                or not url.database
            ):
                raise ValueError(
                    "production requires a PostgreSQL server and database name"
                )
        return self

    def get_database_url(self) -> URL | None:
        if self.database_url is None:
            return None
        try:
            url = make_url(self.database_url.get_secret_value())
        except (ArgumentError, ValueError):
            raise ValueError("invalid database URL") from None
        if url.drivername not in {"sqlite+pysqlite", "postgresql+psycopg"}:
            raise ValueError(
                "database URL must use sqlite+pysqlite or postgresql+psycopg"
            )
        return url
