from __future__ import annotations

from datetime import date, datetime
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


EvidenceState = Literal["approved", "unverified", "stale", "conflicting", "unknown"]
SourceApproval = Literal["approved", "unverified", "restricted", "rejected"]
FreshnessStatus = Literal["current", "stale", "unknown"]


class EvidenceSearchFilters(StrictModel):
    provider: str | None = Field(default=None, min_length=1, max_length=100)
    category: str | None = Field(default=None, min_length=1, max_length=100)
    product: str | None = Field(default=None, min_length=1, max_length=200)


class EvidenceSearchRequest(StrictModel):
    query: str = Field(min_length=2, max_length=500)
    max_results: int = Field(default=5, ge=1, le=20)
    threshold: float = Field(default=0.05, ge=0, le=1)
    filters: EvidenceSearchFilters = Field(default_factory=EvidenceSearchFilters)


class EvidenceRecord(StrictModel):
    evidence_id: str
    policy_id: str
    provider: str
    product: str
    category: str
    field: str
    section_title: str
    value: str
    source_url: str | None = None
    source_file: str
    source_approval: SourceApproval
    evidence_state: EvidenceState
    freshness_status: FreshnessStatus
    document_as_of_date: date | None = None
    product_effective_date: date | None = None
    retrieved_at: datetime | None = None
    document_version: str | None = None
    synthetic: bool
    extraction_confidence: str | None = None
    similarity: float = Field(ge=0, le=1)
    provenance: dict[str, Any] = Field(default_factory=dict)


class EvidenceSearchResponse(StrictModel):
    contract_version: str = CONTRACT_VERSION
    run_id: str
    mode: CapabilityMode
    query: str
    status: Literal["matched", "no_evidence"]
    match_count: int = Field(ge=0)
    evidence: list[EvidenceRecord]


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
    provider: str | None = None
    product: str | None = None
    excerpt: str | None = None
    source_file: str | None = None
    source_approval: SourceApproval | None = None
    evidence_state: EvidenceState | None = None
    freshness_status: FreshnessStatus | None = None
    document_as_of_date: date | None = None
    product_effective_date: date | None = None
    document_version: str | None = None
    similarity: float | None = Field(default=None, ge=0, le=1)


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