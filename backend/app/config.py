from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal, Mapping, cast


CapabilityMode = Literal["live", "cached", "synthetic", "simulated"]
VALID_MODES = {"live", "cached", "synthetic", "simulated"}
DEFAULT_ORIGINS = ("http://localhost:5173", "http://127.0.0.1:5173")


class ConfigurationError(ValueError):
    """Raised when runtime configuration would violate a POC boundary."""


def _mode(value: str, variable: str) -> CapabilityMode:
    if value not in VALID_MODES:
        expected = ", ".join(sorted(VALID_MODES))
        raise ConfigurationError(f"{variable} must be one of: {expected}")
    return cast(CapabilityMode, value)


def _origins(value: str | None) -> tuple[str, ...]:
    origins = DEFAULT_ORIGINS if value is None else tuple(
        origin.strip().rstrip("/") for origin in value.split(",") if origin.strip()
    )
    if not origins:
        raise ConfigurationError("ALLOWED_ORIGINS must contain at least one origin")
    if "*" in origins:
        raise ConfigurationError("ALLOWED_ORIGINS cannot contain a wildcard")
    return origins


@dataclass(frozen=True)
class Settings:
    app_env: str
    allowed_origins: tuple[str, ...]
    profile_mode: CapabilityMode
    extraction_mode: CapabilityMode
    evidence_mode: CapabilityMode
    recommendation_mode: CapabilityMode
    orchestration_mode: CapabilityMode
    conversation_mode: CapabilityMode
    database_configured: bool
    object_store_configured: bool
    openrouter_configured: bool

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> "Settings":
        values = os.environ if environ is None else environ
        openrouter_key = values.get("OPENROUTER_API_KEY", "").strip()
        openrouter_model = values.get("OPENROUTER_MODEL", "").strip()

        settings = cls(
            app_env=values.get("APP_ENV", "development").strip(),
            allowed_origins=_origins(values.get("ALLOWED_ORIGINS")),
            profile_mode=_mode(values.get("PROFILE_MODE", "synthetic"), "PROFILE_MODE"),
            extraction_mode=_mode(
                values.get("EXTRACTION_MODE", "simulated"), "EXTRACTION_MODE"
            ),
            evidence_mode=_mode(values.get("EVIDENCE_MODE", "synthetic"), "EVIDENCE_MODE"),
            recommendation_mode=_mode(
                values.get("RECOMMENDATION_MODE", "simulated"), "RECOMMENDATION_MODE"
            ),
            orchestration_mode=_mode(
                values.get("ORCHESTRATION_MODE", "simulated"), "ORCHESTRATION_MODE"
            ),
            conversation_mode=_mode(
                values.get("CONVERSATION_MODE", "simulated"), "CONVERSATION_MODE"
            ),
            database_configured=bool(values.get("DATABASE_URL", "").strip()),
            object_store_configured=bool(
                values.get("OBJECT_STORE_ENDPOINT", "").strip()
                and values.get("OBJECT_STORE_BUCKET", "").strip()
            ),
            openrouter_configured=bool(openrouter_key and openrouter_model),
        )
        settings.validate()
        return settings

    def validate(self) -> None:
        if not self.app_env:
            raise ConfigurationError("APP_ENV cannot be empty")

        openrouter_modes = (
            self.extraction_mode,
            self.orchestration_mode,
            self.conversation_mode,
        )
        if "live" in openrouter_modes and not self.openrouter_configured:
            raise ConfigurationError(
                "Live model capabilities require OPENROUTER_API_KEY and OPENROUTER_MODEL"
            )