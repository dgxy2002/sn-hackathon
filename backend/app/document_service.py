from __future__ import annotations

import asyncio
import hashlib
import re
import shutil
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import RLock
from uuid import NAMESPACE_URL, uuid4, uuid5

import pymupdf
from fastapi import UploadFile
from starlette.concurrency import run_in_threadpool

from .contracts_v2 import (
    DocumentSpan,
    PrivacyAction,
    PrivacyCategory,
    PrivacyFinding,
    PrivacyReviewRequest,
    ParserPath,
    SourceRegion,
    UploadedDocument,
)




PRIVACY_PATTERNS: tuple[
    tuple[PrivacyCategory, re.Pattern[str], PrivacyAction, float], ...
] = (
    (
        "name",
        re.compile(
            r"(?im)^\s*(?:name|insured|policy owner|life assured)\s*:\s*"
            r"[A-Z][A-Za-z .'-]{1,80}(?=$|\n)"
        ),
        "redact",
        0.98,
    ),
    (
        "national_id",
        re.compile(r"(?i)\b[STFGM]\d{7}[A-Z]\b"),
        "redact",
        0.99,
    ),
    (
        "contact",
        re.compile(
            r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b|"
            r"(?<!\d)(?:\+?65[ -]?)?[689]\d{3}[ -]?\d{4}(?!\d)"
        ),
        "redact",
        0.98,
    ),
    (
        "address",
        re.compile(r"(?im)^\s*address\s*:\s*.+$"),
        "review",
        0.9,
    ),
    (
        "policy_number",
        re.compile(
            r"(?im)\b(?:policy|certificate)\s*(?:number|no\.?|#)\s*:\s*"
            r"[A-Z0-9-]{4,}"
        ),
        "redact",
        0.98,
    ),
    (
        "account_detail",
        re.compile(
            r"(?im)\b(?:account|bank)\s*(?:number|no\.?|#)\s*:\s*"
            r"[A-Z0-9-]{4,}"
        ),
        "redact",
        0.98,
    ),
    (
        "signature",
        re.compile(r"(?im)^\s*(?:signature|signed by)\s*:\s*.+$"),
        "review",
        0.9,
    ),
    (
        "health_information",
        re.compile(
            r"(?im)^\s*(?:medical history|health declaration|"
            r"pre-existing conditions?|current diagnos(?:is|es)|"
            r"current treatments?|current medications?)\s*:\s*.+$"
        ),
        "review",
        0.9,
    ),
)

class DocumentServiceError(ValueError):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int,
        *,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.retryable = retryable


@dataclass(frozen=True)
class ParsedSpan:
    page: int
    x: float
    y: float
    width: float
    height: float
    text: str
    used_ocr: bool


@dataclass(frozen=True)
class ParsedPdf:
    page_count: int
    spans: tuple[ParsedSpan, ...]
    parser_path: ParserPath


class DocumentService:
    def __init__(
        self,
        *,
        workspace_root: Path | None = None,
        max_size_bytes: int = 20 * 1024 * 1024,
        max_page_count: int = 100,
        chunk_size: int = 64 * 1024,
        orphan_ttl: timedelta = timedelta(minutes=30),
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if max_size_bytes <= 0:
            raise ValueError("max_size_bytes must be positive")
        if max_page_count <= 0:
            raise ValueError("max_page_count must be positive")
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if orphan_ttl <= timedelta(0):
            raise ValueError("orphan_ttl must be positive")

        self._workspace_root = workspace_root or Path(
            tempfile.gettempdir(), "before-you-commit"
        )
        self._max_size_bytes = max_size_bytes
        self._max_page_count = max_page_count
        self._chunk_size = chunk_size
        self._orphan_ttl = orphan_ttl
        self._clock = clock or (lambda: datetime.now(UTC))
        self._documents: dict[str, list[UploadedDocument]] = {}
        self._spans: dict[tuple[str, str], tuple[ParsedSpan, ...]] = {}
        self._workspace_ids: dict[str, str] = {}
        self._hash_index: dict[tuple[str, str], str] = {}
        self._idempotency: dict[tuple[str, str], tuple[str, str]] = {}
        self._privacy_findings: dict[str, tuple[PrivacyFinding, ...]] = {}
        self._privacy_idempotency: dict[
            tuple[str, str], tuple[str, tuple[PrivacyFinding, ...]]
        ] = {}
        self._privacy_review_idempotency: dict[
            tuple[str, str], tuple[str, tuple[PrivacyFinding, ...]]
        ] = {}
        self._lock = RLock()
        self._sweep_abandoned_workspaces()


    def _sweep_abandoned_workspaces(self) -> None:
        if not self._workspace_root.exists():
            return
        cutoff = self._clock() - self._orphan_ttl
        for candidate in self._workspace_root.iterdir():
            if not candidate.is_dir() or candidate.is_symlink():
                continue
            modified_at = datetime.fromtimestamp(candidate.stat().st_mtime, UTC)
            if modified_at <= cutoff:
                shutil.rmtree(candidate, ignore_errors=True)

    async def upload(
        self,
        analysis_id: str,
        upload: UploadFile,
        idempotency_key: str | None,
    ) -> UploadedDocument:
        key = self._validate_idempotency_key(idempotency_key)
        self._validate_media_type(upload.content_type)
        document_id = str(uuid4())
        workspace = self._workspace_for(analysis_id)
        temporary_path = workspace / f"{document_id}.upload"
        size_bytes = 0
        digest = hashlib.sha256()
        first_bytes = b""

        try:
            with temporary_path.open("xb") as destination:
                while chunk := await upload.read(self._chunk_size):
                    size_bytes += len(chunk)
                    if size_bytes > self._max_size_bytes:
                        raise DocumentServiceError(
                            "DOCUMENT_TOO_LARGE",
                            "The PDF exceeds the configured upload limit.",
                            413,
                        )
                    if len(first_bytes) < 5:
                        first_bytes = (first_bytes + chunk)[:5]
                    digest.update(chunk)
                    destination.write(chunk)

            if first_bytes != b"%PDF-":
                raise DocumentServiceError(
                    "INVALID_PDF",
                    "The uploaded file is not a valid PDF.",
                    422,
                )

            content_sha256 = digest.hexdigest()
            parsed = await run_in_threadpool(self._inspect_pdf, temporary_path)

            with self._lock:
                existing_for_key = self._idempotency.get((analysis_id, key))
                if existing_for_key is not None:
                    existing_hash, existing_document_id = existing_for_key
                    if existing_hash != content_sha256:
                        raise DocumentServiceError(
                            "IDEMPOTENCY_CONFLICT",
                            "The idempotency key was already used for another payload.",
                            409,
                        )
                    temporary_path.unlink(missing_ok=True)
                    return self._find_document(analysis_id, existing_document_id)

                duplicate_id = self._hash_index.get((analysis_id, content_sha256))
                if duplicate_id is not None:
                    self._idempotency[(analysis_id, key)] = (
                        content_sha256,
                        duplicate_id,
                    )
                    temporary_path.unlink(missing_ok=True)
                    return self._find_document(analysis_id, duplicate_id)

                final_path = workspace / f"{document_id}.pdf"
                temporary_path.replace(final_path)
                document = UploadedDocument(
                    document_id=document_id,
                    analysis_id=analysis_id,
                    state="ready",
                    content_sha256=content_sha256,
                    parser_path=parsed.parser_path,
                    page_count=parsed.page_count,
                    size_bytes=size_bytes,
                    uploaded_at=self._clock(),
                )
                self._documents.setdefault(analysis_id, []).append(document)
                self._spans[(analysis_id, document_id)] = parsed.spans
                self._privacy_findings.pop(analysis_id, None)
                self._hash_index[(analysis_id, content_sha256)] = document_id
                self._idempotency[(analysis_id, key)] = (
                    content_sha256,
                    document_id,
                )
                return document
        except (Exception, asyncio.CancelledError):
            temporary_path.unlink(missing_ok=True)
            self._remove_empty_workspace(analysis_id, workspace)
            raise
        finally:
            await upload.close()

    def list(self, analysis_id: str) -> list[UploadedDocument]:
        with self._lock:
            return list(self._documents.get(analysis_id, ()))


    def scan_privacy(
        self,
        analysis_id: str,
        idempotency_key: str | None,
    ) -> list[PrivacyFinding]:
        key = self._validate_idempotency_key(idempotency_key)
        with self._lock:
            documents = tuple(self._documents.get(analysis_id, ()))
            if not documents:
                raise DocumentServiceError(
                    "NO_DOCUMENTS",
                    "Upload at least one readable PDF before running a privacy scan.",
                    409,
                )
            fingerprint = hashlib.sha256(
                "".join(document.content_sha256 for document in documents).encode()
            ).hexdigest()
            previous = self._privacy_idempotency.get((analysis_id, key))
            if previous is not None:
                previous_fingerprint, previous_findings = previous
                if previous_fingerprint != fingerprint:
                    raise DocumentServiceError(
                        "IDEMPOTENCY_CONFLICT",
                        "The idempotency key was already used for another payload.",
                        409,
                    )
                return list(previous_findings)
            source_spans = tuple(
                (
                    document.document_id,
                    self._spans.get((analysis_id, document.document_id), ()),
                )
                for document in documents
            )

        findings: list[PrivacyFinding] = []
        for document_id, spans in source_spans:
            for span_index, span in enumerate(spans):
                for category, pattern, action, confidence in PRIVACY_PATTERNS:
                    for match in pattern.finditer(span.text):
                        finding_id = str(
                            uuid5(
                                NAMESPACE_URL,
                                f"{document_id}:{span_index}:{category}:"
                                f"{match.start()}:{match.end()}",
                            )
                        )
                        findings.append(
                            PrivacyFinding(
                                finding_id=finding_id,
                                document_id=document_id,
                                category=category,
                                region=SourceRegion(
                                    page=span.page,
                                    x=span.x,
                                    y=span.y,
                                    width=span.width,
                                    height=span.height,
                                ),
                                action=action,
                                confidence=confidence,
                            )
                        )

        result = tuple(findings)
        with self._lock:
            self._privacy_findings[analysis_id] = result
            self._privacy_idempotency[(analysis_id, key)] = (fingerprint, result)
        return list(result)


    def review_privacy(
        self,
        analysis_id: str,
        request: PrivacyReviewRequest,
        idempotency_key: str | None,
    ) -> list[PrivacyFinding]:
        key = self._validate_idempotency_key(idempotency_key)
        payload_sha256 = hashlib.sha256(
            "\n".join(
                f"{decision.finding_id}:{decision.action}:{decision.confirmed}"
                for decision in sorted(
                    request.decisions,
                    key=lambda item: item.finding_id,
                )
            ).encode()
        ).hexdigest()

        with self._lock:
            previous = self._privacy_review_idempotency.get((analysis_id, key))
            if previous is not None:
                previous_hash, previous_findings = previous
                if previous_hash != payload_sha256:
                    raise DocumentServiceError(
                        "IDEMPOTENCY_CONFLICT",
                        "The idempotency key was already used for another payload.",
                        409,
                    )
                return list(previous_findings)

            current = self._privacy_findings.get(analysis_id)
            if current is None:
                raise DocumentServiceError(
                    "PRIVACY_SCAN_REQUIRED",
                    "Run the privacy scan before reviewing findings.",
                    409,
                )
            decisions = {
                decision.finding_id: decision for decision in request.decisions
            }
            known_ids = {finding.finding_id for finding in current}
            if not set(decisions).issubset(known_ids):
                raise DocumentServiceError(
                    "PRIVACY_FINDING_NOT_FOUND",
                    "A privacy finding does not exist in the current scan.",
                    404,
                )
            reviewed = tuple(
                finding.model_copy(
                    update={
                        "action": decisions[finding.finding_id].action,
                        "confirmed": True,
                    }
                )
                if finding.finding_id in decisions
                else finding
                for finding in current
            )
            self._privacy_findings[analysis_id] = reviewed
            self._privacy_review_idempotency[(analysis_id, key)] = (
                payload_sha256,
                reviewed,
            )
            return list(reviewed)


    def redacted_spans(self, analysis_id: str) -> list[DocumentSpan]:
        with self._lock:
            findings = self._privacy_findings.get(analysis_id)
            if findings is None:
                raise DocumentServiceError(
                    "PRIVACY_SCAN_REQUIRED",
                    "Run the privacy scan before extracting document terms.",
                    409,
                )
            if any(
                not finding.confirmed or finding.action == "review"
                for finding in findings
            ):
                raise DocumentServiceError(
                    "PRIVACY_REVIEW_REQUIRED",
                    "Resolve every privacy finding before extracting document terms.",
                    409,
                )
            documents = tuple(self._documents.get(analysis_id, ()))
            source_spans = tuple(
                (
                    document.document_id,
                    self._spans.get((analysis_id, document.document_id), ()),
                )
                for document in documents
            )
            finding_by_id = {finding.finding_id: finding for finding in findings}

        redacted_spans: list[DocumentSpan] = []
        for document_id, spans in source_spans:
            for span_index, span in enumerate(spans):
                excluded = False
                redaction_ranges: list[tuple[int, int]] = []
                for category, pattern, _, _ in PRIVACY_PATTERNS:
                    for match in pattern.finditer(span.text):
                        finding_id = str(
                            uuid5(
                                NAMESPACE_URL,
                                f"{document_id}:{span_index}:{category}:"
                                f"{match.start()}:{match.end()}",
                            )
                        )
                        finding = finding_by_id.get(finding_id)
                        if finding is None:
                            continue
                        if finding.action == "exclude":
                            excluded = True
                        elif finding.action == "redact":
                            redaction_ranges.append((match.start(), match.end()))
                if excluded:
                    continue

                redacted_text = self._redact_text(span.text, redaction_ranges)
                for segment_start in range(0, len(redacted_text), 2000):
                    segment = redacted_text[segment_start : segment_start + 2000]
                    if not segment.strip():
                        continue
                    span_id = str(
                        uuid5(
                            NAMESPACE_URL,
                            f"{document_id}:{span.page}:{span_index}:{segment_start}",
                        )
                    )
                    redacted_spans.append(
                        DocumentSpan(
                            span_id=span_id,
                            analysis_id=analysis_id,
                            document_id=document_id,
                            region=SourceRegion(
                                page=span.page,
                                x=span.x,
                                y=span.y,
                                width=span.width,
                                height=span.height,
                            ),
                            redacted_text=segment,
                            content_sha256=hashlib.sha256(segment.encode()).hexdigest(),
                            parser_version=f"pymupdf-{pymupdf.VersionBind}",
                        )
                    )
        return redacted_spans

    @staticmethod
    def _redact_text(
        text: str,
        ranges: list[tuple[int, int]],
    ) -> str:
        redacted = text
        for start, end in sorted(set(ranges), reverse=True):
            redacted = f"{redacted[:start]}[REDACTED]{redacted[end:]}"
        return redacted

    def delete_analysis(self, analysis_id: str) -> None:
        with self._lock:
            workspace_id = self._workspace_ids.pop(analysis_id, None)
            documents = self._documents.pop(analysis_id, ())
            for document in documents:
                self._spans.pop((analysis_id, document.document_id), None)
                self._hash_index.pop(
                    (analysis_id, document.content_sha256),
                    None,
                )
            self._privacy_findings.pop(analysis_id, None)
            idempotency_keys = [
                key for key in self._idempotency if key[0] == analysis_id
            ]
            for key in idempotency_keys:
                del self._idempotency[key]
            privacy_keys = [
                key for key in self._privacy_idempotency if key[0] == analysis_id
            ]
            for key in privacy_keys:
                del self._privacy_idempotency[key]
            review_keys = [
                key
                for key in self._privacy_review_idempotency
                if key[0] == analysis_id
            ]
            for key in review_keys:
                del self._privacy_review_idempotency[key]

        if workspace_id is not None:
            shutil.rmtree(self._workspace_root / workspace_id, ignore_errors=True)
        self._remove_root_if_empty()

    def _workspace_for(self, analysis_id: str) -> Path:
        with self._lock:
            workspace_id = self._workspace_ids.setdefault(analysis_id, uuid4().hex)
        workspace = self._workspace_root / workspace_id
        workspace.mkdir(parents=True, exist_ok=True)
        return workspace

    def _remove_empty_workspace(self, analysis_id: str, workspace: Path) -> None:
        try:
            workspace.rmdir()
        except (FileNotFoundError, OSError):
            return
        with self._lock:
            if self._workspace_ids.get(analysis_id) == workspace.name:
                del self._workspace_ids[analysis_id]
        self._remove_root_if_empty()

    def _remove_root_if_empty(self) -> None:
        try:
            self._workspace_root.rmdir()
        except (FileNotFoundError, OSError):
            pass

    def _find_document(
        self,
        analysis_id: str,
        document_id: str,
    ) -> UploadedDocument:
        for document in self._documents.get(analysis_id, ()):
            if document.document_id == document_id:
                return document
        raise RuntimeError("document index is inconsistent")

    def _inspect_pdf(self, path: Path) -> ParsedPdf:
        try:
            with pymupdf.open(path) as document:
                if not document.is_pdf:
                    raise self._invalid_pdf()
                if document.needs_pass:
                    raise DocumentServiceError(
                        "ENCRYPTED_PDF",
                        "Encrypted PDFs are not supported.",
                        422,
                    )
                if document.page_count <= 0:
                    raise self._invalid_pdf()
                if document.page_count > self._max_page_count:
                    raise DocumentServiceError(
                        "PAGE_LIMIT_EXCEEDED",
                        "The PDF exceeds the configured page limit.",
                        422,
                    )

                spans: list[ParsedSpan] = []
                page_paths: set[ParserPath] = set()
                for page_number, page in enumerate(document, start=1):
                    page_spans = self._extract_page(page, page_number, used_ocr=False)
                    page_path: ParserPath = "text"
                    if not page_spans:
                        page_path = "ocr"
                        try:
                            text_page = page.get_textpage_ocr(
                                language="eng",
                                dpi=150,
                                full=True,
                            )
                        except Exception as error:
                            raise DocumentServiceError(
                                "OCR_FAILED",
                                "A scanned page could not be read locally.",
                                422,
                            ) from error
                        page_spans = self._extract_page(
                            page,
                            page_number,
                            used_ocr=True,
                            text_page=text_page,
                        )
                    page_paths.add(page_path)
                    spans.extend(page_spans)

                if not spans:
                    raise DocumentServiceError(
                        "DOCUMENT_UNREADABLE",
                        "No readable text was found in the PDF.",
                        422,
                    )
                parser_path: ParserPath = (
                    "mixed" if len(page_paths) > 1 else next(iter(page_paths))
                )
                return ParsedPdf(
                    page_count=document.page_count,
                    spans=tuple(spans),
                    parser_path=parser_path,
                )
        except DocumentServiceError:
            raise
        except Exception as error:
            raise self._invalid_pdf() from error

    @staticmethod
    def _extract_page(
        page: pymupdf.Page,
        page_number: int,
        *,
        used_ocr: bool,
        text_page: pymupdf.TextPage | None = None,
    ) -> list[ParsedSpan]:
        blocks = page.get_text("blocks", textpage=text_page, sort=True)
        page_width = max(float(page.rect.width), 1.0)
        page_height = max(float(page.rect.height), 1.0)
        spans: list[ParsedSpan] = []
        for block in blocks:
            if len(block) < 7 or block[6] != 0:
                continue
            text = str(block[4]).strip()
            if not text:
                continue
            spans.append(
                ParsedSpan(
                    page=page_number,
                    x=max(0.0, float(block[0]) / page_width),
                    y=max(0.0, float(block[1]) / page_height),
                    width=min(1.0, max(0.0, float(block[2] - block[0]) / page_width)),
                    height=min(
                        1.0,
                        max(0.0, float(block[3] - block[1]) / page_height),
                    ),
                    text=text,
                    used_ocr=used_ocr,
                )
            )
        return spans

    @staticmethod
    def _validate_idempotency_key(idempotency_key: str | None) -> str:
        key = (idempotency_key or "").strip()
        if not key:
            raise DocumentServiceError(
                "IDEMPOTENCY_KEY_REQUIRED",
                "An Idempotency-Key header is required.",
                400,
            )
        if len(key) > 128 or not all(character.isprintable() for character in key):
            raise DocumentServiceError(
                "INVALID_IDEMPOTENCY_KEY",
                "The Idempotency-Key header is invalid.",
                400,
            )
        return key

    @staticmethod
    def _validate_media_type(media_type: str | None) -> None:
        if media_type != "application/pdf":
            raise DocumentServiceError(
                "UNSUPPORTED_MEDIA_TYPE",
                "Only application/pdf uploads are supported.",
                415,
            )

    @staticmethod
    def _invalid_pdf() -> DocumentServiceError:
        return DocumentServiceError(
            "INVALID_PDF",
            "The uploaded file is not a valid PDF.",
            422,
        )