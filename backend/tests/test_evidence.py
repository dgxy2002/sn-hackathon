import json

import pytest

from app.config import ConfigurationError, Settings
from app.contracts import EvidenceSearchRequest
from app.evidence import (
    DEFAULT_CORPUS,
    EvidenceDependencyError,
    EvidenceService,
    LocalCorpusEvidenceAdapter,
    SupabaseEvidenceAdapter,
)
from app.main import create_app
from tests.support import request


def test_cached_evidence_search_returns_real_source_provenance() -> None:
    app = create_app(Settings.from_env({"APP_ENV": "test", "EVIDENCE_MODE": "cached"}))

    response = request(
        app,
        "POST",
        "/v1/evidence/search",
        json={"query": "critical illness protection", "max_results": 3},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["contract_version"] == "1.0.0"
    assert payload["mode"] == "cached"
    assert payload["status"] == "matched"
    assert payload["match_count"] == len(payload["evidence"])
    assert 1 <= payload["match_count"] <= 3

    evidence = payload["evidence"][0]
    assert evidence["provider"] in {"AIA", "FWD", "Great Eastern", "Singlife"}
    assert evidence["product"]
    assert evidence["value"]
    assert evidence["source_file"].endswith(".md")
    assert evidence["source_approval"] == "unverified"
    assert evidence["evidence_state"] in {"unverified", "stale"}
    assert evidence["freshness_status"] in {"current", "stale", "unknown"}
    assert evidence["synthetic"] is False
    assert evidence["product_effective_date"] is None
    assert evidence["retrieved_at"] is None
    assert 0 < evidence["similarity"] <= 1
    assert "search_context" not in evidence["provenance"]


def test_cached_evidence_search_returns_explicit_no_evidence() -> None:
    app = create_app(Settings.from_env({"APP_ENV": "test", "EVIDENCE_MODE": "cached"}))

    response = request(
        app,
        "POST",
        "/v1/evidence/search",
        json={"query": "zyxwvutsrqponmlkjihgfedcba", "max_results": 5},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "no_evidence"
    assert response.json()["match_count"] == 0
    assert response.json()["evidence"] == []


def test_cached_adapter_indexes_all_normalized_policy_slugs() -> None:
    expected_slugs = {
        row["policy"]["slug"]
        for line in DEFAULT_CORPUS.read_text(encoding="utf-8").splitlines()
        if line.strip()
        for row in [json.loads(line)]
    }
    adapter = LocalCorpusEvidenceAdapter()
    indexed_slugs = {document.record.policy_id for document in adapter._documents}

    assert len(expected_slugs) == 71
    assert indexed_slugs == expected_slugs


def test_cached_evidence_filters_before_ranking_and_retains_pdf_metadata() -> None:
    app = create_app(Settings.from_env({"APP_ENV": "test", "EVIDENCE_MODE": "cached"}))

    response = request(
        app,
        "POST",
        "/v1/evidence/search",
        json={
            "query": "GREAT Life Advantage critical illness",
            "max_results": 5,
            "filters": {
                "provider": "Great Eastern",
                "product": "GREAT Life Advantage 4",
            },
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "matched"
    assert all(
        item["provider"] == "Great Eastern"
        and item["product"] == "GREAT Life Advantage 4"
        and item["document_as_of_date"] == "2025-10-17"
        and item["document_version"] == "GLA4P/Ver3.0/202510"
        for item in response.json()["evidence"]
    )


def test_synthetic_adapter_uses_same_contract_and_clear_labels() -> None:
    app = create_app(
        Settings.from_env({"APP_ENV": "test", "EVIDENCE_MODE": "synthetic"})
    )

    response = request(
        app,
        "POST",
        "/v1/evidence/search",
        json={"query": "critical illness", "max_results": 2},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "synthetic"
    assert payload["status"] == "matched"
    assert all(item["synthetic"] is True for item in payload["evidence"])
    assert set(payload["evidence"][0]) == {
        "evidence_id",
        "policy_id",
        "provider",
        "product",
        "category",
        "field",
        "section_title",
        "value",
        "source_url",
        "source_file",
        "source_approval",
        "evidence_state",
        "freshness_status",
        "document_as_of_date",
        "product_effective_date",
        "retrieved_at",
        "document_version",
        "synthetic",
        "extraction_confidence",
        "similarity",
        "provenance",
    }


def test_supabase_adapter_maps_live_results_to_the_shared_contract(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    from scraper import rag_common

    captured: dict[str, object] = {}

    class FakeEmbeddingCache:
        def __init__(self, path) -> None:
            captured["cache_path"] = path

        def close(self) -> None:
            captured["cache_closed"] = True

    class FakeEmbeddings:
        def __init__(self, **kwargs) -> None:
            captured["embedding_configuration"] = kwargs

        def embed_with_cache(self, texts, cache, batch_size):
            return [[0.25, 0.75]]

    class FakeSupabase:
        def __init__(self, url, key, timeout) -> None:
            captured["database_url"] = url
            captured["database_key"] = key

        def rpc(self, function, payload):
            captured["rpc"] = (function, payload)
            return [
                {
                    "id": "EVD-LIVE-01",
                    "source_id": "provider-policy",
                    "source_label": "Critical illness benefit",
                    "chunk_text": "A quoted provider benefit.",
                    "similarity": 0.91,
                    "metadata": {
                        "insurer": "Provider",
                        "policy_name": "Provider Policy",
                        "category": "critical_illness",
                        "section_kind": "benefit",
                        "source_file": "Provider/Policy.md",
                        "source_approval": "approved",
                        "evidence_state": "approved",
                        "brochure_url": "https://example.com/policy.pdf",
                        "document_as_of_date": "2026-08-01",
                        "product_effective_date": "2026-08-15",
                        "retrieved_at": "2026-08-20T12:00:00Z",
                        "document_version": "v1",
                    },
                }
            ]

    monkeypatch.setattr(rag_common, "EmbeddingCache", FakeEmbeddingCache)
    monkeypatch.setattr(rag_common, "BedrockEmbeddings", FakeEmbeddings)
    monkeypatch.setattr(rag_common, "SupabaseREST", FakeSupabase)
    service = EvidenceService(
        SupabaseEvidenceAdapter(
            supabase_url="https://database.example",
            service_key="test-service-key",
            bedrock_region="us-east-1",
            cache_path=tmp_path / "embeddings.sqlite3",
        )
    )

    response = service.search(
        EvidenceSearchRequest(
            query="critical illness",
            filters={"provider": "Provider", "category": "critical_illness"},
        )
    )

    assert response.mode == "live"
    assert response.status == "matched"
    assert response.match_count == 1
    assert response.evidence[0].model_dump(mode="json") == {
        "evidence_id": "EVD-LIVE-01",
        "policy_id": "provider-policy",
        "provider": "Provider",
        "product": "Provider Policy",
        "category": "critical_illness",
        "field": "benefit",
        "section_title": "Critical illness benefit",
        "value": "A quoted provider benefit.",
        "source_url": "https://example.com/policy.pdf",
        "source_file": "Provider/Policy.md",
        "source_approval": "approved",
        "evidence_state": "approved",
        "freshness_status": "current",
        "document_as_of_date": "2026-08-01",
        "product_effective_date": "2026-08-15",
        "retrieved_at": "2026-08-20T12:00:00Z",
        "document_version": "v1",
        "synthetic": False,
        "extraction_confidence": None,
        "similarity": 0.91,
        "provenance": {
            "lineage": "supabase-pgvector",
            "metadata": {
                "insurer": "Provider",
                "policy_name": "Provider Policy",
                "category": "critical_illness",
                "section_kind": "benefit",
                "source_file": "Provider/Policy.md",
                "source_approval": "approved",
                "evidence_state": "approved",
                "brochure_url": "https://example.com/policy.pdf",
                "document_as_of_date": "2026-08-01",
                "product_effective_date": "2026-08-15",
                "retrieved_at": "2026-08-20T12:00:00Z",
                "document_version": "v1",
            },
        },
    }
    assert captured["cache_closed"] is True
    assert captured["embedding_configuration"] == {
        "model": "amazon.titan-embed-text-v2:0",
        "dimensions": 1024,
        "region_name": "us-east-1",
        "timeout": 20,
        "max_attempts": 2,
    }
    assert captured["rpc"] == (
        "match_documents_by_type",
        {
            "query_embedding": [0.25, 0.75],
            "p_source_type": "policy",
            "match_threshold": 0.05,
            "match_count": 5,
            "filter_metadata": {
                "company": "Provider",
                "category": "critical_illness",
            },
        },
    )


def test_evidence_request_rejects_unknown_fields() -> None:
    app = create_app(Settings.from_env({"APP_ENV": "test"}))

    response = request(
        app,
        "POST",
        "/v1/evidence/search",
        json={"query": "critical illness", "unknown_filter": "ignored"},
    )

    assert response.status_code == 422


def test_live_evidence_mode_requires_all_dependencies() -> None:
    with pytest.raises(ConfigurationError, match="Live evidence"):
        Settings.from_env({"APP_ENV": "test", "EVIDENCE_MODE": "live"})

    settings = Settings.from_env(
        {
            "APP_ENV": "test",
            "EVIDENCE_MODE": "live",
            "SUPABASE_URL": "https://database.example",
            "SUPABASE_SERVICE_ROLE_KEY": "test-service-key",
            "AWS_REGION": "us-east-1",
        }
    )
    assert settings.bedrock_embedding_model_id == "amazon.titan-embed-text-v2:0"
    assert settings.bedrock_embedding_dimensions == 1024


def test_evidence_dependency_failure_uses_safe_typed_error() -> None:
    class FailingAdapter:
        mode = "cached"

        def search(self, search_request: EvidenceSearchRequest):
            raise EvidenceDependencyError("private upstream details")

    app = create_app(
        Settings.from_env({"APP_ENV": "test"}),
        evidence_service=EvidenceService(FailingAdapter()),
    )

    response = request(
        app,
        "POST",
        "/v1/evidence/search",
        json={"query": "critical illness"},
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "EVIDENCE_DEPENDENCY_UNAVAILABLE"
    assert response.json()["error"]["retryable"] is True
    assert response.json()["error"]["details"] == {"mode": "cached"}
    assert "private upstream details" not in response.text
