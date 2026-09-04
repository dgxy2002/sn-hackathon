from app.config import Settings
from app.main import create_app
from app.model_gateway import ModelInvocationError
from tests.factories import make_profile
from tests.support import request


def test_fixture_extraction_preserves_regions_and_unknowns_through_review() -> None:
    app = create_app(Settings.from_env({"APP_ENV": "test"}))
    submitted = request(
        app,
        "POST",
        "/v1/extractions",
        json={"fixture_id": "policy-income-001"},
    )
    assert submitted.status_code == 201
    payload = submitted.json()
    assert payload["mode"] == "simulated"
    assert payload["review_required"] is True
    unknown = next(
        field
        for field in payload["fields"]
        if field["field_name"] == "underwriting.occupation_class"
    )
    assert unknown["state"] == "unknown"
    assert unknown["original_value"] is None
    assert unknown["evidence_ids"][0].startswith("policy-income-001:page-1:")

    reviewed_fields = payload["fields"]
    reviewed_fields[0]["reviewed_value"] = reviewed_fields[0]["original_value"]
    reviewed = request(
        app,
        "POST",
        f"/v1/extractions/{payload['extraction_id']}/review",
        json={"expected_version": 1, "fields": reviewed_fields},
    )
    assert reviewed.status_code == 200
    assert reviewed.json()["version"] == 2
    assert reviewed.json()["review_required"] is False


def test_no_policy_invocation_skips_extraction_and_is_replayable() -> None:
    app = create_app(Settings.from_env({"APP_ENV": "test"}))
    invoked = request(
        app,
        "POST",
        "/v1/invocations",
        json={
            "invocation_id": "invocation-no-policy",
            "profile": make_profile().model_dump(mode="json"),
        },
    )
    assert invoked.status_code == 200
    payload = invoked.json()
    assert payload["state"] == "completed"
    assert payload["extraction"] is None
    assert payload["recommendation"]["status"] == "ranked"
    assert payload["explanation"]["provider"] == "fixture"
    assert payload["explanation"]["recommendation_id"] == payload["recommendation"]["recommendation_id"]
    skipped = [event for event in payload["events"] if event["capability"] == "extraction"]
    assert skipped == [
        {
            "schema_id": "covercheck.run-event",
            "contract_version": "1.0.0",
            "run_id": payload["run_id"],
            "sequence": 3,
            "occurred_at": skipped[0]["occurred_at"],
            "state": "extracting",
            "capability": "extraction",
            "outcome": "skipped",
            "safe_details": {"reason": "no_policy_or_unknown_policy_status"},
        }
    ]
    inspected = request(app, "GET", f"/v1/runs/{payload['run_id']}")
    assert inspected.status_code == 200
    assert inspected.json()["run"] == payload


def test_policy_invocation_stops_for_review_and_missing_data_is_terminal() -> None:
    app = create_app(Settings.from_env({"APP_ENV": "test"}))
    policy_profile = make_profile(
        has_current_policy=True,
        existing_death_cover=100000,
        existing_ci_cover=50000,
    )
    review = request(
        app,
        "POST",
        "/v1/invocations",
        json={
            "invocation_id": "invocation-policy",
            "profile": policy_profile.model_dump(mode="json"),
            "fixture_id": "policy-term-001",
        },
    )
    assert review.status_code == 200
    assert review.json()["state"] == "waiting_for_extraction_review"
    assert review.json()["extraction"]["review_required"] is True
    assert review.json()["recommendation"] is None

    missing_profile = make_profile(
        profile_id="profile-missing-income",
        monthly_income=None,
        monthly_income_state="unknown",
    )
    missing = request(
        app,
        "POST",
        "/v1/invocations",
        json={
            "invocation_id": "invocation-missing",
            "profile": missing_profile.model_dump(mode="json"),
        },
    )
    assert missing.status_code == 200
    assert missing.json()["state"] == "insufficient_data"
    assert missing.json()["recommendation"]["missing_fields"] == ["monthly_income"]
    assert missing.json()["explanation"] is None


class FailingExplanationService:
    provider = "bedrock"

    def explain(self, profile, recommendation):
        raise ModelInvocationError("BEDROCK_UNAVAILABLE")


def test_model_failure_preserves_decision_and_returns_typed_failed_run() -> None:
    app = create_app(
        Settings.from_env({"APP_ENV": "test"}),
        explanation_service=FailingExplanationService(),
    )

    invoked = request(
        app,
        "POST",
        "/v1/invocations",
        json={
            "invocation_id": "invocation-bedrock-failure",
            "profile": make_profile().model_dump(mode="json"),
        },
    )

    assert invoked.status_code == 200
    payload = invoked.json()
    assert payload["state"] == "failed"
    assert payload["recommendation"]["status"] == "ranked"
    assert payload["explanation"] is None
    assert payload["metrics"]["terminal_status"] == "failed"
    assert payload["events"][-1]["safe_details"] == {
        "error_code": "BEDROCK_UNAVAILABLE"
    }