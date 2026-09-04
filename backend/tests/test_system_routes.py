import pytest

from app.config import ConfigurationError, Settings
from app.main import create_app
from tests.support import request


def test_health_reports_local_dependencies_without_secrets() -> None:
    app = create_app(Settings.from_env({"APP_ENV": "test"}))
    response = request(app, "GET", "/health")

    assert response.status_code == 200
    assert response.json() == {
        "service": "before-you-commit-api",
        "version": "0.1.0",
        "status": "healthy",
        "environment": "test",
        "dependencies": {
            "database": {"status": "not_configured", "mode": "off"},
            "document_processing": {"status": "ready", "mode": "local"},
            "bedrock": {"status": "not_configured", "mode": "off"},
        },
    }
    assert "key" not in response.text.lower()


def test_app_exposes_health_and_v2_product_routes_only() -> None:
    app = create_app(Settings.from_env({"APP_ENV": "test"}))
    paths = set(app.openapi()["paths"])

    assert not any(path.startswith("/v1") for path in paths)
    assert "/health" in paths
    assert "/api/v2/analyses" in paths
    assert "/api/v2/analyses/{analysis_id}/documents" in paths
    assert "/api/v2/analyses/{analysis_id}/privacy-scan" in paths
    assert "/api/v2/analyses/{analysis_id}/extract" in paths


def test_configuration_rejects_wildcard_origins() -> None:
    with pytest.raises(ConfigurationError, match="wildcard"):
        Settings.from_env({"ALLOWED_ORIGINS": "*"})


def test_bedrock_remains_optional_and_requires_complete_configuration() -> None:
    assert Settings.from_env({"BEDROCK_MODEL_ID": "model-only"}).bedrock_configured is False
    assert Settings.from_env({"AWS_REGION": "us-east-1"}).bedrock_configured is False

    settings = Settings.from_env(
        {
            "BEDROCK_MODEL_ID": "test.inference-profile",
            "AWS_REGION": "us-east-1",
        }
    )
    assert settings.bedrock_configured is True