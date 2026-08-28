from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4

from .config import CapabilityMode
from .contracts import (
    CONTRACT_VERSION,
    EvidenceRecord,
    EvidenceComparisonField,
    EvidenceComparisonProduct,
    EvidenceComparisonRequest,
    EvidenceComparisonResponse,
    EvidenceSearchRequest,
    EvidenceSearchResponse,
    EvidenceState,
    FreshnessStatus,
    SourceApproval,
)


BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS = (
    BACKEND_ROOT / "scraper" / "insurance" / "extracted_openai" / "policies.jsonl"
)
DEFAULT_EMBEDDING_CACHE = (
    BACKEND_ROOT
    / "scraper"
    / "insurance"
    / "extracted_openai"
    / "rag_embedding_cache.sqlite3"
)
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_EMBEDDING_DIMENSIONS = 1536
STOP_WORDS = {
    "a",
    "about",
    "all",
    "an",
    "and",
    "are",
    "for",
    "from",
    "in",
    "is",
    "it",
    "me",
    "of",
    "on",
    "only",
    "or",
    "plan",
    "plans",
    "show",
    "that",
    "the",
    "to",
    "what",
    "which",
    "with",
}
DATE_PATTERNS = (
    re.compile(
        r"(?:information|details)[^.\n]{0,80}?(?:correct|accurate)[^.\n]{0,40}?"
        r"as\s+(?:at|of)\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:correct|accurate)\s+as\s+(?:at|of)\s+"
        r"(\d{1,2}\s+[A-Za-z]+\s+\d{4})",
        re.IGNORECASE,
    ),
)
VERSION_PATTERN = re.compile(
    r"\b([A-Z][A-Z0-9-]{1,20}/Ver(?:sion)?\s*[0-9.]+/[0-9]{6})\b",
    re.IGNORECASE,
)
PDF_ONLY_METADATA: dict[str, tuple[date, str]] = {
    "Great Eastern/Life Insurance/GREAT Life Advantage 4.md": (
        date(2025, 10, 17),
        "GLA4P/Ver3.0/202510",
    ),
    "Great Eastern/Critical Illness Insurance/GREAT Life Advantage 4.md": (
        date(2025, 10, 17),
        "GLA4P/Ver3.0/202510",
    ),
    "Great Eastern/Life Insurance/GREAT Life Multiplier.md": (
        date(2025, 10, 1),
        "GLM/Ver4.0/202510",
    ),
    "Great Eastern/Critical Illness Insurance/GREAT Life Multiplier.md": (
        date(2025, 10, 1),
        "GLM/Ver4.0/202510",
    ),
    "Great Eastern/Health Insurance/PayAssure.md": (
        date(2026, 8, 17),
        "PAP/Ver 1.0/202608",
    ),
    "Great Eastern/Personal Accident Insurance/PA Supreme.md": (
        date(2026, 8, 17),
        "PASP/Ver 1.0/202608",
    ),
    "Great Eastern/Health Insurance/GREAT SupremeHealth.md": (
        date(2026, 4, 1),
        "GSHP/Ver1.0/202604",
    ),
}


class EvidenceDependencyError(RuntimeError):
    pass


class EvidenceAdapter(Protocol):
    mode: CapabilityMode

    def search(self, request: EvidenceSearchRequest) -> list[EvidenceRecord]: ...

    def records_for_products(self, product_ids: list[str]) -> list[EvidenceRecord]: ...


class EvidenceComparisonEligibilityError(ValueError):
    def __init__(self, reasons: dict[str, list[str]]) -> None:
        super().__init__("One or more products failed the evidence comparison gate")
        self.reasons = reasons


@dataclass(frozen=True)
class SearchDocument:
    record: EvidenceRecord
    search_text: str
    terms: Counter[str]


def _tokens(value: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[a-z0-9]+", value.casefold())
        if len(token) > 1 and token not in STOP_WORDS
    ]


def _parse_date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _parse_datetime(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _freshness(
    document_as_of_date: date | None, max_age_days: int
) -> FreshnessStatus:
    if document_as_of_date is None:
        return "unknown"
    return (
        "stale"
        if (date.today() - document_as_of_date).days > max_age_days
        else "current"
    )


def _evidence_state(
    source_file: str, freshness_status: FreshnessStatus
) -> EvidenceState:
    if source_file.endswith("GREAT SupremeHealth.md"):
        return "conflicting"
    if freshness_status == "stale":
        return "stale"
    return "unverified"


def _document_metadata(source_file: str) -> tuple[date | None, str | None]:
    known = PDF_ONLY_METADATA.get(source_file)
    if known is not None:
        return known

    path = BACKEND_ROOT / "scraper" / "insurance" / source_file
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None, None

    document_date = None
    for pattern in DATE_PATTERNS:
        match = pattern.search(text)
        if match is None:
            continue
        try:
            document_date = datetime.strptime(match.group(1), "%d %B %Y").date()
        except ValueError:
            continue
        break

    version_match = VERSION_PATTERN.search(text)
    document_version = version_match.group(1) if version_match else None
    return document_date, document_version


def _entity_text(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _quote_records(
    policy: dict[str, Any],
    source: dict[str, Any],
    *,
    max_age_days: int,
) -> list[EvidenceRecord]:
    policy_id = str(policy.get("slug") or source.get("content_sha256") or "unknown-policy")
    provider = str(policy.get("company") or source.get("company") or "Unknown provider")
    product = str(policy.get("policy_name") or source.get("source_filename") or "Unknown product")
    category = str(policy.get("category") or "unknown")
    source_file = str(source.get("source_file") or "unknown")
    document_as_of_date, document_version = _document_metadata(source_file)
    freshness_status = _freshness(document_as_of_date, max_age_days)
    evidence_state = _evidence_state(source_file, freshness_status)
    confidence = policy.get("extraction_confidence")
    content_hash = str(source.get("content_sha256") or "")
    common_provenance = {
        "content_sha256": content_hash or None,
        "document_type": source.get("document_type"),
        "local_markdown_path": source.get("local_markdown_path"),
        "lineage": "openai-structured-extraction",
    }

    sections: list[tuple[str, str, str, list[dict[str, Any]]]] = [
        (
            "overview",
            product,
            " ".join(
                str(value)
                for value in (
                    policy.get("quick_summary"),
                    policy.get("target_customer"),
                    policy.get("coverage_scope"),
                    policy.get("eligibility_notes"),
                    policy.get("important_caveats"),
                )
                if value
            ),
            policy.get("source_evidence") or [],
        )
    ]
    collection_specs = (
        ("benefit", "benefits", "benefit_name"),
        ("plan", "plans", "plan_name"),
        ("rider", "riders", "rider_name"),
        ("exclusion", "exclusions", "exclusion"),
    )
    for field, collection_name, title_key in collection_specs:
        for entity in policy.get(collection_name) or []:
            if not isinstance(entity, dict):
                continue
            title = str(
                entity.get(title_key)
                or entity.get("name")
                or entity.get("description")
                or field.title()
            )
            sections.append(
                (field, title, _entity_text(entity), entity.get("evidence") or [])
            )

    records: list[EvidenceRecord] = []
    seen: set[tuple[str, str]] = set()
    for field, section_title, context, quotes in sections:
        for quote in quotes:
            value = str(quote.get("quote") or "").strip()
            dedupe_key = (field, value)
            if not value or dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            identity = f"{content_hash}|{policy_id}|{field}|{value}".encode("utf-8")
            evidence_id = f"EVD-{hashlib.sha256(identity).hexdigest()[:20]}"
            records.append(
                EvidenceRecord(
                    evidence_id=evidence_id,
                    policy_id=policy_id,
                    provider=provider,
                    product=product,
                    category=category,
                    field=field,
                    section_title=section_title,
                    value=value,
                    source_url=None,
                    source_file=source_file,
                    source_approval="unverified",
                    evidence_state=evidence_state,
                    freshness_status=freshness_status,
                    document_as_of_date=document_as_of_date,
                    product_effective_date=None,
                    retrieved_at=None,
                    document_version=document_version,
                    synthetic=False,
                    extraction_confidence=(str(confidence) if confidence else None),
                    similarity=0,
                    provenance={
                        **common_provenance,
                        "line_start": quote.get("line_start"),
                        "line_end": quote.get("line_end"),
                        "search_context": context,
                    },
                )
            )
    return records


class LocalCorpusEvidenceAdapter:
    mode: CapabilityMode = "cached"

    def __init__(
        self,
        corpus_path: Path = DEFAULT_CORPUS,
        *,
        max_age_days: int = 365,
    ) -> None:
        try:
            rows = [
                json.loads(line)
                for line in corpus_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        except (OSError, json.JSONDecodeError) as error:
            raise EvidenceDependencyError(
                f"Cached evidence corpus could not be loaded: {error}"
            ) from error

        records = [
            record
            for row in rows
            for record in _quote_records(
                row.get("policy") or {},
                row.get("source_document") or {},
                max_age_days=max_age_days,
            )
        ]
        if not records:
            raise EvidenceDependencyError("Cached evidence corpus contains no quoted evidence")

        self._documents = [
            SearchDocument(
                record=record,
                search_text=" ".join(
                    (
                        record.provider,
                        record.product,
                        record.category.replace("_", " "),
                        record.field,
                        record.section_title,
                        record.value,
                        str(record.provenance.get("search_context") or ""),
                    )
                ).casefold(),
                terms=Counter(
                    _tokens(
                        " ".join(
                            (
                                record.provider,
                                record.product,
                                record.category.replace("_", " "),
                                record.field,
                                record.section_title,
                                record.value,
                                str(record.provenance.get("search_context") or ""),
                            )
                        )
                    )
                ),
            )
            for record in records
        ]
        document_frequency: Counter[str] = Counter()
        for document in self._documents:
            document_frequency.update(document.terms.keys())
        total = len(self._documents)
        self._idf = {
            term: math.log((total + 1) / (frequency + 1)) + 1
            for term, frequency in document_frequency.items()
        }

    def search(self, request: EvidenceSearchRequest) -> list[EvidenceRecord]:
        query_terms = Counter(_tokens(request.query))
        if not query_terms:
            return []
        query_norm = math.sqrt(
            sum((count * self._idf.get(term, 1)) ** 2 for term, count in query_terms.items())
        )
        filters = request.filters
        scored: list[tuple[float, SearchDocument]] = []
        for document in self._documents:
            record = document.record
            if filters.provider and record.provider.casefold() != filters.provider.casefold():
                continue
            if filters.category and record.category.casefold() != filters.category.casefold():
                continue
            if filters.product and filters.product.casefold() not in record.product.casefold():
                continue

            shared_terms = set(query_terms) & set(document.terms)
            if not shared_terms:
                continue
            dot_product = sum(
                query_terms[term]
                * document.terms[term]
                * self._idf.get(term, 1) ** 2
                for term in shared_terms
            )
            document_norm = math.sqrt(
                sum(
                    (count * self._idf.get(term, 1)) ** 2
                    for term, count in document.terms.items()
                )
            )
            score = dot_product / (query_norm * document_norm or 1)
            normalized_query = " ".join(_tokens(request.query))
            if normalized_query and normalized_query in document.search_text:
                score = min(1, score + 0.15)
            if score >= request.threshold:
                scored.append((score, document))

        scored.sort(
            key=lambda item: (
                -item[0],
                item[1].record.provider,
                item[1].record.product,
                item[1].record.evidence_id,
            )
        )
        selected: list[EvidenceRecord] = []
        seen_policies: set[str] = set()
        for score, document in scored:
            if document.record.policy_id in seen_policies:
                continue
            seen_policies.add(document.record.policy_id)
            selected.append(
                document.record.model_copy(
                    update={
                        "similarity": round(score, 6),
                        "provenance": {
                            key: value
                            for key, value in document.record.provenance.items()
                            if key != "search_context"
                        },
                    }
                )
            )
            if len(selected) == request.max_results:
                break
        return selected

    def records_for_products(self, product_ids: list[str]) -> list[EvidenceRecord]:
        selected = set(product_ids)
        return [
            document.record
            for document in self._documents
            if document.record.policy_id in selected
        ]


class PostgresEvidenceAdapter:
    mode: CapabilityMode = "cached"

    def __init__(
        self,
        database_url: str,
        corpus_path: Path = DEFAULT_CORPUS,
        *,
        max_age_days: int = 365,
    ) -> None:
        self._database_url = database_url
        corpus = LocalCorpusEvidenceAdapter(corpus_path, max_age_days=max_age_days)
        records = [document.record for document in corpus._documents]
        try:
            import psycopg

            with psycopg.connect(self._database_url) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        CREATE TABLE IF NOT EXISTS evidence_records (
                            evidence_id TEXT PRIMARY KEY,
                            policy_id TEXT NOT NULL,
                            provider TEXT NOT NULL,
                            product TEXT NOT NULL,
                            category TEXT NOT NULL,
                            field_name TEXT NOT NULL,
                            payload JSONB NOT NULL,
                            search_document TSVECTOR GENERATED ALWAYS AS (
                                to_tsvector(
                                    'simple',
                                    provider || ' ' || product || ' ' || category || ' ' ||
                                    field_name || ' ' || coalesce(payload ->> 'section_title', '') ||
                                    ' ' || coalesce(payload ->> 'value', '')
                                )
                            ) STORED
                        )
                        """
                    )
                    cursor.execute(
                        "CREATE INDEX IF NOT EXISTS evidence_records_search_idx "
                        "ON evidence_records USING GIN (search_document)"
                    )
                    cursor.executemany(
                        """
                        INSERT INTO evidence_records (
                            evidence_id, policy_id, provider, product, category,
                            field_name, payload
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
                        ON CONFLICT (evidence_id) DO UPDATE SET
                            policy_id = EXCLUDED.policy_id,
                            provider = EXCLUDED.provider,
                            product = EXCLUDED.product,
                            category = EXCLUDED.category,
                            field_name = EXCLUDED.field_name,
                            payload = EXCLUDED.payload
                        """,
                        [
                            (
                                record.evidence_id,
                                record.policy_id,
                                record.provider,
                                record.product,
                                record.category,
                                record.field,
                                json.dumps(record.model_dump(mode="json")),
                            )
                            for record in records
                        ],
                    )
        except Exception as error:
            raise EvidenceDependencyError(
                f"Local PostgreSQL evidence initialization failed: {error}"
            ) from error

    def search(self, request: EvidenceSearchRequest) -> list[EvidenceRecord]:
        import psycopg

        query_terms = _tokens(request.query)
        if not query_terms:
            return []
        tsquery = " | ".join(query_terms)
        conditions = ["search_document @@ to_tsquery('simple', %s)"]
        where_parameters: list[Any] = [tsquery]
        if request.filters.provider:
            conditions.append("lower(provider) = lower(%s)")
            where_parameters.append(request.filters.provider)
        if request.filters.category:
            conditions.append("lower(category) = lower(%s)")
            where_parameters.append(request.filters.category)
        if request.filters.product:
            conditions.append("product ILIKE %s")
            where_parameters.append(f"%{request.filters.product}%")
        statement = f"""
            SELECT payload,
                   ts_rank_cd(search_document, to_tsquery('simple', %s)) AS rank
            FROM evidence_records
            WHERE {' AND '.join(conditions)}
            ORDER BY rank DESC, provider, product, evidence_id
            LIMIT %s
        """
        parameters = [tsquery, *where_parameters, request.max_results * 8]
        try:
            with psycopg.connect(self._database_url) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(statement, parameters)
                    rows = cursor.fetchall()
        except Exception as error:
            raise EvidenceDependencyError(f"Local PostgreSQL search failed: {error}") from error

        selected: list[EvidenceRecord] = []
        seen_policies: set[str] = set()
        for payload, rank in rows:
            record = EvidenceRecord.model_validate(payload)
            if record.policy_id in seen_policies:
                continue
            score = min(1.0, max(0.0, float(rank)))
            if score < request.threshold:
                continue
            seen_policies.add(record.policy_id)
            selected.append(record.model_copy(update={"similarity": round(score, 6)}))
            if len(selected) == request.max_results:
                break
        return selected

    def records_for_products(self, product_ids: list[str]) -> list[EvidenceRecord]:
        import psycopg

        try:
            with psycopg.connect(self._database_url) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT payload FROM evidence_records WHERE policy_id = ANY(%s)",
                        (product_ids,),
                    )
                    return [EvidenceRecord.model_validate(row[0]) for row in cursor.fetchall()]
        except Exception as error:
            raise EvidenceDependencyError(
                f"Local PostgreSQL comparison lookup failed: {error}"
            ) from error


class FixtureEvidenceAdapter:
    def __init__(self, mode: CapabilityMode = "synthetic") -> None:
        self.mode = mode
        self._records = [
            EvidenceRecord(
                evidence_id="SYN-LTF-EVIDENCE",
                policy_id="synthetic-lioncity-term-flex",
                provider="LionCity Mutual",
                product="LionCity Term Flex",
                category="life",
                field="overview",
                section_title="Synthetic comparison fixture",
                value="Illustrative term protection within the demo budget.",
                source_file="synthetic-fixture",
                source_approval="approved",
                evidence_state="approved",
                freshness_status="current",
                document_as_of_date=date(2026, 8, 28),
                document_version="fixture-v1",
                synthetic=True,
                extraction_confidence=None,
                similarity=1,
                provenance={
                    "lineage": "deterministic-synthetic-fixture",
                    "normalized_value": 400000,
                    "unit": "SGD lump sum",
                },
            ),
            EvidenceRecord(
                evidence_id="SYN-LCC-BENEFIT",
                policy_id="synthetic-lioncity-critical-cover",
                provider="LionCity Mutual",
                product="LionCity Critical Cover",
                category="critical_illness",
                field="benefit",
                section_title="Synthetic comparison fixture",
                value="Illustrative critical-illness benefit of S$120,000.",
                source_file="synthetic-fixture",
                source_approval="approved",
                evidence_state="approved",
                freshness_status="current",
                document_as_of_date=date(2026, 8, 28),
                document_version="fixture-v1",
                synthetic=True,
                extraction_confidence=None,
                similarity=1,
                provenance={
                    "lineage": "deterministic-synthetic-fixture",
                    "normalized_value": 120000,
                    "unit": "SGD lump sum",
                },
            ),
            EvidenceRecord(
                evidence_id="SYN-LCC-PREMIUM",
                policy_id="synthetic-lioncity-critical-cover",
                provider="LionCity Mutual",
                product="LionCity Critical Cover",
                category="critical_illness",
                field="premium",
                section_title="Synthetic comparison fixture",
                value="Illustrative premium of S$58 per month.",
                source_file="synthetic-fixture",
                source_approval="approved",
                evidence_state="approved",
                freshness_status="current",
                document_as_of_date=date(2026, 8, 28),
                document_version="fixture-v1",
                synthetic=True,
                extraction_confidence=None,
                similarity=1,
                provenance={
                    "lineage": "deterministic-synthetic-fixture",
                    "normalized_value": 58,
                    "unit": "SGD/month",
                },
            ),
            EvidenceRecord(
                evidence_id="SYN-HEC-BENEFIT",
                policy_id="synthetic-harbour-essential-ci",
                provider="Harbour Life",
                product="Harbour Essential CI",
                category="critical_illness",
                field="benefit",
                section_title="Synthetic comparison fixture",
                value="Illustrative critical-illness benefit of S$150,000.",
                source_file="synthetic-fixture",
                source_approval="approved",
                evidence_state="approved",
                freshness_status="current",
                document_as_of_date=date(2026, 8, 28),
                document_version="fixture-v1",
                synthetic=True,
                extraction_confidence=None,
                similarity=1,
                provenance={
                    "lineage": "deterministic-synthetic-fixture",
                    "normalized_value": 150000,
                    "unit": "SGD lump sum",
                },
            ),
            EvidenceRecord(
                evidence_id="SYN-HEC-PREMIUM",
                policy_id="synthetic-harbour-essential-ci",
                provider="Harbour Life",
                product="Harbour Essential CI",
                category="critical_illness",
                field="premium",
                section_title="Synthetic comparison fixture",
                value="Illustrative premium of S$64 per month.",
                source_file="synthetic-fixture",
                source_approval="approved",
                evidence_state="approved",
                freshness_status="current",
                document_as_of_date=date(2026, 8, 28),
                document_version="fixture-v1",
                synthetic=True,
                extraction_confidence=None,
                similarity=1,
                provenance={
                    "lineage": "deterministic-synthetic-fixture",
                    "normalized_value": 64,
                    "unit": "SGD/month",
                },
            ),
        ]

    def search(self, request: EvidenceSearchRequest) -> list[EvidenceRecord]:
        query_terms = set(_tokens(request.query))
        matches = [
            record
            for record in self._records
            if query_terms & set(_tokens(f"{record.product} {record.category} {record.value}"))
        ]
        return matches[: request.max_results]

    def records_for_products(self, product_ids: list[str]) -> list[EvidenceRecord]:
        selected = set(product_ids)
        return [record for record in self._records if record.policy_id in selected]


class SupabaseEvidenceAdapter:
    mode: CapabilityMode = "live"

    def __init__(
        self,
        *,
        supabase_url: str,
        service_key: str,
        openai_key: str,
        cache_path: Path = DEFAULT_EMBEDDING_CACHE,
        timeout_seconds: int = 20,
        max_age_days: int = 365,
    ) -> None:
        self._supabase_url = supabase_url
        self._service_key = service_key
        self._openai_key = openai_key
        self._cache_path = cache_path
        self._timeout_seconds = timeout_seconds
        self._max_age_days = max_age_days

    def search(self, request: EvidenceSearchRequest) -> list[EvidenceRecord]:
        from scraper.rag_common import EmbeddingCache, OpenAIEmbeddings, SupabaseREST

        metadata_filter = {
            key: value
            for key, value in {
                "company": request.filters.provider,
                "category": request.filters.category,
                "policy_name": request.filters.product,
            }.items()
            if value
        }
        cache = EmbeddingCache(self._cache_path)
        try:
            embedder = OpenAIEmbeddings(
                self._openai_key,
                model=DEFAULT_EMBEDDING_MODEL,
                dimensions=DEFAULT_EMBEDDING_DIMENSIONS,
                timeout=self._timeout_seconds,
                max_attempts=2,
            )
            embedding = embedder.embed_with_cache([request.query], cache, batch_size=1)[0]
        except Exception as error:
            raise EvidenceDependencyError(f"Embedding dependency failed: {error}") from error
        finally:
            cache.close()

        database = SupabaseREST(
            self._supabase_url,
            self._service_key,
            timeout=self._timeout_seconds,
        )
        try:
            matches = database.rpc(
                "match_documents_by_type",
                {
                    "query_embedding": embedding,
                    "p_source_type": "policy",
                    "match_threshold": request.threshold,
                    "match_count": request.max_results,
                    "filter_metadata": metadata_filter or None,
                },
            ) or []
        except Exception as error:
            raise EvidenceDependencyError(f"Evidence database failed: {error}") from error

        records = []
        for match in matches:
            metadata = match.get("metadata") or {}
            document_as_of_date = _parse_date(metadata.get("document_as_of_date"))
            freshness_status = _freshness(document_as_of_date, self._max_age_days)
            source_file = str(metadata.get("source_file") or "unknown")
            approval = str(metadata.get("source_approval") or "unverified")
            source_approval: SourceApproval = (
                approval
                if approval in {"approved", "unverified", "restricted", "rejected"}
                else "unverified"
            )
            state = str(metadata.get("evidence_state") or "")
            evidence_state: EvidenceState = (
                state
                if state in {"approved", "unverified", "stale", "conflicting", "unknown"}
                else _evidence_state(source_file, freshness_status)
            )
            records.append(
                EvidenceRecord(
                    evidence_id=str(match["id"]),
                    policy_id=str(match.get("source_id") or metadata.get("policy_id") or "unknown"),
                    provider=str(metadata.get("insurer") or metadata.get("company") or "Unknown provider"),
                    product=str(metadata.get("policy_name") or "Unknown product"),
                    category=str(metadata.get("category") or "unknown"),
                    field=str(metadata.get("section_kind") or "evidence"),
                    section_title=str(match.get("source_label") or "Policy evidence"),
                    value=str(match.get("chunk_text") or ""),
                    source_url=metadata.get("brochure_url") or metadata.get("product_page"),
                    source_file=source_file,
                    source_approval=source_approval,
                    evidence_state=evidence_state,
                    freshness_status=freshness_status,
                    document_as_of_date=document_as_of_date,
                    product_effective_date=_parse_date(metadata.get("product_effective_date")),
                    retrieved_at=_parse_datetime(metadata.get("retrieved_at")),
                    document_version=metadata.get("document_version"),
                    synthetic=bool(metadata.get("synthetic", False)),
                    extraction_confidence=metadata.get("extraction_confidence"),
                    similarity=float(match.get("similarity") or 0),
                    provenance={"lineage": "supabase-pgvector", "metadata": metadata},
                )
            )
        return records

    def records_for_products(self, product_ids: list[str]) -> list[EvidenceRecord]:
        raise EvidenceDependencyError(
            "Live comparison requires the approved comparison projection"
        )


class EvidenceService:
    def __init__(self, adapter: EvidenceAdapter) -> None:
        self._adapter = adapter

    @property
    def mode(self) -> CapabilityMode:
        return self._adapter.mode

    def search(self, request: EvidenceSearchRequest) -> EvidenceSearchResponse:
        evidence = self._adapter.search(request)
        return EvidenceSearchResponse(
            run_id=f"evidence-{uuid4()}",
            mode=self.mode,
            query=request.query,
            status="matched" if evidence else "no_evidence",
            match_count=len(evidence),
            evidence=evidence,
            contract_version=CONTRACT_VERSION,
        )

    def records_for_products(self, product_ids: list[str]) -> list[EvidenceRecord]:
        return self._adapter.records_for_products(product_ids)


COMPARISON_FIELDS = (
    ("premium", "Premium"),
    ("benefit", "Benefit"),
    ("eligibility", "Eligibility"),
    ("exclusion", "Exclusions"),
    ("term", "Term"),
)


class EvidenceComparisonService:
    def __init__(
        self,
        evidence: EvidenceService,
        fixture_evidence: EvidenceService | None = None,
    ) -> None:
        self._evidence = evidence
        self._fixture_evidence = fixture_evidence

    def compare(self, request: EvidenceComparisonRequest) -> EvidenceComparisonResponse:
        service = (
            self._fixture_evidence
            if request.comparison_mode == "synthetic_fixture"
            else self._evidence
        )
        if service is None:
            raise EvidenceDependencyError("Synthetic comparison fixture is unavailable")
        records = service.records_for_products(request.product_ids)
        grouped = {
            product_id: [record for record in records if record.policy_id == product_id]
            for product_id in request.product_ids
        }
        gate_failures = {
            product_id: self._gate_reasons(product_records)
            for product_id, product_records in grouped.items()
            if self._gate_reasons(product_records)
        }
        categories = {
            product_records[0].category
            for product_records in grouped.values()
            if product_records
        }
        if len(categories) > 1:
            gate_failures["selection"] = ["MIXED_CATEGORY_SELECTION"]
        if gate_failures:
            raise EvidenceComparisonEligibilityError(gate_failures)

        products = [self._product(product_records) for product_records in grouped.values()]
        products.sort(key=lambda item: (item.provider.casefold(), item.product.casefold()))
        return EvidenceComparisonResponse(
            run_id=f"comparison-{uuid4()}",
            mode=service.mode,
            canonical_references=request.canonical_references,
            products=products,
            warnings=[
                "This is a neutral evidence comparison, not a recommendation or suitability assessment.",
                "Unknown fields were not inferred.",
            ],
        )

    @staticmethod
    def _gate_reasons(records: list[EvidenceRecord]) -> list[str]:
        if not records:
            return ["PRODUCT_NOT_FOUND"]
        reasons: list[str] = []
        if any(record.source_approval != "approved" for record in records):
            reasons.append("SOURCE_REUSE_NOT_APPROVED")
        if any(record.evidence_state != "approved" for record in records):
            reasons.append("EVIDENCE_NOT_APPROVED")
        if any(record.freshness_status != "current" for record in records):
            reasons.append("EVIDENCE_NOT_CURRENT")
        if not records[0].synthetic and any(record.source_url is None for record in records):
            reasons.append("AUTHORITATIVE_URL_MISSING")
        if any(
            record.document_as_of_date is None and record.product_effective_date is None
            for record in records
        ):
            reasons.append("SOURCE_DATE_MISSING")
        if any(record.document_version is None for record in records):
            reasons.append("DOCUMENT_VERSION_MISSING")
        return reasons

    @staticmethod
    def _product(records: list[EvidenceRecord]) -> EvidenceComparisonProduct:
        first = records[0]
        fields = []
        for key, label in COMPARISON_FIELDS:
            matches = [record for record in records if record.field == key]
            if not matches:
                fields.append(EvidenceComparisonField(key=key, label=label, state="unknown"))
                continue
            record = matches[0]
            if record.product_effective_date is not None:
                date_type = "product_effective_date"
                date_value = record.product_effective_date
            elif record.document_as_of_date is not None:
                date_type = "document_as_of_date"
                date_value = record.document_as_of_date
            elif record.retrieved_at is not None:
                date_type = "retrieved_at"
                date_value = record.retrieved_at
            else:
                date_type = "unknown"
                date_value = None
            fields.append(
                EvidenceComparisonField(
                    key=key,
                    label=label,
                    state="available",
                    value=record.value,
                    normalized_value=record.provenance.get("normalized_value"),
                    unit=record.provenance.get("unit"),
                    evidence_ids=[item.evidence_id for item in matches],
                    source_url=record.source_url,
                    source_approval=record.source_approval,
                    evidence_state=record.evidence_state,
                    freshness_status=record.freshness_status,
                    date_type=date_type,
                    date_value=date_value,
                    document_version=record.document_version,
                )
            )
        return EvidenceComparisonProduct(
            product_id=first.policy_id,
            provider=first.provider,
            product=first.product,
            category=first.category,
            eligibility="comparison_eligible",
            gate_reasons=["SYNTHETIC_COMPARISON_FIXTURE"] if first.synthetic else [],
            synthetic=first.synthetic,
            fields=fields,
        )


def create_evidence_service(
    mode: CapabilityMode,
    *,
    corpus_path: str | None = None,
    max_age_days: int = 365,
    timeout_seconds: int = 20,
    supabase_url: str | None = None,
    service_key: str | None = None,
    openai_key: str | None = None,
    database_url: str | None = None,
) -> EvidenceService:
    if mode == "live":
        if not (supabase_url and service_key and openai_key):
            raise EvidenceDependencyError("Live evidence dependencies are not configured")
        adapter: EvidenceAdapter = SupabaseEvidenceAdapter(
            supabase_url=supabase_url,
            service_key=service_key,
            openai_key=openai_key,
            timeout_seconds=timeout_seconds,
            max_age_days=max_age_days,
        )
    elif mode == "cached":
        cached_path = Path(corpus_path).expanduser().resolve() if corpus_path else DEFAULT_CORPUS
        if database_url:
            adapter = PostgresEvidenceAdapter(
                database_url,
                cached_path,
                max_age_days=max_age_days,
            )
        else:
            adapter = LocalCorpusEvidenceAdapter(
                cached_path,
                max_age_days=max_age_days,
            )
    else:
        adapter = FixtureEvidenceAdapter(mode)
    return EvidenceService(adapter)