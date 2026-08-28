from app.config import Settings
from app.decision_support import DecisionService
from app.main import create_app
from tests.factories import make_profile
from tests.support import request


def test_no_policy_profile_is_ranked_without_inventing_existing_cover() -> None:
    result = DecisionService().evaluate(make_profile())

    assert result.status == "ranked"
    assert result.gaps[0].existing_amount == 0
    assert result.gaps[1].existing_amount == 0
    assert "No current private policy was declared" in " ".join(result.assumptions)
    assert result.evaluations[0].evidence_ids


def test_missing_critical_value_returns_focused_insufficient_data() -> None:
    result = DecisionService().evaluate(
        make_profile(monthly_income=None, monthly_income_state="unknown")
    )

    assert result.status == "insufficient_data"
    assert result.missing_fields == ["monthly_income"]
    assert result.focused_questions == ["What is your monthly take-home income?"]
    assert result.evaluations == []


def test_hard_constraints_exclude_before_deterministic_ranking() -> None:
    service = DecisionService()
    first = service.evaluate(make_profile(monthly_budget=80.0))
    second = service.evaluate(make_profile(monthly_budget=80.0))

    assert first == second
    excluded = {item.plan_id: item for item in first.evaluations if not item.eligible}
    assert "BUDGET_EXCEEDED" in excluded["synthetic-orchid-income-shield"].exclusions
    assert "BUDGET_EXCEEDED" in excluded["synthetic-meridian-whole-life-plus"].exclusions
    ranked = sorted(
        (item for item in first.evaluations if item.rank), key=lambda item: item.rank or 0
    )
    assert ranked[0].plan_id == "synthetic-lioncity-term-flex"


def test_profile_and_recommendation_routes_preserve_versioned_contracts() -> None:
    app = create_app(Settings.from_env({"APP_ENV": "test"}))
    profile = make_profile()

    created = request(app, "POST", "/v1/profiles", json=profile.model_dump(mode="json"))
    assert created.status_code == 201
    assert created.json()["profile"]["schema_id"] == "covercheck.profile"

    fetched = request(app, "GET", f"/v1/profiles/{profile.profile_id}")
    assert fetched.status_code == 200
    assert fetched.json()["profile"] == created.json()["profile"]

    evaluated = request(
        app,
        "POST",
        "/v1/recommendations/evaluate",
        json={"profile": profile.model_dump(mode="json")},
    )
    assert evaluated.status_code == 200
    payload = evaluated.json()
    assert payload["schema_id"] == "covercheck.recommendation"
    assert payload["status"] == "ranked"
    assert payload["synthetic"] is True


def test_profile_versions_are_immutable_and_missing_profiles_are_typed() -> None:
    app = create_app(Settings.from_env({"APP_ENV": "test"}))
    profile = make_profile()
    request(app, "POST", "/v1/profiles", json=profile.model_dump(mode="json"))

    changed = make_profile(monthly_budget=100.0)
    conflict = request(app, "POST", "/v1/profiles", json=changed.model_dump(mode="json"))
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "PROFILE_VERSION_CONFLICT"

    missing = request(app, "GET", "/v1/profiles/missing")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "PROFILE_NOT_FOUND"