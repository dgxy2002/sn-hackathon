from __future__ import annotations

from dataclasses import dataclass
import json
from time import monotonic
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .contracts import GroundedExplanation, RecommendationResult, VersionedProfile
from .personalization import build_context


PROMPT_VERSION = "bedrock-grounded-explanation-v1"
FIXTURE_MODEL_ID = "fixture-grounded-explanation-v1"


class ModelInvocationError(RuntimeError):
    """A safe, typed model failure that does not expose provider internals."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class ModelUsage:
    input_tokens: int | None = None
    output_tokens: int | None = None
    duration_ms: int = 0


@dataclass(frozen=True)
class ExplanationOutcome:
    explanation: GroundedExplanation
    usage: ModelUsage


class ExplanationService(Protocol):
    provider: str

    def explain(
        self,
        profile: VersionedProfile,
        recommendation: RecommendationResult,
    ) -> ExplanationOutcome: ...


class _ExplanationDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1, max_length=1200)
    plan_reasons: dict[str, str] = Field(default_factory=dict)
    next_steps: list[str] = Field(default_factory=list, max_length=3)


class FixtureExplanationService:
    provider = "fixture"

    def explain(
        self,
        profile: VersionedProfile,
        recommendation: RecommendationResult,
    ) -> ExplanationOutcome:
        ranked = sorted(
            (item for item in recommendation.evaluations if item.rank is not None),
            key=lambda item: item.rank or 0,
        )
        if ranked:
            gap_summary = ", ".join(
                f"{gap.gap_type.replace('_', ' ')} S${gap.gap_amount:,.0f}"
                for gap in recommendation.gaps
            )
            summary = (
                f"The calculation identified these planning gaps: {gap_summary}. "
                "Review the assumptions and verify current policy benefits before acting."
            )
            plan_reasons = {
                item.plan_id: ", ".join(item.reason_codes)
                for item in ranked
            }
        else:
            summary = (
                "No illustrative cover structure fits the monthly ceiling supplied. "
                "Review the ceiling or discuss a staged approach with a licensed adviser."
            )
            plan_reasons = {}
        return ExplanationOutcome(
            explanation=GroundedExplanation(
                mode="simulated",
                provider="fixture",
                model_id=FIXTURE_MODEL_ID,
                prompt_version=PROMPT_VERSION,
                recommendation_id=recommendation.recommendation_id,
                summary=summary,
                plan_reasons=plan_reasons,
                next_steps=[
                    "Review the recorded assumptions and evidence before acting.",
                    "Do not cancel or surrender existing cover from this calculation alone.",
                ],
            ),
            usage=ModelUsage(),
        )


class BedrockExplanationService:
    """Explain an immutable E07 result through the Bedrock Converse API."""

    provider = "bedrock"

    def __init__(
        self,
        model_id: str,
        region_name: str,
        timeout_seconds: int,
        client: Any | None = None,
    ) -> None:
        self.model_id = model_id
        self.region_name = region_name
        self.timeout_seconds = timeout_seconds
        self._client = client

    def explain(
        self,
        profile: VersionedProfile,
        recommendation: RecommendationResult,
    ) -> ExplanationOutcome:
        started = monotonic()
        allowed_plan_ids = {
            item.plan_id
            for item in recommendation.evaluations
            if item.eligible
        }
        payload = {
            "profile_context": build_context(profile),
            "immutable_recommendation": {
                "recommendation_id": recommendation.recommendation_id,
                "status": recommendation.status,
                "gaps": [gap.model_dump(mode="json") for gap in recommendation.gaps],
                "assumptions": recommendation.assumptions,
                "stated_monthly_ceiling": (
                    profile.data.monthly_budget.value
                    if profile.data.monthly_budget.state == "present"
                    else None
                ),
                "ceiling_income_share": (
                    recommendation.affordability.budget_income_share
                    if recommendation.affordability is not None
                    else None
                ),
            },
        }
        try:
            response = self._bedrock_client().converse(
                modelId=self.model_id,
                system=[{"text": self._system_prompt()}],
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "text": json.dumps(
                                    payload,
                                    sort_keys=True,
                                    separators=(",", ":"),
                                )
                            }
                        ],
                    }
                ],
                inferenceConfig={"maxTokens": 1200, "temperature": 0.1},
            )
            draft = self._parse_response(response)
            unexpected_ids = set(draft.plan_reasons) - allowed_plan_ids
            if unexpected_ids:
                raise ModelInvocationError("MODEL_OUTPUT_INVALID")
            usage = response.get("usage", {})
            return ExplanationOutcome(
                explanation=GroundedExplanation(
                    mode="live",
                    provider="bedrock",
                    model_id=self.model_id,
                    prompt_version=PROMPT_VERSION,
                    recommendation_id=recommendation.recommendation_id,
                    summary=draft.summary,
                    plan_reasons=draft.plan_reasons,
                    next_steps=draft.next_steps,
                ),
                usage=ModelUsage(
                    input_tokens=self._optional_int(usage.get("inputTokens")),
                    output_tokens=self._optional_int(usage.get("outputTokens")),
                    duration_ms=max(0, round((monotonic() - started) * 1000)),
                ),
            )
        except ModelInvocationError:
            raise
        except Exception as error:
            raise ModelInvocationError("BEDROCK_UNAVAILABLE") from error

    def _bedrock_client(self) -> Any:
        if self._client is None:
            import boto3
            from botocore.config import Config

            self._client = boto3.client(
                "bedrock-runtime",
                region_name=self.region_name,
                config=Config(
                    connect_timeout=self.timeout_seconds,
                    read_timeout=self.timeout_seconds,
                    retries={"max_attempts": 2, "mode": "standard"},
                ),
            )
        return self._client

    @staticmethod
    def _parse_response(response: dict[str, Any]) -> _ExplanationDraft:
        try:
            blocks = response["output"]["message"]["content"]
            text = "".join(
                block["text"] for block in blocks if isinstance(block.get("text"), str)
            ).strip()
            if text.startswith("```json") and text.endswith("```"):
                text = text[7:-3].strip()
            elif text.startswith("```") and text.endswith("```"):
                text = text[3:-3].strip()
            return _ExplanationDraft.model_validate(json.loads(text))
        except (KeyError, TypeError, json.JSONDecodeError, ValidationError) as error:
            raise ModelInvocationError("MODEL_OUTPUT_INVALID") from error

    @staticmethod
    def _optional_int(value: Any) -> int | None:
        return value if isinstance(value, int) and value >= 0 else None

    @staticmethod
    def _system_prompt() -> str:
        return (
            "You explain a completed educational insurance coverage calculation. The supplied "
            "recommendation is immutable. Never recalculate or invent profile values, "
            "evidence, benefits, premiums, eligibility, products, or suitability. Return "
            "JSON only with keys summary, plan_reasons, and next_steps. plan_reasons must "
            "be an empty object because no products are supplied. next_steps must "
            "contain at most three cautious educational actions. The customer-facing summary "
            "must explain only the calculated coverage gaps, stated monthly ceiling, and key "
            "assumptions in plain English. Do not mention plans, options, products, providers, "
            "availability, eligibility, internal IDs, scores, models, or fictional names. Do "
            "not use the words synthetic, fixture, demo, prototype, ruleset, catalogue, "
            "ranking, ranked, fit score, or deterministic. Treat stated_monthly_ceiling only "
            "as the user's exploration limit and ceiling_income_share only as its percentage "
            "of monthly income; never call either a premium, current spending, affordability "
            "position, recommendation, or guarantee. Do not advise purchase, "
            "cancellation, surrender, or replacement."
        )