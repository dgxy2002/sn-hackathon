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
            top = ranked[0]
            summary = (
                f"The deterministic rules ranked {top.plan_id} first among the "
                "eligible synthetic options."
            )
            plan_reasons = {
                item.plan_id: ", ".join(item.reason_codes)
                for item in ranked
            }
        else:
            summary = (
                "The deterministic rules did not identify an eligible synthetic "
                "option for the supplied profile."
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
                    "Do not cancel or surrender existing cover based on this POC.",
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
            "immutable_recommendation": recommendation.model_dump(mode="json"),
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
            "You explain a completed educational insurance comparison. The supplied "
            "recommendation is immutable. Never recalculate, add, remove, reorder, or "
            "rescore a plan. Never invent profile values, evidence, benefits, premiums, "
            "eligibility, or suitability. Return JSON only with keys summary, "
            "plan_reasons, and next_steps. plan_reasons must be an object keyed only by "
            "eligible plan_id values from the supplied recommendation. next_steps must "
            "contain at most three cautious educational actions. If affordability is "
            "present, distinguish the 5% adviser-interview comfort marker from the 15% "
            "MoneySense educational upper reference and do not present either as a "
            "guarantee or personal recommendation. Do not advise purchase, "
            "cancellation, surrender, or replacement."
        )