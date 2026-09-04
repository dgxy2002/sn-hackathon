from app.config import Settings
from app.main import create_app
from tests.support import request


def test_analysis_session_create_get_and_delete_lifecycle() -> None:
    app = create_app(Settings.from_env({"APP_ENV": "test"}))

    created = request(
        app,
        "POST",
        "/api/v2/analyses",
        json={"purpose": "considering_offer"},
    )

    assert created.status_code == 201
    session = created.json()["analysis"]
    assert session["schema_id"] == "before-you-commit.analysis-session"
    assert session["schema_version"] == "2.0.0"
    assert session["stage"] == "created"
    assert session["model_consent"] == {
        "enabled": False,
        "acknowledged_at": None,
    }

    analysis_id = session["analysis_id"]
    fetched = request(app, "GET", f"/api/v2/analyses/{analysis_id}")
    assert fetched.status_code == 200
    assert fetched.json() == created.json()

    deleted = request(app, "DELETE", f"/api/v2/analyses/{analysis_id}")
    assert deleted.status_code == 204

    missing = request(app, "GET", f"/api/v2/analyses/{analysis_id}")
    assert missing.status_code == 404
    assert missing.json() == {
        "error": {
            "code": "ANALYSIS_NOT_FOUND",
            "message": "The analysis does not exist or has expired.",
            "retryable": False,
            "analysis_id": analysis_id,
            "details": {},
        }
    }


def test_analysis_session_rejects_unacknowledged_model_consent_and_extra_fields() -> None:
    app = create_app(Settings.from_env({"APP_ENV": "test"}))

    consent = request(
        app,
        "POST",
        "/api/v2/analyses",
        json={
            "purpose": "considering_offer",
            "model_consent": {"enabled": True},
        },
    )
    assert consent.status_code == 422

    extra = request(
        app,
        "POST",
        "/api/v2/analyses",
        json={"purpose": "considering_offer", "name": "must-not-be-collected"},
    )
    assert extra.status_code == 422