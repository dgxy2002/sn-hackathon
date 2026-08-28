from __future__ import annotations

from datetime import date, datetime
from typing import Annotated, Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .config import CapabilityMode


SERVICE_VERSION = "0.1.0"
API_VERSION = "v1"
CONTRACT_VERSION = "1.0.0"
PROFILE_SCHEMA_ID = "covercheck.profile"
EXTRACTION_SCHEMA_ID = "covercheck.extraction"
PLAN_SCHEMA_ID = "covercheck.plan"
RECOMMENDATION_SCHEMA_ID = "covercheck.recommendation"
INVOCATION_SCHEMA_ID = "covercheck.invocation"
RUN_EVENT_SCHEMA_ID = "covercheck.run-event"
RUN_METRICS_SCHEMA_ID = "covercheck.run-metrics"


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


FieldState = Literal["present", "unknown", "not_applicable"]
FieldSource = Literal["user", "extraction", "system", "fixture"]
ProfileValue = TypeVar("ProfileValue")
NonNegativeNumber = Annotated[float, Field(strict=True, ge=0)]
NonNegativeInteger = Annotated[int, Field(strict=True, ge=0)]


class FieldProvenance(StrictModel):
    source: FieldSource
    recorded_at: datetime
    source_ref: str | None = Field(default=None, max_length=200)


class ProfileField(StrictModel, Generic[ProfileValue]):
    state: FieldState
    value: ProfileValue | None = None
    provenance: FieldProvenance

    @model_validator(mode="after")
    def validate_state_value(self) -> "ProfileField[ProfileValue]":
        if self.state == "present" and self.value is None:
            raise ValueError("present profile fields require a value")
        if self.state != "present" and self.value is not None:
            raise ValueError("unknown and not-applicable profile fields cannot have a value")
        return self


class ProfileData(StrictModel):
    life_stage: ProfileField[str]
    employment_status: ProfileField[str]
    goal: ProfileField[str]
    target_amount: ProfileField[NonNegativeNumber]
    target_date: ProfileField[date]
    monthly_income: ProfileField[NonNegativeNumber]
    monthly_expenses: ProfileField[NonNegativeNumber]
    emergency_savings_months: ProfileField[NonNegativeNumber]
    dependant_count: ProfileField[NonNegativeInteger]
    dependant_support_years: ProfileField[NonNegativeInteger]
    liabilities: ProfileField[NonNegativeNumber]
    has_current_policy: ProfileField[bool]
    existing_death_cover: ProfileField[NonNegativeNumber]
    existing_ci_cover: ProfileField[NonNegativeNumber]
    government_cover: ProfileField[list[str]]
    employer_cover: ProfileField[bool]
    monthly_budget: ProfileField[NonNegativeNumber]
    product_preference: ProfileField[str]


class VersionedProfile(StrictModel):
    schema_id: Literal["covercheck.profile"] = PROFILE_SCHEMA_ID
    contract_version: Literal["1.0.0"] = CONTRACT_VERSION
    profile_id: str = Field(min_length=1, max_length=100)
    version: int = Field(ge=1)
    as_of_date: date
    consent: bool
    data: ProfileData


class ProfileResponse(StrictModel):
    contract_version: Literal["1.0.0"] = CONTRACT_VERSION
    run_id: str
    mode: CapabilityMode
    profile: VersionedProfile


class ExtractionField(StrictModel):
    field_name: str = Field(min_length=1, max_length=100)
    original_value: str | None = None
    reviewed_value: str | None = None
    state: FieldState
    confidence: float | None = Field(default=None, ge=0, le=1)
    evidence_ids: list[str] = Field(default_factory=list)


class ExtractionResult(StrictModel):
    schema_id: Literal["covercheck.extraction"] = EXTRACTION_SCHEMA_ID
    contract_version: Literal["1.0.0"] = CONTRACT_VERSION
    extraction_id: str
    version: int = Field(ge=1)
    mode: CapabilityMode
    document_supplied: bool
    review_required: bool
    fields: list[ExtractionField]


class ExtractionSubmitRequest(StrictModel):
    fixture_id: str = Field(min_length=1, max_length=100)


class ExtractionReviewRequest(StrictModel):
    expected_version: int = Field(ge=1)
    fields: list[ExtractionField]


class PlanBenefit(StrictModel):
    benefit_type: str
    amount: NonNegativeNumber
    term_years: NonNegativeInteger


class PlanFixture(StrictModel):
    schema_id: Literal["covercheck.plan"] = PLAN_SCHEMA_ID
    contract_version: Literal["1.0.0"] = CONTRACT_VERSION
    plan_id: str
    catalogue_version: str
    name: str
    category: str
    monthly_premium: NonNegativeNumber
    benefits: list[PlanBenefit]
    preferences: list[str] = Field(default_factory=list)
    synthetic: Literal[True] = True
    evidence_ids: list[str] = Field(default_factory=list)


class GapCalculation(StrictModel):
    gap_type: Literal["death", "critical_illness"]
    target_amount: NonNegativeNumber
    existing_amount: NonNegativeNumber
    gap_amount: NonNegativeNumber
    reason_code: str


class FitComponent(StrictModel):
    component: str
    score: float = Field(ge=0, le=1)
    weight: float = Field(ge=0, le=1)
    reason_code: str


class PlanEvaluation(StrictModel):
    plan_id: str
    eligible: bool
    rank: int | None = Field(default=None, ge=1)
    score: float | None = Field(default=None, ge=0, le=1)
    fit_components: list[FitComponent] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)
    exclusions: list[str] = Field(default_factory=list)
    trade_offs: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)


class RecommendationResult(StrictModel):
    schema_id: Literal["covercheck.recommendation"] = RECOMMENDATION_SCHEMA_ID
    contract_version: Literal["1.0.0"] = CONTRACT_VERSION
    run_id: str
    mode: CapabilityMode
    recommendation_id: str
    profile_id: str
    profile_version: int = Field(ge=1)
    formulation_version: str
    ruleset_version: str
    catalogue_version: str
    status: Literal["ranked", "insufficient_data", "no_eligible_plan"]
    gaps: list[GapCalculation]
    evaluations: list[PlanEvaluation]
    assumptions: list[str]
    missing_fields: list[str]
    focused_questions: list[str]
    synthetic: Literal[True] = True


class RecommendationEvaluationRequest(StrictModel):
    profile: VersionedProfile
    prior_recommendation_id: str | None = None


class InvocationRequest(StrictModel):
    schema_id: Literal["covercheck.invocation"] = INVOCATION_SCHEMA_ID
    contract_version: Literal["1.0.0"] = CONTRACT_VERSION
    invocation_id: str
    profile: VersionedProfile
    extraction_id: str | None = None
    fixture_id: str | None = None
    prior_recommendation_id: str | None = None


class RunEvent(StrictModel):
    schema_id: Literal["covercheck.run-event"] = RUN_EVENT_SCHEMA_ID
    contract_version: Literal["1.0.0"] = CONTRACT_VERSION
    run_id: str
    sequence: int = Field(ge=1)
    occurred_at: datetime
    state: Literal[
        "validating",
        "extracting",
        "waiting_for_extraction_review",
        "completing_profile",
        "retrieving",
        "deciding",
        "explaining",
        "completed",
        "insufficient_data",
        "failed",
    ]
    capability: str
    outcome: Literal["started", "completed", "skipped", "failed"]
    safe_details: dict[str, Any] = Field(default_factory=dict)


class RunMetrics(StrictModel):
    schema_id: Literal["covercheck.run-metrics"] = RUN_METRICS_SCHEMA_ID
    contract_version: Literal["1.0.0"] = CONTRACT_VERSION
    run_id: str
    started_at: datetime
    completed_at: datetime | None = None
    duration_ms: int = Field(ge=0)
    tool_calls: int = Field(ge=0)
    retries: int = Field(ge=0)
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    estimated_cost_usd: float | None = Field(default=None, ge=0)
    terminal_status: Literal["completed", "failed", "blocked"]


class InvocationResponse(StrictModel):
    contract_version: Literal["1.0.0"] = CONTRACT_VERSION
    invocation_id: str
    run_id: str
    mode: CapabilityMode
    state: Literal[
        "waiting_for_extraction_review",
        "completed",
        "insufficient_data",
        "no_eligible_plan",
        "failed",
    ]
    profile: VersionedProfile
    extraction: ExtractionResult | None = None
    recommendation: RecommendationResult | None = None
    events: list[RunEvent]
    metrics: RunMetrics


class RunInspectionResponse(StrictModel):
    run: InvocationResponse


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


ComparisonEligibility = Literal[
    "searchable_only", "comparison_eligible", "ranking_eligible"
]
ComparisonFieldState = Literal["available", "unknown"]


class CanonicalReferences(StrictModel):
    profile_id: str
    profile_version: int = Field(ge=1)
    catalogue_version: str
    recommendation_id: str
    revision_id: str


class EvidenceComparisonRequest(StrictModel):
    product_ids: list[str] = Field(min_length=2, max_length=4)
    canonical_references: CanonicalReferences
    comparison_mode: Literal["configured", "synthetic_fixture"] = "configured"

    @model_validator(mode="after")
    def require_unique_products(self) -> "EvidenceComparisonRequest":
        if len(set(self.product_ids)) != len(self.product_ids):
            raise ValueError("product_ids must be unique")
        return self


class EvidenceComparisonField(StrictModel):
    key: str
    label: str
    state: ComparisonFieldState
    value: str | None = None
    normalized_value: str | float | int | None = None
    unit: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    source_url: str | None = None
    source_approval: SourceApproval | None = None
    evidence_state: EvidenceState | None = None
    freshness_status: FreshnessStatus | None = None
    date_type: Literal[
        "document_as_of_date", "product_effective_date", "retrieved_at", "unknown"
    ] = "unknown"
    date_value: date | datetime | None = None
    document_version: str | None = None


class EvidenceComparisonProduct(StrictModel):
    product_id: str
    provider: str
    product: str
    category: str
    eligibility: ComparisonEligibility
    gate_reasons: list[str]
    synthetic: bool
    fields: list[EvidenceComparisonField]


class EvidenceComparisonResponse(StrictModel):
    contract_version: Literal["1.0.0"] = CONTRACT_VERSION
    run_id: str
    mode: CapabilityMode
    status: Literal["compared"] = "compared"
    label: Literal["Evidence comparison - not a recommendation"] = (
        "Evidence comparison - not a recommendation"
    )
    canonical_references: CanonicalReferences
    products: list[EvidenceComparisonProduct]
    warnings: list[str]


class ConversationCreateRequest(StrictModel):
    active_revision_id: str = Field(min_length=1, max_length=100)
    profile: VersionedProfile | None = None
    recommendation: RecommendationResult | None = None


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
    profile_id: str | None = None
    recommendation_id: str | None = None


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
    status: Literal["pending", "completed", "blocked", "cancelled"]
    evidence_count: int = Field(ge=0)
    confirmation_required: bool
    affected_regions: list[SummaryRegion]
    error_code: str | None = None


class AssistantMessage(StrictModel):
    message_id: str
    content: str
    citations: list[Citation]


PatchField = Literal[
    "monthly_budget",
    "goal",
    "dependant_count",
    "product_preference",
    "has_current_policy",
    "existing_death_cover",
    "existing_ci_cover",
]
PatchValue = str | float | int | bool | None


class ProfilePatch(StrictModel):
    base_profile_version: int = Field(ge=1)
    field_name: PatchField
    old_state: FieldState
    old_value: PatchValue
    proposed_state: FieldState
    proposed_value: PatchValue
    reason: str
    affected_calculations: list[str]


class ChangeProposal(StrictModel):
    proposal_id: str
    conversation_id: str
    base_revision_id: str
    status: Literal["pending", "applied", "cancelled"]
    patch: ProfilePatch


class ValueDelta(StrictModel):
    field_name: str
    old_value: PatchValue
    new_value: PatchValue


class GapDelta(StrictModel):
    gap_type: Literal["death", "critical_illness"]
    old_amount: NonNegativeNumber
    new_amount: NonNegativeNumber


class SummaryDelta(StrictModel):
    changed_inputs: list[ValueDelta]
    changed_gaps: list[GapDelta]
    old_top_plan_id: str | None = None
    new_top_plan_id: str | None = None
    ranking_changed: bool
    affected_regions: list[SummaryRegion]


class SummaryRevision(StrictModel):
    revision_id: str
    parent_revision_id: str | None = None
    created_at: datetime
    cause: Literal["initial", "confirmed_profile_patch", "undo"]
    profile: VersionedProfile
    recommendation: RecommendationResult
    delta: SummaryDelta | None = None


class ProposalDecisionRequest(StrictModel):
    client_request_id: str = Field(min_length=1, max_length=100)
    expected_revision_id: str = Field(min_length=1, max_length=100)


class ProposalDecisionResponse(StrictModel):
    conversation_id: str
    state: Literal["completed", "cancelled"]
    active_revision_id: str
    proposal: ChangeProposal
    revision: SummaryRevision | None = None


class RevisionListResponse(StrictModel):
    conversation_id: str
    active_revision_id: str
    revisions: list[SummaryRevision]


class ReplayEvent(StrictModel):
    sequence: int = Field(ge=1)
    occurred_at: datetime
    event_type: Literal[
        "conversation_created",
        "message_resolved",
        "proposal_created",
        "proposal_confirmed",
        "proposal_cancelled",
        "recommendation_rerun",
        "revision_applied",
        "revision_undone",
    ]
    run_id: str | None = None
    proposal_id: str | None = None
    revision_id: str | None = None
    safe_details: dict[str, Any] = Field(default_factory=dict)


class ReplayResponse(StrictModel):
    conversation_id: str
    active_revision_id: str
    events: list[ReplayEvent]


class UndoRequest(StrictModel):
    client_request_id: str = Field(min_length=1, max_length=100)
    expected_revision_id: str = Field(min_length=1, max_length=100)


class UndoResponse(StrictModel):
    conversation_id: str
    active_revision_id: str
    undone_revision_id: str
    restored_revision: SummaryRevision


class ConversationMessageResponse(StrictModel):
    conversation_id: str
    client_message_id: str
    run_id: str
    state: Literal["waiting_for_confirmation", "completed", "unsupported"]
    mode: Literal["simulated"] = "simulated"
    active_revision_id: str
    assistant_message: AssistantMessage
    actions: list[ActionEvent]
    proposal: ChangeProposal | None = None