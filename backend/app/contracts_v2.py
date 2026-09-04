from __future__ import annotations

from datetime import date, datetime
from typing import Annotated, Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator


API_VERSION = "v2"
CONTRACT_VERSION = "2.0.0"

ValueState = Literal["present", "absent", "unknown", "unreadable", "not_applicable"]
EvidencePlane = Literal["private_bundle", "public_guidance"]
AnalysisPurpose = Literal["considering_offer", "reviewing_issued_policy"]
AnalysisStage = Literal[
    "created",
    "uploading",
    "privacy_scan",
    "privacy_review",
    "extracting",
    "term_review",
    "ready",
    "running",
    "review_required",
    "completed",
    "failed",
    "deleted",
]
DocumentType = Literal[
    "policy_illustration",
    "product_summary",
    "product_highlights_sheet",
    "quotation",
    "cover_page",
    "policy_schedule",
    "policy_wording",
    "bundled_product_disclosure",
    "direct_purchase_fact_sheet",
    "unknown",
]
DocumentState = Literal[
    "uploaded",
    "privacy_review",
    "ready",
    "unreadable",
    "rejected",
    "deleted",
]
ParserPath = Literal["text", "ocr", "mixed"]
PrivacyCategory = Literal[
    "name",
    "national_id",
    "contact",
    "address",
    "policy_number",
    "account_detail",
    "signature",
    "health_information",
]
PrivacyAction = Literal["redact", "exclude", "keep", "review"]
ClaimOrigin = Literal["user", "document"]
ClaimStatus = Literal[
    "supported",
    "supported_with_conditions",
    "contradicted",
    "not_found",
    "external_confirmation_required",
    "unreadable",
]
EvidenceCompleteness = Literal[
    "blocked", "review_required", "complete_for_supplied_bundle"
]
TaskState = Literal[
    "pending",
    "ready",
    "running",
    "succeeded",
    "review_required",
    "blocked",
    "failed",
    "cancelled",
]
Confidence = Annotated[float, Field(strict=True, ge=0.0, le=1.0)]
PositiveInt = Annotated[int, Field(strict=True, gt=0)]
NonNegativeInt = Annotated[int, Field(strict=True, ge=0)]
ModelValue = TypeVar("ModelValue")


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class StatefulValue(StrictModel, Generic[ModelValue]):
    state: ValueState
    value: ModelValue | None = None

    @model_validator(mode="after")
    def validate_state_value(self) -> StatefulValue[ModelValue]:
        if self.state == "present" and self.value is None:
            raise ValueError("present values require a value")
        if self.state != "present" and self.value is not None:
            raise ValueError(f"{self.state} values cannot have a value")
        return self


class ModelConsent(StrictModel):
    enabled: bool = False
    acknowledged_at: datetime | None = None

    @model_validator(mode="after")
    def require_acknowledgement(self) -> ModelConsent:
        if self.enabled and self.acknowledged_at is None:
            raise ValueError("enabled model processing requires acknowledged_at")
        return self


class AnalysisSession(StrictModel):
    schema_id: Literal["before-you-commit.analysis-session"] = (
        "before-you-commit.analysis-session"
    )
    schema_version: Literal[CONTRACT_VERSION] = CONTRACT_VERSION
    analysis_id: str = Field(min_length=1)
    purpose: AnalysisPurpose
    stage: AnalysisStage = "created"
    decision_date: date | None = None
    model_consent: ModelConsent = Field(default_factory=ModelConsent)
    created_at: datetime
    expires_at: datetime
    input_hashes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_lifecycle_dates(self) -> AnalysisSession:
        if self.expires_at <= self.created_at:
            raise ValueError("expires_at must be later than created_at")
        return self


class UploadedDocument(StrictModel):
    schema_id: Literal["before-you-commit.uploaded-document"] = (
        "before-you-commit.uploaded-document"
    )
    schema_version: Literal[CONTRACT_VERSION] = CONTRACT_VERSION
    document_id: str = Field(min_length=1)
    analysis_id: str = Field(min_length=1)
    document_type: DocumentType = "unknown"
    state: DocumentState = "uploaded"
    content_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    media_type: Literal["application/pdf"] = "application/pdf"
    parser_path: ParserPath
    page_count: PositiveInt
    size_bytes: PositiveInt
    uploaded_at: datetime
    transient_artifacts_deleted: bool = False


class DocumentResponse(StrictModel):
    document: UploadedDocument


class DocumentListResponse(StrictModel):
    documents: list[UploadedDocument]


class SourceRegion(StrictModel):
    page: PositiveInt
    x: Annotated[float, Field(strict=True, ge=0.0, le=1.0)] | None = None
    y: Annotated[float, Field(strict=True, ge=0.0, le=1.0)] | None = None
    width: Annotated[float, Field(strict=True, gt=0.0, le=1.0)] | None = None
    height: Annotated[float, Field(strict=True, gt=0.0, le=1.0)] | None = None

    @model_validator(mode="after")
    def require_complete_box(self) -> SourceRegion:
        box = (self.x, self.y, self.width, self.height)
        if any(value is not None for value in box) and not all(
            value is not None for value in box
        ):
            raise ValueError("bounding box coordinates must be provided together")
        return self


class DocumentSpan(StrictModel):
    schema_id: Literal["before-you-commit.document-span"] = (
        "before-you-commit.document-span"
    )
    schema_version: Literal[CONTRACT_VERSION] = CONTRACT_VERSION
    span_id: str = Field(min_length=1)
    analysis_id: str = Field(min_length=1)
    document_id: str = Field(min_length=1)
    evidence_plane: Literal["private_bundle"] = "private_bundle"
    region: SourceRegion
    redacted_text: str = Field(min_length=1, max_length=2000)
    content_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    parser_version: str = Field(min_length=1)


class PrivacyFinding(StrictModel):
    schema_id: Literal["before-you-commit.privacy-finding"] = (
        "before-you-commit.privacy-finding"
    )
    schema_version: Literal[CONTRACT_VERSION] = CONTRACT_VERSION
    finding_id: str = Field(min_length=1)
    document_id: str = Field(min_length=1)
    category: PrivacyCategory
    region: SourceRegion
    action: PrivacyAction
    confidence: Confidence
    confirmed: bool = False




class PrivacyFindingDecision(StrictModel):
    finding_id: str = Field(min_length=1)
    action: PrivacyAction
    confirmed: Literal[True] = True


class PrivacyReviewRequest(StrictModel):
    decisions: Annotated[list[PrivacyFindingDecision], Field(min_length=1)]

    @model_validator(mode="after")
    def require_unique_findings(self) -> PrivacyReviewRequest:
        finding_ids = [decision.finding_id for decision in self.decisions]
        if len(finding_ids) != len(set(finding_ids)):
            raise ValueError("privacy review decisions must have unique finding IDs")
        return self

class PrivacyScanResponse(StrictModel):
    findings: list[PrivacyFinding]


class MaterialTerm(StrictModel):
    schema_id: Literal["before-you-commit.material-term"] = (
        "before-you-commit.material-term"
    )
    schema_version: Literal[CONTRACT_VERSION] = CONTRACT_VERSION
    term_id: str = Field(min_length=1)
    analysis_id: str = Field(min_length=1)
    taxonomy_key: str = Field(min_length=1)
    value: StatefulValue[Any]
    confidence: Confidence
    source_span_ids: list[str] = Field(default_factory=list)
    extraction_method: Literal["deterministic", "model_candidate", "user"]
    confirmed: bool = False

    @model_validator(mode="after")
    def require_source_for_present_term(self) -> MaterialTerm:
        if self.value.state == "present" and not self.source_span_ids:
            raise ValueError("present material terms require a source span")
        return self




class MaterialTermDecision(StrictModel):
    term_id: str = Field(min_length=1)
    value: StatefulValue[Any]
    source_span_ids: list[str] = Field(default_factory=list)
    confirmed: Literal[True] = True


class MaterialTermReviewRequest(StrictModel):
    decisions: Annotated[list[MaterialTermDecision], Field(min_length=1)]

    @model_validator(mode="after")
    def require_unique_terms(self) -> MaterialTermReviewRequest:
        term_ids = [decision.term_id for decision in self.decisions]
        if len(term_ids) != len(set(term_ids)):
            raise ValueError("material term decisions must have unique term IDs")
        return self

class ExtractionResponse(StrictModel):
    spans: list[DocumentSpan]
    terms: list[MaterialTerm]


class Claim(StrictModel):
    schema_id: Literal["before-you-commit.claim"] = "before-you-commit.claim"
    schema_version: Literal[CONTRACT_VERSION] = CONTRACT_VERSION
    claim_id: str = Field(min_length=1)
    analysis_id: str = Field(min_length=1)
    origin: ClaimOrigin
    statement: str = Field(min_length=1, max_length=1000)
    subject: str | None = None
    predicate: str | None = None
    value: str | float | int | bool | None = None
    unit: str | None = None
    time_qualifier: str | None = None
    conditions: list[str] = Field(default_factory=list)
    confirmed: bool = False


class ClaimAssessment(StrictModel):
    schema_id: Literal["before-you-commit.claim-assessment"] = (
        "before-you-commit.claim-assessment"
    )
    schema_version: Literal[CONTRACT_VERSION] = CONTRACT_VERSION
    assessment_id: str = Field(min_length=1)
    claim_id: str = Field(min_length=1)
    status: ClaimStatus
    reason_codes: list[str] = Field(min_length=1)
    supporting_span_ids: list[str] = Field(default_factory=list)
    conflicting_span_ids: list[str] = Field(default_factory=list)
    unresolved_conditions: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_status_evidence(self) -> ClaimAssessment:
        if self.status in {"supported", "supported_with_conditions"}:
            if not self.supporting_span_ids:
                raise ValueError(f"{self.status} assessments require supporting evidence")
        if self.status == "supported_with_conditions" and not self.unresolved_conditions:
            raise ValueError("conditional support requires unresolved conditions")
        if self.status == "contradicted" and not self.conflicting_span_ids:
            raise ValueError("contradicted assessments require conflicting evidence")
        return self


class GuidanceEvidence(StrictModel):
    schema_id: Literal["before-you-commit.guidance-evidence"] = (
        "before-you-commit.guidance-evidence"
    )
    schema_version: Literal[CONTRACT_VERSION] = CONTRACT_VERSION
    evidence_id: str = Field(min_length=1)
    evidence_plane: Literal["public_guidance"] = "public_guidance"
    source_id: str = Field(min_length=1)
    chunk_id: str = Field(min_length=1)
    url: str = Field(pattern=r"^https://")
    title: str = Field(min_length=1)
    heading_path: list[str] = Field(default_factory=list)
    publisher: str = Field(min_length=1)
    snippet: str = Field(min_length=1, max_length=2000)
    content_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    chunk_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    document_date: date | None = None
    crawled_at: datetime
    retrieval_method: Literal["lexical", "semantic", "hybrid"]
    retrieval_score: float
    index_version: str = Field(min_length=1)


class CalculationInput(StrictModel):
    name: str = Field(min_length=1)
    value: float
    unit: str = Field(min_length=1)
    source_span_ids: list[str] = Field(min_length=1)


class Calculation(StrictModel):
    schema_id: Literal["before-you-commit.calculation"] = (
        "before-you-commit.calculation"
    )
    schema_version: Literal[CONTRACT_VERSION] = CONTRACT_VERSION
    calculation_id: str = Field(min_length=1)
    formula_id: str = Field(min_length=1)
    inputs: list[CalculationInput] = Field(min_length=1)
    result: float
    unit: str = Field(min_length=1)
    rounding_rule: str = Field(min_length=1)
    assumptions: list[str] = Field(default_factory=list)


class Question(StrictModel):
    schema_id: Literal["before-you-commit.question"] = "before-you-commit.question"
    schema_version: Literal[CONTRACT_VERSION] = CONTRACT_VERSION
    question_id: str = Field(min_length=1)
    text: str = Field(min_length=1, max_length=1000)
    priority: Literal["high", "medium", "low"]
    trigger_ids: list[str] = Field(min_length=1)
    intended_recipient: Literal["insurer", "representative", "financial_adviser"]
    resolved: bool = False


class RealityCheckBrief(StrictModel):
    schema_id: Literal["before-you-commit.reality-check-brief"] = (
        "before-you-commit.reality-check-brief"
    )
    schema_version: Literal[CONTRACT_VERSION] = CONTRACT_VERSION
    analysis_id: str = Field(min_length=1)
    revision: PositiveInt
    completeness: EvidenceCompleteness
    terms: list[MaterialTerm]
    assessments: list[ClaimAssessment]
    calculations: list[Calculation]
    questions: list[Question]
    private_span_ids: list[str]
    public_evidence_ids: list[str]
    limitations: list[str] = Field(min_length=1)
    generated_at: datetime


class TaskRecord(StrictModel):
    schema_id: Literal["before-you-commit.task-record"] = (
        "before-you-commit.task-record"
    )
    schema_version: Literal[CONTRACT_VERSION] = CONTRACT_VERSION
    task_id: str = Field(min_length=1)
    analysis_id: str = Field(min_length=1)
    capability: str = Field(min_length=1)
    state: TaskState
    attempt: PositiveInt
    capsule_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    dependency_task_ids: list[str] = Field(default_factory=list)
    artifact_ids: list[str] = Field(default_factory=list)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_code: str | None = None


class RunEvent(StrictModel):
    schema_id: Literal["before-you-commit.run-event"] = "before-you-commit.run-event"
    schema_version: Literal[CONTRACT_VERSION] = CONTRACT_VERSION
    event_id: str = Field(min_length=1)
    analysis_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    task_id: str | None = None
    event_type: str = Field(min_length=1)
    occurred_at: datetime
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class RunMetrics(StrictModel):
    schema_id: Literal["before-you-commit.run-metrics"] = (
        "before-you-commit.run-metrics"
    )
    schema_version: Literal[CONTRACT_VERSION] = CONTRACT_VERSION
    analysis_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    task_count: NonNegativeInt
    completed_task_count: NonNegativeInt
    failed_task_count: NonNegativeInt
    duration_ms: NonNegativeInt
    model_invoked: bool
    model_input_tokens: NonNegativeInt = 0
    model_output_tokens: NonNegativeInt = 0
    cleanup_completed: bool


class Revision(StrictModel):
    schema_id: Literal["before-you-commit.revision"] = "before-you-commit.revision"
    schema_version: Literal[CONTRACT_VERSION] = CONTRACT_VERSION
    revision_id: str = Field(min_length=1)
    analysis_id: str = Field(min_length=1)
    version: PositiveInt
    parent_version: PositiveInt | None = None
    patch: dict[str, Any]
    affected_task_ids: list[str]
    created_at: datetime


class CreateAnalysisRequest(StrictModel):
    purpose: AnalysisPurpose
    decision_date: date | None = None
    model_consent: ModelConsent = Field(default_factory=ModelConsent)


class AnalysisResponse(StrictModel):
    analysis: AnalysisSession


class ErrorDetail(StrictModel):
    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    retryable: bool
    analysis_id: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorEnvelope(StrictModel):
    error: ErrorDetail