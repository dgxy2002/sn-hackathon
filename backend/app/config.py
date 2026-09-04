from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Mapping


DEFAULT_ORIGINS = ("http://localhost:5173", "http://127.0.0.1:5173")


class ConfigurationError(ValueError):
    """Raised when runtime configuration violates a local privacy boundary."""


def _origins(value: str | None) -> tuple[str, ...]:
    origins = DEFAULT_ORIGINS if value is None else tuple(
        origin.strip().rstrip("/") for origin in value.split(",") if origin.strip()
    )
    if not origins:
        raise ConfigurationError("ALLOWED_ORIGINS must contain at least one origin")
    if "*" in origins:
        raise ConfigurationError("ALLOWED_ORIGINS cannot contain a wildcard")
    return origins


def _positive_int(value: str, variable: str) -> int:
    try:
        parsed = int(value)
    except ValueError as error:
        raise ConfigurationError(f"{variable} must be an integer") from error
    if parsed < 1:
        raise ConfigurationError(f"{variable} must be greater than zero")
    return parsed


@dataclass(frozen=True)
class Settings:
    app_env: str
    allowed_origins: tuple[str, ...]
    database_configured: bool
    database_url: str | None = field(repr=False)
    bedrock_configured: bool
    analysis_ttl_hours: int
    document_max_size_bytes: int
    document_max_page_count: int
    document_orphan_ttl_minutes: int
    document_workspace_root: str | None = field(repr=False)

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> "Settings":
        values = os.environ if environ is None else environ
        database_url = values.get("DATABASE_URL", "").strip()
        bedrock_model_id = values.get("BEDROCK_MODEL_ID", "").strip()
        aws_region = (
            values.get("AWS_REGION", "").strip()
            or values.get("AWS_DEFAULT_REGION", "").strip()
        )
        settings = cls(
            app_env=values.get("APP_ENV", "development").strip(),
            allowed_origins=_origins(values.get("ALLOWED_ORIGINS")),
            database_configured=bool(database_url),
            database_url=database_url or None,
            bedrock_configured=bool(bedrock_model_id and aws_region),
            analysis_ttl_hours=_positive_int(
                values.get("ANALYSIS_TTL_HOURS", "24"),
                "ANALYSIS_TTL_HOURS",
            ),
            document_max_size_bytes=_positive_int(
                values.get("DOCUMENT_MAX_SIZE_BYTES", "20971520"),
                "DOCUMENT_MAX_SIZE_BYTES",
            ),
            document_max_page_count=_positive_int(
                values.get("DOCUMENT_MAX_PAGE_COUNT", "100"),
                "DOCUMENT_MAX_PAGE_COUNT",
            ),
            document_orphan_ttl_minutes=_positive_int(
                values.get("DOCUMENT_ORPHAN_TTL_MINUTES", "30"),
                "DOCUMENT_ORPHAN_TTL_MINUTES",
            ),
            document_workspace_root=(
                values.get("DOCUMENT_WORKSPACE_ROOT", "").strip() or None
            ),
        )
        settings.validate()
        return settings

    def validate(self) -> None:
        if not self.app_env:
            raise ConfigurationError("APP_ENV cannot be empty")