from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .analysis_service import AnalysisSessionService
from .api_v2 import create_v2_router
from .config import Settings
from .document_service import DocumentService


SERVICE_VERSION = "0.1.0"


def _dependency(configured: bool, ready_mode: str) -> dict[str, str]:
    return {
        "status": "ready" if configured else "not_configured",
        "mode": ready_mode if configured else "off",
    }


def create_app(settings: Settings | None = None) -> FastAPI:
    runtime = settings or Settings.from_env()
    application = FastAPI(
        title="Before You Commit API",
        version=SERVICE_VERSION,
        description="Evidence-backed financial commitment reality-check API.",
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(runtime.allowed_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Content-Type", "Idempotency-Key", "X-Request-ID"],
    )

    @application.get("/health", tags=["system"])
    def health() -> dict[str, object]:
        return {
            "service": "before-you-commit-api",
            "version": SERVICE_VERSION,
            "status": "healthy",
            "environment": runtime.app_env,
            "dependencies": {
                "database": _dependency(runtime.database_configured, "local"),
                "document_processing": _dependency(True, "local"),
                "bedrock": _dependency(runtime.bedrock_configured, "configured"),
            },
        }

    analysis_sessions = AnalysisSessionService(
        ttl=timedelta(hours=runtime.analysis_ttl_hours)
    )
    document_workspace = (
        Path(runtime.document_workspace_root)
        if runtime.document_workspace_root is not None
        else None
    )
    documents = DocumentService(
        workspace_root=document_workspace,
        max_size_bytes=runtime.document_max_size_bytes,
        max_page_count=runtime.document_max_page_count,
        orphan_ttl=timedelta(minutes=runtime.document_orphan_ttl_minutes),
    )
    application.include_router(create_v2_router(analysis_sessions, documents))

    return application


app = create_app()