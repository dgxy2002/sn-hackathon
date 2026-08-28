from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from .config import CapabilityMode


SERVICE_VERSION = "0.1.0"
API_VERSION = "v1"
CONTRACT_VERSION = "1.0.0"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DependencyStatus(StrictModel):
    status: Literal["ready", "not_configured"]
    mode: CapabilityMode


class HealthResponse(StrictModel):
    service: Literal["covercheck-api"] = "covercheck-api"
    version: str
    status: Literal["healthy"] = "healthy"
    environment: str
    dependencies: dict[str, DependencyStatus]


class CapabilityStatus(StrictModel):
    mode: CapabilityMode
    contract_version: str
    available: bool


class CapabilitiesResponse(StrictModel):
    service_version: str
    api_version: str
    capabilities: dict[str, CapabilityStatus]


class ErrorDetail(StrictModel):
    code: str
    message: str
    retryable: bool
    run_id: str
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorEnvelope(StrictModel):
    error: ErrorDetail


class ConversationCreateRequest(StrictModel):
    active_revision_id: str = Field(min_length=1, max_length=100)


class SuggestedPrompt(StrictModel):
    id: str
    label: str
    message: str


class ConversationResponse(StrictModel):
    conversation_id: str
    active_revision_id: str
    state: Literal["idle"] = "idle"
    mode: Literal["simulated"] = "simulated"
    suggested_prompts: list[SuggestedPrompt]


AgentIntent = Literal[
    "ANSWER_QUESTION",
    "FOCUS_SECTION",
    "FILTER_COMPARISON",
    "PROPOSE_PROFILE_PATCH",
]
AgentTool = Literal[
    "ANSWER_QUESTION",
    "FOCUS_SECTION",
    "FILTER_COMPARISON",
    "PROPOSE_PROFILE_PATCH",
]
SummaryRegion = Literal["comparison", "ranking_reason", "assumptions", "agent"]


class ConversationMessageRequest(StrictModel):
    client_message_id: str = Field(min_length=1, max_length=100)
    active_revision_id: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=1000)


class Citation(StrictModel):
    evidence_id: str
    label: str
    url: str | None = None
    synthetic: bool


class ActionEvent(StrictModel):
    action_id: str
    intent: AgentIntent
    tool: AgentTool
    target: str
    status: Literal["completed", "blocked"]
    evidence_count: int = Field(ge=0)
    confirmation_required: bool
    affected_regions: list[SummaryRegion]
    error_code: str | None = None


class AssistantMessage(StrictModel):
    message_id: str
    content: str
    citations: list[Citation]


class ConversationMessageResponse(StrictModel):
    conversation_id: str
    client_message_id: str
    run_id: str
    state: Literal["completed", "unsupported"]
    mode: Literal["simulated"] = "simulated"
    active_revision_id: str
    assistant_message: AssistantMessage
    actions: list[ActionEvent]