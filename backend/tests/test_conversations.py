from app.config import Settings
from app.main import create_app
from tests.support import request


def create_conversation(app) -> dict:
    response = request(
        app,
        "POST",
        "/v1/conversations",
        json={"active_revision_id": "summary-v1"},
    )
    assert response.status_code == 201
    return response.json()


def test_conversation_explains_and_focuses_without_changing_revision() -> None:
    app = create_app(Settings.from_env({"APP_ENV": "test"}))
    conversation = create_conversation(app)

    response = request(
        app,
        "POST",
        f"/v1/conversations/{conversation['conversation_id']}/messages",
        json={
            "client_message_id": "client-message-1",
            "active_revision_id": "summary-v1",
            "message": "Why does LionCity Term Flex rank first?",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["state"] == "completed"
    assert payload["active_revision_id"] == "summary-v1"
    assert payload["actions"] == [
        {
            "action_id": payload["actions"][0]["action_id"],
            "intent": "FOCUS_SECTION",
            "tool": "FOCUS_SECTION",
            "target": "reasoning:ranking",
            "status": "completed",
            "evidence_count": 2,
            "confirmation_required": False,
            "affected_regions": ["ranking_reason", "agent"],
            "error_code": None,
        }
    ]
    assert len(payload["assistant_message"]["citations"]) == 2


def test_duplicate_client_message_replays_identical_response() -> None:
    app = create_app(Settings.from_env({"APP_ENV": "test"}))
    conversation = create_conversation(app)
    path = f"/v1/conversations/{conversation['conversation_id']}/messages"
    body = {
        "client_message_id": "stable-client-message",
        "active_revision_id": "summary-v1",
        "message": "Show only the critical illness option.",
    }

    first = request(app, "POST", path, json=body)
    second = request(app, "POST", path, json=body)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()
    assert first.json()["actions"][0]["target"] == "comparison:critical-illness"


def test_decision_input_change_is_blocked_without_deterministic_rerun() -> None:
    app = create_app(Settings.from_env({"APP_ENV": "test"}))
    conversation = create_conversation(app)

    response = request(
        app,
        "POST",
        f"/v1/conversations/{conversation['conversation_id']}/messages",
        json={
            "client_message_id": "client-message-budget",
            "active_revision_id": "summary-v1",
            "message": "Change my budget to S$120.",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["state"] == "unsupported"
    assert payload["active_revision_id"] == "summary-v1"
    assert payload["actions"][0]["confirmation_required"] is True
    assert payload["actions"][0]["status"] == "blocked"
    assert payload["actions"][0]["error_code"] == "DEPENDENCY_UNAVAILABLE"


def test_stale_revision_returns_typed_conflict() -> None:
    app = create_app(Settings.from_env({"APP_ENV": "test"}))
    conversation = create_conversation(app)

    response = request(
        app,
        "POST",
        f"/v1/conversations/{conversation['conversation_id']}/messages",
        json={
            "client_message_id": "client-message-stale",
            "active_revision_id": "summary-v0",
            "message": "Why does this rank first?",
        },
    )

    assert response.status_code == 409
    assert response.json()["error"] == {
        "code": "REVISION_CONFLICT",
        "message": "The active summary revision changed before this action could run.",
        "retryable": False,
        "run_id": response.json()["error"]["run_id"],
        "details": {"active_revision_id": "summary-v1"},
    }