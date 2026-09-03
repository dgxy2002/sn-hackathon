import json
from typing import Any

import pytest

from app.decision_support import DecisionService
from app.model_gateway import BedrockExplanationService, ModelInvocationError
from tests.factories import make_profile


class FakeBedrockClient:
    def __init__(self, payload: Any) -> None:
        self.payload = payload
        self.requests: list[dict] = []

    def converse(self, **request):
        self.requests.append(request)
        return {
            "output": {
                "message": {
                    "content": [{"text": json.dumps(self.payload)}],
                }
            },
            "usage": {"inputTokens": 321, "outputTokens": 87},
        }


def test_bedrock_explains_immutable_ranking_and_records_usage() -> None:
    profile = make_profile(goal="Protect dependants")
    recommendation = DecisionService().evaluate(profile)
    top_plan = next(item for item in recommendation.evaluations if item.rank == 1)
    client = FakeBedrockClient(
        {
            "summary": "The first option follows the supplied deterministic result.",
            "plan_reasons": {top_plan.plan_id: "It passed the recorded constraints."},
            "next_steps": ["Review assumptions and policy wording."],
        }
    )
    service = BedrockExplanationService(
        model_id="test.inference-profile",
        region_name="us-east-1",
        timeout_seconds=5,
        client=client,
    )
    before = recommendation.model_dump(mode="json")

    outcome = service.explain(profile, recommendation)

    assert recommendation.model_dump(mode="json") == before
    assert outcome.explanation.provider == "bedrock"
    assert outcome.explanation.recommendation_id == recommendation.recommendation_id
    assert outcome.explanation.plan_reasons == {
        top_plan.plan_id: "It passed the recorded constraints."
    }
    assert outcome.usage.input_tokens == 321
    assert outcome.usage.output_tokens == 87
    request = client.requests[0]
    assert request["modelId"] == "test.inference-profile"
    supplied = json.loads(request["messages"][0]["content"][0]["text"])
    assert supplied["immutable_recommendation"]["recommendation_id"] == (
        recommendation.recommendation_id
    )
    assert supplied["profile_context"]["goal_categories"] == ["family_protection"]


def test_bedrock_rejects_model_authored_plan_ids() -> None:
    profile = make_profile()
    recommendation = DecisionService().evaluate(profile)
    service = BedrockExplanationService(
        model_id="test.inference-profile",
        region_name="us-east-1",
        timeout_seconds=5,
        client=FakeBedrockClient(
            {
                "summary": "An unsupported plan was invented.",
                "plan_reasons": {"invented-plan": "Not in the decision contract."},
                "next_steps": [],
            }
        ),
    )

    with pytest.raises(ModelInvocationError, match="MODEL_OUTPUT_INVALID"):
        service.explain(profile, recommendation)


def test_bedrock_rejects_non_json_object_output() -> None:
    profile = make_profile()
    recommendation = DecisionService().evaluate(profile)
    service = BedrockExplanationService(
        model_id="test.inference-profile",
        region_name="us-east-1",
        timeout_seconds=5,
        client=FakeBedrockClient("not-a-json-object"),
    )

    with pytest.raises(ModelInvocationError, match="MODEL_OUTPUT_INVALID"):
        service.explain(profile, recommendation)