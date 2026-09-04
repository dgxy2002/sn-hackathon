from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Literal, Mapping, cast


CapabilityMode = Literal["live", "cached", "synthetic", "simulated"]
VALID_MODES = {"live", "cached", "synthetic", "simulated"}
ModelProvider = Literal["fixture", "openrouter", "bedrock"]
VALID_MODEL_PROVIDERS = {"fixture", "openrouter", "bedrock"}
DEFAULT_ORIGINS = ("http://localhost:5173", "http://127.0.0.1:5173")


class ConfigurationError(ValueError):
    """Raised when runtime configuration would violate a POC boundary."""


def _mode(value: str, variable: str) -> CapabilityMode:
    if value not in VALID_MODES:
        expected = ", ".join(sorted(VALID_MODES))
        raise ConfigurationError(f"{variable} must be one of: {expected}")
    return cast(CapabilityMode, value)


def _provider(value: str, variable: str) -> ModelProvider:
    if value not in VALID_MODEL_PROVIDERS:
        expected = ", ".join(sorted(VALID_MODEL_PROVIDERS))
        raise ConfigurationError(f"{variable} must be one of: {expected}")
    return cast(ModelProvider, value)


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
    profile_mode: CapabilityMode
    extraction_mode: CapabilityMode
    evidence_mode: CapabilityMode
    recommendation_mode: CapabilityMode
    orchestration_mode: CapabilityMode
    conversation_mode: CapabilityMode
    database_configured: bool
    database_url: str | None = field(repr=False)
    object_store_configured: bool
    openrouter_configured: bool
    bedrock_configured: bool
    llm_provider: ModelProvider
    document_ai_provider: ModelProvider
    bedrock_model_id: str | None
    bedrock_embedding_model_id: str
    bedrock_embedding_dimensions: int
    aws_region: str | None
    supabase_url: str | None = field(repr=False)
    supabase_service_role_key: str | None = field(repr=False)
    evidence_corpus_path: str | None
    evidence_max_age_days: int
    dependency_timeout_seconds: int

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> "Settings":
        values = os.environ if environ is None else environ
        openrouter_key = values.get("OPENROUTER_API_KEY", "").strip()
        openrouter_model = values.get("OPENROUTER_MODEL", "").strip()
        bedrock_model_id = values.get("BEDROCK_MODEL_ID", "").strip()
        bedrock_embedding_model_id = values.get(
            "BEDROCK_EMBEDDING_MODEL_ID", "amazon.titan-embed-text-v2:0"
        ).strip()
        aws_region = (
            values.get("AWS_REGION", "").strip()
            or values.get("AWS_DEFAULT_REGION", "").strip()
        )
        supabase_url = values.get("SUPABASE_URL", "").strip()
        supabase_service_role_key = values.get(
            "SUPABASE_SERVICE_ROLE_KEY", ""
        ).strip()
        database_url = values.get("DATABASE_URL", "").strip()

        settings = cls(
            app_env=values.get("APP_ENV", "development").strip(),
            allowed_origins=_origins(values.get("ALLOWED_ORIGINS")),
            profile_mode=_mode(values.get("PROFILE_MODE", "synthetic"), "PROFILE_MODE"),
            extraction_mode=_mode(
                values.get("EXTRACTION_MODE", "simulated"), "EXTRACTION_MODE"
            ),
            evidence_mode=_mode(values.get("EVIDENCE_MODE", "cached"), "EVIDENCE_MODE"),
            recommendation_mode=_mode(
                values.get("RECOMMENDATION_MODE", "simulated"), "RECOMMENDATION_MODE"
            ),
            orchestration_mode=_mode(
                values.get("ORCHESTRATION_MODE", "simulated"), "ORCHESTRATION_MODE"
            ),
            conversation_mode=_mode(
                values.get("CONVERSATION_MODE", "simulated"), "CONVERSATION_MODE"
            ),
            database_configured=bool(
                database_url or (supabase_url and supabase_service_role_key)
            ),
            database_url=database_url or None,
            object_store_configured=bool(
                values.get("OBJECT_STORE_ENDPOINT", "").strip()
                and values.get("OBJECT_STORE_BUCKET", "").strip()
            ),
            openrouter_configured=bool(openrouter_key and openrouter_model),
            bedrock_configured=bool(bedrock_model_id and aws_region),
            llm_provider=_provider(
                values.get("LLM_PROVIDER", "bedrock"), "LLM_PROVIDER"
            ),
            document_ai_provider=_provider(
                values.get("DOCUMENT_AI_PROVIDER", "fixture"),
                "DOCUMENT_AI_PROVIDER",
            ),
            bedrock_model_id=bedrock_model_id or None,
            bedrock_embedding_model_id=bedrock_embedding_model_id,
            bedrock_embedding_dimensions=_positive_int(
                values.get("BEDROCK_EMBEDDING_DIMENSIONS", "1024"),
                "BEDROCK_EMBEDDING_DIMENSIONS",
            ),
            aws_region=aws_region or None,
            supabase_url=supabase_url or None,
            supabase_service_role_key=supabase_service_role_key or None,
            evidence_corpus_path=values.get("EVIDENCE_CORPUS_PATH", "").strip() or None,
            evidence_max_age_days=_positive_int(
                values.get("EVIDENCE_MAX_AGE_DAYS", "365"),
                "EVIDENCE_MAX_AGE_DAYS",
            ),
            dependency_timeout_seconds=_positive_int(
                values.get("DEPENDENCY_TIMEOUT_SECONDS", "20"),
                "DEPENDENCY_TIMEOUT_SECONDS",
            ),
        )
        settings.validate()
        return settings

    def validate(self) -> None:
        if not self.app_env:
            raise ConfigurationError("APP_ENV cannot be empty")

        if self.extraction_mode == "live" and (
            self.document_ai_provider != "openrouter"
            or not self.openrouter_configured
        ):
            raise ConfigurationError(
                "Live extraction requires DOCUMENT_AI_PROVIDER=openrouter, "
                "OPENROUTER_API_KEY, and OPENROUTER_MODEL"
            )
        if (
            self.orchestration_mode == "live"
            or self.conversation_mode == "live"
        ) and (self.llm_provider != "bedrock" or not self.bedrock_configured):
            raise ConfigurationError(
                "Live orchestration requires LLM_PROVIDER=bedrock, "
                "BEDROCK_MODEL_ID, and AWS_REGION"
            )
        if self.evidence_mode == "live" and not (
            self.supabase_url
            and self.supabase_service_role_key
            and self.aws_region
            and self.bedrock_embedding_model_id
        ):
            raise ConfigurationError(
                "Live evidence requires SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, "
                "AWS_REGION, and BEDROCK_EMBEDDING_MODEL_ID"
            )
        if self.bedrock_embedding_dimensions not in {256, 512, 1024}:
            raise ConfigurationError(
                "BEDROCK_EMBEDDING_DIMENSIONS must be one of: 256, 512, 1024"
            )
