from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .config import CapabilityMode, Settings
from .decision_support import (
    DecisionService,
    InMemoryProfileRepository,
    ProfileNotFoundError,
    ProfileVersionConflictError,
)
from .extraction import (
    ExtractionFixtureNotFoundError,
    ExtractionNotFoundError,
    ExtractionVersionConflictError,
    FixtureExtractionService,
)
from .orchestration import CoordinatorService, RunNotFoundError
from .conversations import (
    ConversationNotFoundError,
    ConversationService,
    ProposalNotFoundError,
    ProposalStateError,
    RevisionConflictError,
    UndoNotAvailableError,
)
from .contracts import (
    API_VERSION,
    CONTRACT_VERSION,
    SERVICE_VERSION,
    CapabilitiesResponse,
    CapabilityStatus,
    ConversationCreateRequest,
    ConversationMessageRequest,
    ConversationMessageResponse,
    ConversationResponse,
    DependencyStatus,
    ErrorDetail,
    ErrorEnvelope,
    EvidenceComparisonRequest,
    EvidenceComparisonResponse,
    EvidenceSearchRequest,
    EvidenceSearchResponse,
    ExtractionResult,
    ExtractionReviewRequest,
    ExtractionSubmitRequest,
    HealthResponse,
    InvocationRequest,
    InvocationResponse,
    ProfileResponse,
    ProposalDecisionRequest,
    ProposalDecisionResponse,
    ReplayResponse,
    RecommendationEvaluationRequest,
    RecommendationResult,
    RevisionListResponse,
    UndoRequest,
    UndoResponse,
    RunInspectionResponse,
    VersionedProfile,
)
from .evidence import (
    EvidenceComparisonEligibilityError,
    EvidenceComparisonService,
    EvidenceDependencyError,
    EvidenceService,
    FixtureEvidenceAdapter,
    create_evidence_service,
)


def _dependency(configured: bool, fallback_mode: CapabilityMode) -> DependencyStatus:
    return DependencyStatus(
        status="ready" if configured else "not_configured",
        mode="live" if configured else fallback_mode,
    )


def create_app(
    settings: Settings | None = None,
    evidence_service: EvidenceService | None = None,
) -> FastAPI:
    runtime = settings or Settings.from_env()
    evidence = evidence_service or create_evidence_service(
        runtime.evidence_mode,
        corpus_path=runtime.evidence_corpus_path,
        max_age_days=runtime.evidence_max_age_days,
        timeout_seconds=runtime.dependency_timeout_seconds,
        supabase_url=runtime.supabase_url,
        service_key=runtime.supabase_service_role_key,
        openai_key=runtime.openai_key,
        database_url=runtime.database_url,
    )
    profiles = InMemoryProfileRepository()
    decisions = DecisionService(runtime.recommendation_mode)
    extractions = FixtureExtractionService(runtime.extraction_mode)
    coordinator = CoordinatorService(
        profiles,
        extractions,
        decisions,
        runtime.orchestration_mode,
    )
    conversations = ConversationService(evidence, profiles, decisions)
    comparisons = EvidenceComparisonService(
        evidence,
        EvidenceService(FixtureEvidenceAdapter("synthetic")),
    )
    application = FastAPI(
        title="CoverCheck POC API",
        version=SERVICE_VERSION,
        description="Versioned fixture-first integration API for the CoverCheck POC.",
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(runtime.allowed_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Idempotency-Key", "X-Request-ID"],
    )

    def error_response(
        code: str,
        message: str,
        status_code: int,
        retryable: bool = False,
        details: dict[str, str] | None = None,
    ) -> JSONResponse:
        envelope = ErrorEnvelope(
            error=ErrorDetail(
                code=code,
                message=message,
                retryable=retryable,
                run_id=f"request-{uuid4()}",
                details=details or {},
            )
        )
        return JSONResponse(status_code=status_code, content=envelope.model_dump())

    @application.exception_handler(ConversationNotFoundError)
    def conversation_not_found(
        request: Request, error: ConversationNotFoundError
    ) -> JSONResponse:
        return error_response(
            code="CONVERSATION_NOT_FOUND",
            message="The conversation does not exist or has expired.",
            status_code=404,
            details={"conversation_id": str(error)},
        )

    @application.exception_handler(RevisionConflictError)
    def revision_conflict(request: Request, error: RevisionConflictError) -> JSONResponse:
        return error_response(
            code="REVISION_CONFLICT",
            message="The active summary revision changed before this action could run.",
            status_code=409,
            details={"active_revision_id": str(error)},
        )

    @application.exception_handler(ProposalNotFoundError)
    def proposal_not_found(request: Request, error: ProposalNotFoundError) -> JSONResponse:
        return error_response(
            code="PROPOSAL_NOT_FOUND",
            message="The proposal does not exist or has expired.",
            status_code=404,
            details={"proposal_id": str(error)},
        )

    @application.exception_handler(ProposalStateError)
    def proposal_state_error(request: Request, error: ProposalStateError) -> JSONResponse:
        return error_response(
            code="PROPOSAL_STATE_CONFLICT",
            message="The proposal is no longer pending or its dependencies are unavailable.",
            status_code=409,
            details={"proposal_state": str(error)},
        )

    @application.exception_handler(UndoNotAvailableError)
    def undo_not_available(
        request: Request, error: UndoNotAvailableError
    ) -> JSONResponse:
        return error_response(
            code="UNDO_NOT_AVAILABLE",
            message="There is no earlier coherent revision to restore.",
            status_code=409,
            details={"active_revision_id": str(error)},
        )

    @application.exception_handler(ExtractionFixtureNotFoundError)
    def extraction_fixture_not_found(
        request: Request, error: ExtractionFixtureNotFoundError
    ) -> JSONResponse:
        return error_response(
            code="EXTRACTION_FIXTURE_NOT_FOUND",
            message="The requested synthetic policy fixture does not exist.",
            status_code=404,
            details={"fixture_id": str(error)},
        )

    @application.exception_handler(ExtractionNotFoundError)
    def extraction_not_found(
        request: Request, error: ExtractionNotFoundError
    ) -> JSONResponse:
        return error_response(
            code="EXTRACTION_NOT_FOUND",
            message="The extraction does not exist or has expired.",
            status_code=404,
            details={"extraction_id": str(error)},
        )

    @application.exception_handler(ExtractionVersionConflictError)
    def extraction_version_conflict(
        request: Request, error: ExtractionVersionConflictError
    ) -> JSONResponse:
        return error_response(
            code="EXTRACTION_VERSION_CONFLICT",
            message="The extraction changed before review was submitted.",
            status_code=409,
            details={"extraction_id": str(error)},
        )

    @application.exception_handler(RunNotFoundError)
    def run_not_found(request: Request, error: RunNotFoundError) -> JSONResponse:
        return error_response(
            code="RUN_NOT_FOUND",
            message="The run does not exist or has expired.",
            status_code=404,
            details={"run_id": str(error)},
        )

    @application.exception_handler(EvidenceDependencyError)
    def evidence_dependency_failed(
        request: Request, error: EvidenceDependencyError
    ) -> JSONResponse:
        return error_response(
            code="EVIDENCE_DEPENDENCY_UNAVAILABLE",
            message="The evidence service is temporarily unavailable.",
            status_code=503,
            retryable=True,
            details={"mode": evidence.mode},
        )

    @application.exception_handler(EvidenceComparisonEligibilityError)
    def comparison_not_eligible(
        request: Request, error: EvidenceComparisonEligibilityError
    ) -> JSONResponse:
        return error_response(
            code="EVIDENCE_COMPARISON_NOT_ELIGIBLE",
            message="The selected products do not meet the evidence comparison gate.",
            status_code=422,
            details={"gate_reasons": error.reasons},
        )

    @application.exception_handler(ProfileNotFoundError)
    def profile_not_found(request: Request, error: ProfileNotFoundError) -> JSONResponse:
        return error_response(
            code="PROFILE_NOT_FOUND",
            message="The profile does not exist or has expired.",
            status_code=404,
            details={"profile_id": str(error)},
        )

    @application.exception_handler(ProfileVersionConflictError)
    def profile_version_conflict(
        request: Request, error: ProfileVersionConflictError
    ) -> JSONResponse:
        return error_response(
            code="PROFILE_VERSION_CONFLICT",
            message="The profile version conflicts with an immutable stored version.",
            status_code=409,
            details={"profile_id": str(error)},
        )

    @application.get("/health", response_model=HealthResponse, tags=["system"])
    def health() -> HealthResponse:
        return HealthResponse(
            version=SERVICE_VERSION,
            environment=runtime.app_env,
            dependencies={
                "database": _dependency(runtime.database_configured, "synthetic"),
                "object_store": _dependency(runtime.object_store_configured, "simulated"),
                "openrouter": _dependency(runtime.openrouter_configured, "simulated"),
            },
        )

    @application.get(
        "/v1/capabilities", response_model=CapabilitiesResponse, tags=["system"]
    )
    def capabilities() -> CapabilitiesResponse:
        modes = {
            "profile": runtime.profile_mode,
            "extraction": runtime.extraction_mode,
            "evidence": runtime.evidence_mode,
            "recommendation": runtime.recommendation_mode,
            "orchestration": runtime.orchestration_mode,
            "conversation": runtime.conversation_mode,
        }
        return CapabilitiesResponse(
            service_version=SERVICE_VERSION,
            api_version=API_VERSION,
            capabilities={
                name: CapabilityStatus(
                    mode=mode,
                    contract_version=CONTRACT_VERSION,
                    available=True,
                )
                for name, mode in modes.items()
            },
        )

    @application.post(
        "/v1/evidence/search",
        response_model=EvidenceSearchResponse,
        tags=["evidence"],
    )
    def search_evidence(request: EvidenceSearchRequest) -> EvidenceSearchResponse:
        return evidence.search(request)

    @application.post(
        "/v1/evidence/compare",
        response_model=EvidenceComparisonResponse,
        tags=["evidence"],
    )
    def compare_evidence(
        request: EvidenceComparisonRequest,
    ) -> EvidenceComparisonResponse:
        return comparisons.compare(request)

    @application.post(
        "/v1/profiles",
        response_model=ProfileResponse,
        status_code=201,
        tags=["profiles"],
    )
    def create_profile(profile: VersionedProfile) -> ProfileResponse:
        stored = profiles.save(profile)
        return ProfileResponse(
            run_id=f"profile-{uuid4()}",
            mode=runtime.profile_mode,
            profile=stored,
        )

    @application.get(
        "/v1/profiles/{profile_id}",
        response_model=ProfileResponse,
        tags=["profiles"],
    )
    def get_profile(profile_id: str, version: int | None = None) -> ProfileResponse:
        return ProfileResponse(
            run_id=f"profile-{uuid4()}",
            mode=runtime.profile_mode,
            profile=profiles.get(profile_id, version),
        )

    @application.post(
        "/v1/recommendations/evaluate",
        response_model=RecommendationResult,
        tags=["recommendations"],
    )
    def evaluate_recommendation(
        request: RecommendationEvaluationRequest,
    ) -> RecommendationResult:
        profiles.save(request.profile)
        return decisions.evaluate(request.profile)

    @application.post(
        "/v1/extractions",
        response_model=ExtractionResult,
        status_code=201,
        tags=["extractions"],
    )
    def submit_extraction(request: ExtractionSubmitRequest) -> ExtractionResult:
        return extractions.submit(request.fixture_id)

    @application.post(
        "/v1/extractions/{extraction_id}/review",
        response_model=ExtractionResult,
        tags=["extractions"],
    )
    def review_extraction(
        extraction_id: str,
        request: ExtractionReviewRequest,
    ) -> ExtractionResult:
        return extractions.review(extraction_id, request)

    @application.post(
        "/v1/invocations",
        response_model=InvocationResponse,
        tags=["orchestration"],
    )
    def invoke(request: InvocationRequest) -> InvocationResponse:
        return coordinator.invoke(request)

    @application.get(
        "/v1/runs/{run_id}",
        response_model=RunInspectionResponse,
        tags=["orchestration"],
    )
    def inspect_run(run_id: str) -> RunInspectionResponse:
        return RunInspectionResponse(run=coordinator.get(run_id))

    @application.post(
        "/v1/conversations",
        response_model=ConversationResponse,
        status_code=201,
        tags=["conversations"],
    )
    def create_conversation(request: ConversationCreateRequest) -> ConversationResponse:
        return conversations.create(
            request.active_revision_id,
            request.profile,
            request.recommendation,
        )

    @application.post(
        "/v1/conversations/{conversation_id}/messages",
        response_model=ConversationMessageResponse,
        tags=["conversations"],
    )
    def post_conversation_message(
        conversation_id: str, request: ConversationMessageRequest
    ) -> ConversationMessageResponse:
        return conversations.respond(conversation_id, request)

    @application.post(
        "/v1/conversations/{conversation_id}/proposals/{proposal_id}/confirm",
        response_model=ProposalDecisionResponse,
        tags=["conversations"],
    )
    def confirm_proposal(
        conversation_id: str,
        proposal_id: str,
        request: ProposalDecisionRequest,
    ) -> ProposalDecisionResponse:
        return conversations.confirm_proposal(conversation_id, proposal_id, request)

    @application.post(
        "/v1/conversations/{conversation_id}/proposals/{proposal_id}/cancel",
        response_model=ProposalDecisionResponse,
        tags=["conversations"],
    )
    def cancel_proposal(
        conversation_id: str,
        proposal_id: str,
        request: ProposalDecisionRequest,
    ) -> ProposalDecisionResponse:
        return conversations.cancel_proposal(conversation_id, proposal_id, request)

    @application.get(
        "/v1/conversations/{conversation_id}/revisions",
        response_model=RevisionListResponse,
        tags=["conversations"],
    )
    def list_revisions(conversation_id: str) -> RevisionListResponse:
        revisions = conversations.list_revisions(conversation_id)
        active_revision_id = conversations.replay(conversation_id).active_revision_id
        return RevisionListResponse(
            conversation_id=conversation_id,
            active_revision_id=active_revision_id,
            revisions=revisions,
        )

    @application.get(
        "/v1/conversations/{conversation_id}/replay",
        response_model=ReplayResponse,
        tags=["conversations"],
    )
    def replay_conversation(conversation_id: str) -> ReplayResponse:
        return conversations.replay(conversation_id)

    @application.post(
        "/v1/conversations/{conversation_id}/undo",
        response_model=UndoResponse,
        tags=["conversations"],
    )
    def undo_revision(conversation_id: str, request: UndoRequest) -> UndoResponse:
        return conversations.undo(conversation_id, request)

    return application


app = create_app()