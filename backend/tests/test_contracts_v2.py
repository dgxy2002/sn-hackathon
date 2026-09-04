from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.contracts_v2 import (
    AnalysisSession,
    ClaimAssessment,
    DocumentSpan,
    GuidanceEvidence,
    MaterialTerm,
    ModelConsent,
    SourceRegion,
    StatefulValue,
)


NOW = datetime(2026, 9, 4, tzinfo=UTC)
SHA256 = "a" * 64


def test_stateful_value_distinguishes_absent_unknown_and_zero() -> None:
    assert StatefulValue[int](state="present", value=0).value == 0
    assert StatefulValue[int](state="absent").value is None
    assert StatefulValue[int](state="unknown").value is None

    with pytest.raises(ValidationError, match="require a value"):
        StatefulValue[int](state="present")

    with pytest.raises(ValidationError, match="cannot have a value"):
        StatefulValue[int](state="unreadable", value=12)


def test_model_consent_and_session_expiry_fail_closed() -> None:
    with pytest.raises(ValidationError, match="requires acknowledged_at"):
        ModelConsent(enabled=True)

    with pytest.raises(ValidationError, match="later than created_at"):
        AnalysisSession(
            analysis_id="analysis-1",
            purpose="considering_offer",
            created_at=NOW,
            expires_at=NOW - timedelta(seconds=1),
        )


def test_present_material_term_requires_private_source_span() -> None:
    with pytest.raises(ValidationError, match="require a source span"):
        MaterialTerm(
            term_id="term-1",
            analysis_id="analysis-1",
            taxonomy_key="premium.amount",
            value=StatefulValue[float](state="present", value=125.0),
            confidence=0.99,
            extraction_method="deterministic",
        )

    span = DocumentSpan(
        span_id="span-1",
        analysis_id="analysis-1",
        document_id="document-1",
        region=SourceRegion(page=2),
        redacted_text="Annual premium: $1,500",
        content_sha256=SHA256,
        parser_version="test-1",
    )
    assert span.evidence_plane == "private_bundle"


def test_claim_assessment_requires_status_specific_evidence() -> None:
    with pytest.raises(ValidationError, match="supporting evidence"):
        ClaimAssessment(
            assessment_id="assessment-1",
            claim_id="claim-1",
            status="supported",
            reason_codes=["EXACT_TEXT_MATCH"],
        )

    with pytest.raises(ValidationError, match="unresolved conditions"):
        ClaimAssessment(
            assessment_id="assessment-1",
            claim_id="claim-1",
            status="supported_with_conditions",
            reason_codes=["CONDITIONAL_TEXT_MATCH"],
            supporting_span_ids=["span-1"],
        )


def test_public_guidance_cannot_be_mislabelled_as_private_evidence() -> None:
    with pytest.raises(ValidationError):
        GuidanceEvidence(
            evidence_id="evidence-1",
            evidence_plane="private_bundle",
            source_id="moneysense",
            chunk_id="chunk-1",
            url="https://www.moneysense.gov.sg/insurance-basics/",
            title="Insurance basics",
            publisher="MoneySense",
            snippet="Read the documents carefully.",
            content_sha256=SHA256,
            chunk_sha256=SHA256,
            crawled_at=NOW,
            retrieval_method="lexical",
            retrieval_score=1.0,
            index_version="test-1",
        )