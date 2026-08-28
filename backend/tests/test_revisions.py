from app.config import Settings
from app.decision_support import DecisionService
from app.main import create_app
from tests.factories import make_profile
from tests.support import request


def create_contextual_conversation(app) -> dict:
    profile = make_profile()
    recommendation = DecisionService().evaluate(profile)
    response = request(
        app,
        "POST",
        "/v1/conversations",
        json={
            "active_revision_id": "summary-v1",
            "profile": profile.model_dump(mode="json"),
            "recommendation": recommendation.model_dump(mode="json"),
        },
    )
    assert response.status_code == 201
    return response.json()


def propose_budget(app, conversation_id: str, amount: int = 100) -> dict:
    response = request(
        app,
        "POST",
        f"/v1/conversations/{conversation_id}/messages",
        json={
            "client_message_id": f"budget-{amount}",
            "active_revision_id": "summary-v1",
            "message": f"Change my budget to S${amount}.",
        },
    )
    assert response.status_code == 200
    return response.json()


def test_budget_change_requires_confirmation_then_applies_atomic_revision() -> None:
    app = create_app(Settings.from_env({"APP_ENV": "test"}))
    conversation = create_contextual_conversation(app)
    proposed = propose_budget(app, conversation["conversation_id"])

    assert proposed["state"] == "waiting_for_confirmation"
    assert proposed["active_revision_id"] == "summary-v1"
    assert proposed["proposal"]["patch"]["old_value"] == 180
    assert proposed["proposal"]["patch"]["proposed_value"] == 100
    assert proposed["actions"][0]["status"] == "pending"

    proposal_id = proposed["proposal"]["proposal_id"]
    confirmed = request(
        app,
        "POST",
        f"/v1/conversations/{conversation['conversation_id']}/proposals/{proposal_id}/confirm",
        json={"client_request_id": "confirm-1", "expected_revision_id": "summary-v1"},
    )
    assert confirmed.status_code == 200
    payload = confirmed.json()
    assert payload["state"] == "completed"
    assert payload["active_revision_id"] != "summary-v1"
    assert payload["revision"]["profile"]["version"] == 2
    assert payload["revision"]["profile"]["data"]["monthly_budget"]["value"] == 100
    assert payload["revision"]["recommendation"]["profile_version"] == 2
    assert payload["revision"]["delta"]["changed_inputs"] == [
        {"field_name": "monthly_budget", "old_value": 180.0, "new_value": 100.0}
    ]

    replay = request(
        app, "GET", f"/v1/conversations/{conversation['conversation_id']}/replay"
    )
    event_types = [event["event_type"] for event in replay.json()["events"]]
    assert event_types[-3:] == [
        "proposal_confirmed",
        "recommendation_rerun",
        "revision_applied",
    ]


def test_cancel_and_stale_confirmation_never_change_canonical_revision() -> None:
    app = create_app(Settings.from_env({"APP_ENV": "test"}))
    conversation = create_contextual_conversation(app)
    proposed = propose_budget(app, conversation["conversation_id"], 120)
    proposal_id = proposed["proposal"]["proposal_id"]

    stale = request(
        app,
        "POST",
        f"/v1/conversations/{conversation['conversation_id']}/proposals/{proposal_id}/confirm",
        json={"client_request_id": "stale", "expected_revision_id": "summary-v0"},
    )
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "REVISION_CONFLICT"

    cancelled = request(
        app,
        "POST",
        f"/v1/conversations/{conversation['conversation_id']}/proposals/{proposal_id}/cancel",
        json={"client_request_id": "cancel-1", "expected_revision_id": "summary-v1"},
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["state"] == "cancelled"
    assert cancelled.json()["active_revision_id"] == "summary-v1"
    assert cancelled.json()["revision"] is None


def test_confirm_is_idempotent_and_undo_restores_coherent_prior_revision() -> None:
    app = create_app(Settings.from_env({"APP_ENV": "test"}))
    conversation = create_contextual_conversation(app)
    proposed = propose_budget(app, conversation["conversation_id"], 90)
    path = (
        f"/v1/conversations/{conversation['conversation_id']}/proposals/"
        f"{proposed['proposal']['proposal_id']}/confirm"
    )
    body = {"client_request_id": "confirm-stable", "expected_revision_id": "summary-v1"}
    first = request(app, "POST", path, json=body)
    second = request(app, "POST", path, json=body)
    assert first.json() == second.json()

    active_revision_id = first.json()["active_revision_id"]
    undone = request(
        app,
        "POST",
        f"/v1/conversations/{conversation['conversation_id']}/undo",
        json={"client_request_id": "undo-1", "expected_revision_id": active_revision_id},
    )
    assert undone.status_code == 200
    payload = undone.json()
    assert payload["active_revision_id"] == "summary-v1"
    assert payload["restored_revision"]["profile"]["version"] == 1
    assert payload["restored_revision"]["recommendation"]["profile_version"] == 1

    revisions = request(
        app, "GET", f"/v1/conversations/{conversation['conversation_id']}/revisions"
    )
    assert revisions.status_code == 200
    assert revisions.json()["active_revision_id"] == "summary-v1"
    assert len(revisions.json()["revisions"]) == 2