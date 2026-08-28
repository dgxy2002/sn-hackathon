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


def test_live_model_mode_requires_explicit_openrouter_configuration() -> None:
    with pytest.raises(ConfigurationError, match="OPENROUTER"):
        Settings.from_env({"EXTRACTION_MODE": "live"})

    settings = Settings.from_env(
        {
            "EXTRACTION_MODE": "live",
            "OPENROUTER_API_KEY": "test-only-key",
            "OPENROUTER_MODEL": "configured/model-slug",
        }
    )
    assert settings.openrouter_configured is True