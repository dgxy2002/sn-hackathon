from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, File, Header, UploadFile
from fastapi.responses import JSONResponse, Response

from .analysis_service import AnalysisNotFoundError, AnalysisSessionService
from .contracts_v2 import (
    AnalysisResponse,
    CreateAnalysisRequest,
    DocumentListResponse,
    DocumentResponse,
    ErrorDetail,
    ErrorEnvelope,
    ExtractionResponse,
    MaterialTermReviewRequest,
    PrivacyReviewRequest,
    PrivacyScanResponse,
)
from .document_service import DocumentService, DocumentServiceError
from .material_extraction import MaterialExtractionService


def create_v2_router(
    service: AnalysisSessionService | None = None,
    document_service: DocumentService | None = None,
    extraction_service: MaterialExtractionService | None = None,
) -> APIRouter:
    analyses = service or AnalysisSessionService()
    documents = document_service or DocumentService()
    extractor = extraction_service or MaterialExtractionService()
    router = APIRouter(prefix="/api/v2", tags=["reality-check"])

    @router.post(
        "/analyses",
        response_model=AnalysisResponse,
        status_code=201,
    )
    def create_analysis(request: CreateAnalysisRequest) -> AnalysisResponse:
        return AnalysisResponse(analysis=analyses.create(request))

    @router.get(
        "/analyses/{analysis_id}",
        response_model=AnalysisResponse,
        responses={404: {"model": ErrorEnvelope}},
    )
    def get_analysis(analysis_id: str) -> AnalysisResponse | JSONResponse:
        try:
            return AnalysisResponse(analysis=analyses.get(analysis_id))
        except AnalysisNotFoundError:
            documents.delete_analysis(analysis_id)
            return _not_found(analysis_id)

    @router.post(
        "/analyses/{analysis_id}/documents",
        response_model=DocumentResponse,
        status_code=201,
        responses={
            400: {"model": ErrorEnvelope},
            404: {"model": ErrorEnvelope},
            409: {"model": ErrorEnvelope},
            413: {"model": ErrorEnvelope},
            415: {"model": ErrorEnvelope},
            422: {"model": ErrorEnvelope},
        },
    )
    async def upload_document(
        analysis_id: str,
        document: Annotated[UploadFile, File()],
        idempotency_key: Annotated[
            str | None,
            Header(alias="Idempotency-Key"),
        ] = None,
    ) -> DocumentResponse | JSONResponse:
        try:
            analyses.get(analysis_id)
        except AnalysisNotFoundError:
            documents.delete_analysis(analysis_id)
            return _not_found(analysis_id)
        try:
            uploaded = await documents.upload(
                analysis_id,
                document,
                idempotency_key,
            )
        except DocumentServiceError as error:
            return _document_error(analysis_id, error)
        analyses.set_stage(analysis_id, "privacy_scan")
        return DocumentResponse(document=uploaded)

    @router.get(
        "/analyses/{analysis_id}/documents",
        response_model=DocumentListResponse,
        responses={404: {"model": ErrorEnvelope}},
    )
    def list_documents(analysis_id: str) -> DocumentListResponse | JSONResponse:
        try:
            analyses.get(analysis_id)
        except AnalysisNotFoundError:
            documents.delete_analysis(analysis_id)
            return _not_found(analysis_id)
        return DocumentListResponse(documents=documents.list(analysis_id))


    @router.post(
        "/analyses/{analysis_id}/privacy-scan",
        response_model=PrivacyScanResponse,
        responses={
            400: {"model": ErrorEnvelope},
            404: {"model": ErrorEnvelope},
            409: {"model": ErrorEnvelope},
        },
    )
    def scan_privacy(
        analysis_id: str,
        idempotency_key: Annotated[
            str | None,
            Header(alias="Idempotency-Key"),
        ] = None,
    ) -> PrivacyScanResponse | JSONResponse:
        try:
            analyses.get(analysis_id)
        except AnalysisNotFoundError:
            documents.delete_analysis(analysis_id)
            return _not_found(analysis_id)
        try:
            findings = documents.scan_privacy(analysis_id, idempotency_key)
        except DocumentServiceError as error:
            return _document_error(analysis_id, error)
        stage = "privacy_review" if findings else "extracting"
        analyses.set_stage(analysis_id, stage)
        return PrivacyScanResponse(findings=findings)


    @router.patch(
        "/analyses/{analysis_id}/privacy-findings",
        response_model=PrivacyScanResponse,
        responses={
            400: {"model": ErrorEnvelope},
            404: {"model": ErrorEnvelope},
            409: {"model": ErrorEnvelope},
        },
    )
    def review_privacy(
        analysis_id: str,
        request: PrivacyReviewRequest,
        idempotency_key: Annotated[
            str | None,
            Header(alias="Idempotency-Key"),
        ] = None,
    ) -> PrivacyScanResponse | JSONResponse:
        try:
            analyses.get(analysis_id)
        except AnalysisNotFoundError:
            documents.delete_analysis(analysis_id)
            return _not_found(analysis_id)
        try:
            findings = documents.review_privacy(
                analysis_id,
                request,
                idempotency_key,
            )
        except DocumentServiceError as error:
            return _document_error(analysis_id, error)
        resolved = all(
            finding.confirmed and finding.action != "review" for finding in findings
        )
        analyses.set_stage(
            analysis_id,
            "extracting" if resolved else "privacy_review",
        )
        return PrivacyScanResponse(findings=findings)


    @router.post(
        "/analyses/{analysis_id}/extract",
        response_model=ExtractionResponse,
        responses={
            400: {"model": ErrorEnvelope},
            404: {"model": ErrorEnvelope},
            409: {"model": ErrorEnvelope},
        },
    )
    def extract_terms(
        analysis_id: str,
        idempotency_key: Annotated[
            str | None,
            Header(alias="Idempotency-Key"),
        ] = None,
    ) -> ExtractionResponse | JSONResponse:
        try:
            analyses.get(analysis_id)
        except AnalysisNotFoundError:
            documents.delete_analysis(analysis_id)
            extractor.delete_analysis(analysis_id)
            return _not_found(analysis_id)
        try:
            spans = documents.redacted_spans(analysis_id)
            result = extractor.extract(analysis_id, spans, idempotency_key)
        except DocumentServiceError as error:
            return _document_error(analysis_id, error)
        analyses.set_stage(analysis_id, "term_review")
        return ExtractionResponse(
            spans=list(result.spans),
            terms=list(result.terms),
        )


    @router.patch(
        "/analyses/{analysis_id}/terms",
        response_model=ExtractionResponse,
        responses={
            400: {"model": ErrorEnvelope},
            404: {"model": ErrorEnvelope},
            409: {"model": ErrorEnvelope},
            422: {"model": ErrorEnvelope},
        },
    )
    def review_terms(
        analysis_id: str,
        request: MaterialTermReviewRequest,
        idempotency_key: Annotated[
            str | None,
            Header(alias="Idempotency-Key"),
        ] = None,
    ) -> ExtractionResponse | JSONResponse:
        try:
            analyses.get(analysis_id)
        except AnalysisNotFoundError:
            documents.delete_analysis(analysis_id)
            extractor.delete_analysis(analysis_id)
            return _not_found(analysis_id)
        try:
            result = extractor.review(analysis_id, request, idempotency_key)
        except DocumentServiceError as error:
            return _document_error(analysis_id, error)
        stage = "ready" if all(term.confirmed for term in result.terms) else "term_review"
        analyses.set_stage(analysis_id, stage)
        return ExtractionResponse(
            spans=list(result.spans),
            terms=list(result.terms),
        )

    @router.delete(
        "/analyses/{analysis_id}",
        status_code=204,
        response_class=Response,
        response_model=None,
        responses={404: {"model": ErrorEnvelope}},
    )
    def delete_analysis(analysis_id: str) -> Response | JSONResponse:
        try:
            analyses.get(analysis_id)
            documents.delete_analysis(analysis_id)
            extractor.delete_analysis(analysis_id)
            analyses.delete(analysis_id)
        except AnalysisNotFoundError:
            return _not_found(analysis_id)
        return Response(status_code=204)

    return router


def _not_found(analysis_id: str) -> JSONResponse:
    envelope = ErrorEnvelope(
        error=ErrorDetail(
            code="ANALYSIS_NOT_FOUND",
            message="The analysis does not exist or has expired.",
            retryable=False,
            analysis_id=analysis_id,
        )
    )
    return JSONResponse(status_code=404, content=envelope.model_dump(mode="json"))


def _document_error(
    analysis_id: str,
    error: DocumentServiceError,
) -> JSONResponse:
    envelope = ErrorEnvelope(
        error=ErrorDetail(
            code=error.code,
            message=error.message,
            retryable=error.retryable,
            analysis_id=analysis_id,
        )
    )
    return JSONResponse(
        status_code=error.status_code,
        content=envelope.model_dump(mode="json"),
    )
