import pytest

from app.config import ConfigurationError, Settings
from app.main import create_app
from tests.support import request


def test_health_reports_fixture_dependencies_without_secrets() -> None:
    app = create_app(Settings.from_env({"APP_ENV": "test"}))
    response = request(app, "GET", "/health")

    assert response.status_code == 200
    assert response.json() == {
        "service": "covercheck-api",
        "version": "0.1.0",
        "status": "healthy",
        "environment": "test",
        "dependencies": {
            "database": {"status": "not_configured", "mode": "synthetic"},
            "object_store": {"status": "not_configured", "mode": "simulated"},
            "openrouter": {"status": "not_configured", "mode": "simulated"},
            "bedrock": {"status": "not_configured", "mode": "simulated"},
        },
    }
    assert "key" not in response.text.lower()


def test_capabilities_publish_modes_and_contract_versions() -> None:
    app = create_app(Settings.from_env({"APP_ENV": "test"}))
    response = request(app, "GET", "/v1/capabilities")

    assert response.status_code == 200
    payload = response.json()
    assert payload["service_version"] == "0.1.0"
    assert payload["api_version"] == "v1"
    assert set(payload["capabilities"]) == {
        "profile",
        "extraction",
        "evidence",
        "recommendation",
        "orchestration",
        "conversation",
    }
    assert payload["capabilities"]["profile"] == {
        "mode": "synthetic",
        "contract_version": "1.0.0",
        "available": True,
    }
    assert payload["capabilities"]["extraction"]["mode"] == "simulated"


def test_configuration_rejects_wildcard_origins() -> None:
    with pytest.raises(ConfigurationError, match="wildcard"):
        Settings.from_env({"ALLOWED_ORIGINS": "*"})


def test_live_extraction_requires_explicit_openrouter_configuration() -> None:
    with pytest.raises(ConfigurationError, match="OPENROUTER"):
        Settings.from_env({"EXTRACTION_MODE": "live"})

    settings = Settings.from_env(
        {
            "EXTRACTION_MODE": "live",
            "DOCUMENT_AI_PROVIDER": "openrouter",
            "OPENROUTER_API_KEY": "test-only-key",
            "OPENROUTER_MODEL": "configured/model-slug",
        }
    )
    assert settings.openrouter_configured is True


def test_live_orchestration_requires_bedrock_model_and_region() -> None:
    with pytest.raises(ConfigurationError, match="BEDROCK_MODEL_ID"):
        Settings.from_env({"ORCHESTRATION_MODE": "live"})

    settings = Settings.from_env(
        {
            "ORCHESTRATION_MODE": "live",
            "LLM_PROVIDER": "bedrock",
            "BEDROCK_MODEL_ID": "test.inference-profile",
            "AWS_REGION": "us-east-1",
        }
    )
    assert settings.bedrock_configured is True
    assert settings.llm_provider == "bedrock"
    assert settings.bedrock_model_id == "test.inference-profile"