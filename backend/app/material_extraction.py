from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from threading import RLock
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from .contracts_v2 import (
    DocumentSpan,
    MaterialTerm,
    MaterialTermDecision,
    MaterialTermReviewRequest,
    StatefulValue,
)
from .document_service import DocumentServiceError


PREMIUM_AMOUNT_PATTERN = re.compile(
    r"(?im)\bpremium(?:\s+amount)?\s*:\s*"
    r"(?P<currency>S\$|SGD|\$)\s*"
    r"(?P<amount>\d[\d,]*(?:\.\d{1,2})?)"
)
PREMIUM_FREQUENCY_PATTERN = re.compile(
    r"(?im)\bpremium(?:\s+payment)?\s+frequency\s*:\s*"
    r"(?P<frequency>monthly|quarterly|half[- ]yearly|semi[- ]annually|"
    r"annually|annual|yearly|single premium)\b"
)
PREMIUM_DURATION_PATTERN = re.compile(
    r"(?im)\bpremium\s+payment\s+(?:period|term)\s*:\s*"
    r"(?P<duration>\d+)\s*(?P<unit>years?|months?)\b"
)
INSURER_PATTERN = re.compile(
    r"(?im)^\s*(?:insurer|insurance company)\s*[:\-]\s*"
    r"(?P<value>[^\r\n]{2,160})\s*$"
)
UNDERWRITTEN_BY_PATTERN = re.compile(
    r"(?im)\b(?:insurance plan|policy)\s+is\s+underwritten\s+by\s+"
    r"(?P<value>[A-Z][^\r\n(]{2,160}?)(?=\s*\(|\s*$)"
)
PRODUCT_NAME_PATTERN = re.compile(
    r"(?im)^\s*(?:product|product name|plan name)\s*[:\-]\s*"
    r"(?P<value>[^\r\n]{2,160})\s*$"
)
PLAN_DESCRIPTION_PATTERN = re.compile(
    r"(?im)^\s*(?P<value>[A-Z][A-Za-z0-9 &()'/-]{3,100}?)\s+"
    r"is\s+an?\s+(?:affordable\s+)?plan\b"
)
DOCUMENT_TYPE_PATTERN = re.compile(
    r"(?im)^\s*(?:(?:document type)\s*[:\-]\s*)?"
    r"(?P<value>benefit illustration|policy illustration|policy contract|"
    r"policy schedule|quotation|proposal|brochure)\s*$"
)
BROCHURE_TYPE_PATTERN = re.compile(
    r"(?i)\bthis\s+(?P<value>brochure)\s+is\s+not\s+a\s+contract\b"
)
ISSUE_DATE_PATTERN = re.compile(
    r"(?im)^\s*(?:issue date|date of issue|illustration date|quotation date)"
    r"\s*[:\-]\s*(?P<value>\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}|"
    r"\d{1,2}\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|"
    r"Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|"
    r"Nov(?:ember)?|Dec(?:ember)?)\s+\d{4})\s*$"
)
PUBLICATION_DATE_PATTERN = re.compile(
    r"(?im)\b(?:the\s+)?information\s+is\s+correct\s+as\s+at\s+"
    r"(?P<value>\d{1,2}\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|"
    r"Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|"
    r"Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4})\b"
)
POLICY_STATUS_PATTERN = re.compile(
    r"(?im)^\s*(?:policy|quotation)\s+status\s*[:\-]\s*"
    r"(?P<value>proposed|illustrative|quoted|pending|in force|lapsed|"
    r"cancelled|terminated|matured)\s*$"
)
PREMIUM_ESCALATION_PATTERN = re.compile(
    r"(?im)^\s*(?:premium escalation|premium increase)\s*[:\-]\s*"
    r"(?P<percentage>\d{1,3}(?:\.\d{1,2})?)\s*(?:%|percent)\s*"
    r"(?P<frequency>annually|annual|yearly|per annum)\s*$"
)
COVERAGE_COMMENCEMENT_PATTERN = re.compile(
    r"(?im)^\s*(?:coverage commencement|coverage start date|commencement date)"
    r"\s*[:\-]\s*(?P<value>\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}|"
    r"\d{1,2}\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|"
    r"Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|"
    r"Nov(?:ember)?|Dec(?:ember)?)\s+\d{4})\s*$"
)
COVERAGE_END_PATTERN = re.compile(
    r"(?im)^\s*(?:coverage expiry|expiry date|maturity date)\s*[:\-]\s*"
    r"(?P<value>\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}|"
    r"\d{1,2}\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|"
    r"Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|"
    r"Nov(?:ember)?|Dec(?:ember)?)\s+\d{4})\s*$"
)
FREE_LOOK_PATTERN = re.compile(
    r"(?im)^\s*(?:free[- ]look(?: period)?|cancellation period)\s*[:\-]\s*"
    r"(?P<duration>\d+)\s*(?P<unit>days?|weeks?)\b"
)
ANNUAL_PREMIUM_HEADING_PATTERN = re.compile(
    r"(?im)^\s*annual\s+premium(?:\s|\(|$)"
)
MATERIAL_TERM_TAXONOMY = (
    "premium.amount",
    "premium.frequency",
    "premium.payment_duration",
    "commitment.insurer",
    "commitment.product_name",
    "commitment.document_type",
    "commitment.issue_date",
    "commitment.policy_status",
    "premium.escalation",
    "coverage.commencement",
    "coverage.expiry_or_maturity",
    "exit.free_look_period",
)


@dataclass(frozen=True)
class ExtractionResult:
    spans: tuple[DocumentSpan, ...]
    terms: tuple[MaterialTerm, ...]


class MaterialExtractionService:
    def __init__(self) -> None:
        self._idempotency: dict[tuple[str, str], tuple[str, ExtractionResult]] = {}
        self._results: dict[str, ExtractionResult] = {}
        self._review_idempotency: dict[
            tuple[str, str], tuple[str, ExtractionResult]
        ] = {}
        self._lock = RLock()

    def extract(
        self,
        analysis_id: str,
        spans: list[DocumentSpan],
        idempotency_key: str | None,
    ) -> ExtractionResult:
        key = self._validate_idempotency_key(idempotency_key)
        fingerprint = hashlib.sha256(
            "".join(span.content_sha256 for span in spans).encode()
        ).hexdigest()
        with self._lock:
            previous = self._idempotency.get((analysis_id, key))
            if previous is not None:
                previous_fingerprint, previous_result = previous
                if previous_fingerprint != fingerprint:
                    raise DocumentServiceError(
                        "IDEMPOTENCY_CONFLICT",
                        "The idempotency key was already used for another payload.",
                        409,
                    )
                return previous_result

        amount_candidates: list[tuple[dict[str, str], str]] = []
        frequency_candidates: list[tuple[str, str]] = []
        duration_candidates: list[tuple[dict[str, Any], str]] = []
        taxonomy_candidates: dict[str, list[tuple[Any, str]]] = {
            "commitment.insurer": [],
            "commitment.product_name": [],
            "commitment.document_type": [],
            "commitment.issue_date": [],
            "commitment.policy_status": [],
            "premium.escalation": [],
            "coverage.commencement": [],
            "coverage.expiry_or_maturity": [],
            "exit.free_look_period": [],
        }
        for span in spans:
            for match in PREMIUM_AMOUNT_PATTERN.finditer(span.redacted_text):
                currency = match.group("currency")
                amount_candidates.append(
                    (
                        {
                            "amount": format(
                                Decimal(match.group("amount").replace(",", "")),
                                "f",
                            ),
                            "currency": "SGD" if currency in {"S$", "SGD", "$"} else currency,
                        },
                        span.span_id,
                    )
                )
            for match in PREMIUM_FREQUENCY_PATTERN.finditer(span.redacted_text):
                frequency_candidates.append(
                    (self._normalize_frequency(match.group("frequency")), span.span_id)
                )
            if ANNUAL_PREMIUM_HEADING_PATTERN.search(span.redacted_text):
                frequency_candidates.append(("annual", span.span_id))
            for match in PREMIUM_DURATION_PATTERN.finditer(span.redacted_text):
                duration_candidates.append(
                    (
                        {
                            "duration": int(match.group("duration")),
                            "unit": self._normalize_duration_unit(match.group("unit")),
                        },
                        span.span_id,
                    )
                )
            self._append_match(
                taxonomy_candidates["commitment.insurer"],
                INSURER_PATTERN,
                span,
                self._normalize_text,
            )
            self._append_match(
                taxonomy_candidates["commitment.insurer"],
                UNDERWRITTEN_BY_PATTERN,
                span,
                self._normalize_text,
            )
            self._append_match(
                taxonomy_candidates["commitment.product_name"],
                PRODUCT_NAME_PATTERN,
                span,
                self._normalize_text,
            )
            self._append_match(
                taxonomy_candidates["commitment.product_name"],
                PLAN_DESCRIPTION_PATTERN,
                span,
                self._normalize_text,
            )
            self._append_match(
                taxonomy_candidates["commitment.document_type"],
                DOCUMENT_TYPE_PATTERN,
                span,
                self._normalize_document_type,
            )
            self._append_match(
                taxonomy_candidates["commitment.document_type"],
                BROCHURE_TYPE_PATTERN,
                span,
                self._normalize_document_type,
            )
            self._append_match(
                taxonomy_candidates["commitment.issue_date"],
                ISSUE_DATE_PATTERN,
                span,
                self._normalize_date,
            )
            self._append_match(
                taxonomy_candidates["commitment.issue_date"],
                PUBLICATION_DATE_PATTERN,
                span,
                self._normalize_date,
            )
            self._append_match(
                taxonomy_candidates["commitment.policy_status"],
                POLICY_STATUS_PATTERN,
                span,
                self._normalize_choice,
            )
            for match in PREMIUM_ESCALATION_PATTERN.finditer(span.redacted_text):
                taxonomy_candidates["premium.escalation"].append(
                    (
                        {
                            "percentage": format(
                                Decimal(match.group("percentage")),
                                "f",
                            ),
                            "frequency": "annual",
                        },
                        span.span_id,
                    )
                )
            self._append_match(
                taxonomy_candidates["coverage.commencement"],
                COVERAGE_COMMENCEMENT_PATTERN,
                span,
                self._normalize_date,
            )
            self._append_match(
                taxonomy_candidates["coverage.expiry_or_maturity"],
                COVERAGE_END_PATTERN,
                span,
                self._normalize_date,
            )
            for match in FREE_LOOK_PATTERN.finditer(span.redacted_text):
                taxonomy_candidates["exit.free_look_period"].append(
                    (
                        {
                            "duration": int(match.group("duration")),
                            "unit": self._normalize_period_unit(match.group("unit")),
                        },
                        span.span_id,
                    )
                )

        terms = (
            self._term(analysis_id, "premium.amount", amount_candidates, fingerprint),
            self._term(
                analysis_id,
                "premium.frequency",
                frequency_candidates,
                fingerprint,
            ),
            self._term(
                analysis_id,
                "premium.payment_duration",
                duration_candidates,
                fingerprint,
            ),
            *(
                self._term(
                    analysis_id,
                    taxonomy_key,
                    candidates,
                    fingerprint,
                )
                for taxonomy_key, candidates in taxonomy_candidates.items()
            ),
        )
        result = ExtractionResult(spans=tuple(spans), terms=terms)
        with self._lock:
            self._idempotency[(analysis_id, key)] = (fingerprint, result)
            self._results[analysis_id] = result
        return result


    def review(
        self,
        analysis_id: str,
        request: MaterialTermReviewRequest,
        idempotency_key: str | None,
    ) -> ExtractionResult:
        key = self._validate_idempotency_key(idempotency_key)
        payload_sha256 = hashlib.sha256(
            json.dumps(
                request.model_dump(mode="json"),
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()

        with self._lock:
            previous = self._review_idempotency.get((analysis_id, key))
            if previous is not None:
                previous_hash, previous_result = previous
                if previous_hash != payload_sha256:
                    raise DocumentServiceError(
                        "IDEMPOTENCY_CONFLICT",
                        "The idempotency key was already used for another payload.",
                        409,
                    )
                return previous_result

            current = self._results.get(analysis_id)
            if current is None:
                raise DocumentServiceError(
                    "EXTRACTION_REQUIRED",
                    "Extract material terms before reviewing them.",
                    409,
                )
            decisions = {decision.term_id: decision for decision in request.decisions}
            known_term_ids = {term.term_id for term in current.terms}
            if not set(decisions).issubset(known_term_ids):
                raise DocumentServiceError(
                    "MATERIAL_TERM_NOT_FOUND",
                    "A material term does not exist in the current extraction.",
                    404,
                )
            known_span_ids = {span.span_id for span in current.spans}
            for decision in request.decisions:
                if not set(decision.source_span_ids).issubset(known_span_ids):
                    raise DocumentServiceError(
                        "INVALID_TERM_SOURCE",
                        "A material term references an unavailable source span.",
                        422,
                    )
                if decision.value.state == "present" and not decision.source_span_ids:
                    raise DocumentServiceError(
                        "TERM_SOURCE_REQUIRED",
                        "Present material terms require a source span.",
                        422,
                    )

            reviewed_terms = tuple(
                self._apply_decision(term, decisions.get(term.term_id))
                for term in current.terms
            )
            reviewed = ExtractionResult(spans=current.spans, terms=reviewed_terms)
            self._results[analysis_id] = reviewed
            self._review_idempotency[(analysis_id, key)] = (
                payload_sha256,
                reviewed,
            )
            return reviewed

    def delete_analysis(self, analysis_id: str) -> None:
        with self._lock:
            self._results.pop(analysis_id, None)
            keys = [key for key in self._idempotency if key[0] == analysis_id]
            for key in keys:
                del self._idempotency[key]
            review_keys = [
                key for key in self._review_idempotency if key[0] == analysis_id
            ]
            for key in review_keys:
                del self._review_idempotency[key]

    @staticmethod
    def _apply_decision(
        term: MaterialTerm,
        decision: MaterialTermDecision | None,
    ) -> MaterialTerm:
        if decision is None:
            return term
        changed = (
            decision.value != term.value
            or decision.source_span_ids != term.source_span_ids
        )
        return term.model_copy(
            update={
                "value": decision.value,
                "source_span_ids": decision.source_span_ids,
                "extraction_method": "user" if changed else term.extraction_method,
                "confirmed": True,
            }
        )

    @staticmethod
    def _term(
        analysis_id: str,
        taxonomy_key: str,
        candidates: list[tuple[Any, str]],
        fingerprint: str,
    ) -> MaterialTerm:
        unique_values = {
            MaterialExtractionService._candidate_key(value)
            for value, _ in candidates
        }
        source_span_ids = list(dict.fromkeys(span_id for _, span_id in candidates))
        if len(unique_values) == 1:
            value = candidates[0][0]
            stateful_value = StatefulValue[Any](state="present", value=value)
            confidence = 0.99
        else:
            stateful_value = StatefulValue[Any](state="unknown")
            confidence = 0.0 if not candidates else 0.5

        return MaterialTerm(
            term_id=str(
                uuid5(
                    NAMESPACE_URL,
                    f"{analysis_id}:{taxonomy_key}:{fingerprint}",
                )
            ),
            analysis_id=analysis_id,
            taxonomy_key=taxonomy_key,
            value=stateful_value,
            confidence=confidence,
            source_span_ids=source_span_ids,
            extraction_method="deterministic",
        )

    @staticmethod
    def _normalize_frequency(value: str) -> str:
        normalized = value.lower().replace(" ", "-")
        aliases = {
            "annual": "annual",
            "annually": "annual",
            "yearly": "annual",
            "half-yearly": "semi-annual",
            "semi-annually": "semi-annual",
            "single-premium": "single",
        }
        return aliases.get(normalized, normalized)

    @staticmethod
    def _normalize_duration_unit(value: str) -> str:
        return "years" if value.lower().startswith("year") else "months"

    @staticmethod
    def _normalize_period_unit(value: str) -> str:
        return "weeks" if value.lower().startswith("week") else "days"

    @staticmethod
    def _normalize_text(value: str) -> str:
        return " ".join(value.split()).strip(" .")

    @staticmethod
    def _normalize_choice(value: str) -> str:
        return MaterialExtractionService._normalize_text(value).casefold()

    @staticmethod
    def _normalize_document_type(value: str) -> str:
        return MaterialExtractionService._normalize_choice(value).replace(" ", "_")

    @staticmethod
    def _candidate_key(value: Any) -> str:
        comparable = value.casefold() if isinstance(value, str) else value
        return json.dumps(comparable, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _normalize_date(value: str) -> str:
        normalized = " ".join(value.split())
        for date_format in ("%Y-%m-%d", "%d/%m/%Y", "%d %B %Y", "%d %b %Y"):
            try:
                return datetime.strptime(normalized, date_format).date().isoformat()
            except ValueError:
                continue
        raise ValueError(f"unsupported date value: {value}")

    @staticmethod
    def _append_match(
        candidates: list[tuple[Any, str]],
        pattern: re.Pattern[str],
        span: DocumentSpan,
        normalize: Callable[[str], Any],
    ) -> None:
        for match in pattern.finditer(span.redacted_text):
            candidates.append((normalize(match.group("value")), span.span_id))

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