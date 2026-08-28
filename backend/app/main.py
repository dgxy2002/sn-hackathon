from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .config import CapabilityMode, Settings
from .conversations import (
    ConversationNotFoundError,
    ConversationService,
    RevisionConflictError,
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
    EvidenceSearchRequest,
    EvidenceSearchResponse,
    HealthResponse,
)
from .evidence import EvidenceDependencyError, EvidenceService, create_evidence_service


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
    )
    conversations = ConversationService(evidence)
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
        "/v1/conversations",
        response_model=ConversationResponse,
        status_code=201,
        tags=["conversations"],
    )
    def create_conversation(request: ConversationCreateRequest) -> ConversationResponse:
        return conversations.create(request.active_revision_id)

    @application.post(
        "/v1/conversations/{conversation_id}/messages",
        response_model=ConversationMessageResponse,
        tags=["conversations"],
    )
    def post_conversation_message(
        conversation_id: str, request: ConversationMessageRequest
    ) -> ConversationMessageResponse:
        return conversations.respond(conversation_id, request)

    return application


app = create_app()