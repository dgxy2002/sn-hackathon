"""Query insurance policy evidence from the Supabase pgvector RAG store."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from rag_common import EmbeddingCache, OpenAIEmbeddings, SupabaseREST, load_env


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_ENV = SCRIPT_DIR.parent / ".env"
DEFAULT_CACHE = SCRIPT_DIR / "insurance" / "extracted_openai" / "rag_embedding_cache.sqlite3"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_EMBEDDING_DIMENSIONS = 1536


def typed_value(value: str) -> Any:
    lowered = value.casefold()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered == "null":
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def metadata_filters(values: list[str] | None) -> dict[str, Any] | None:
    result: dict[str, Any] = {}
    for value in values or []:
        if "=" not in value:
            raise RuntimeError(f"Invalid --filter {value!r}; expected key=value")
        key, raw = value.split("=", 1)
        if not key.strip():
            raise RuntimeError("Metadata filter key cannot be empty")
        result[key.strip()] = typed_value(raw.strip())
    return result or None


def evidence_record(match: dict[str, Any]) -> dict[str, Any]:
    metadata = match.get("metadata") or {}
    return {
        "evidence_id": match["id"],
        "policy_id": match.get("source_id") or metadata.get("policy_id"),
        "provider": metadata.get("insurer") or metadata.get("company"),
        "product": metadata.get("policy_name"),
        "field": metadata.get("section_kind"),
        "section_title": match.get("source_label"),
        "value": match.get("chunk_text"),
        "source_url": metadata.get("brochure_url") or metadata.get("product_page"),
        "source_file": metadata.get("source_file"),
        "retrieved_at": metadata.get("retrieved_at"),
        "synthetic": bool(metadata.get("synthetic", False)),
        "extraction_confidence": metadata.get("extraction_confidence"),
        "similarity": match.get("similarity"),
        "metadata": metadata,
    }


def hydrate_policies(db: SupabaseREST, policy_ids: list[str]) -> list[dict[str, Any]]:
    if not policy_ids:
        return []
    expression = "in.(" + ",".join(dict.fromkeys(policy_ids)) + ")"
    policies = db.select(
        "policies",
        columns="id,insurer_id,name,slug,category,type,quick_summary,target_customer,coverage_scope,is_active,available_to_new,min_entry_age,max_entry_age,max_coverage_age,eligibility_notes,coverage_term_description,premium_payment_term_description,important_caveats,source_url,extraction_confidence",
        filters={"id": expression},
    )
    plans = db.select("policy_plans", filters={"policy_id": expression})
    benefits = db.select("policy_coverage", filters={"policy_id": expression})
    riders = db.select("policy_riders", filters={"policy_id": expression})
    exclusions = db.select("policy_exclusions", filters={"policy_id": expression})
    plan_ids = [row["id"] for row in plans]
    plan_benefits = db.select(
        "policy_plan_benefits",
        filters={"plan_id": "in.(" + ",".join(plan_ids) + ")"},
    ) if plan_ids else []
    amounts_by_plan: dict[str, list[dict[str, Any]]] = {}
    for row in plan_benefits:
        amounts_by_plan.setdefault(row["plan_id"], []).append(row)
    for plan in plans:
        plan["benefit_amounts"] = amounts_by_plan.get(plan["id"], [])
    for policy in policies:
        policy_id = policy["id"]
        policy["plans"] = [row for row in plans if row["policy_id"] == policy_id]
        policy["benefits"] = [row for row in benefits if row["policy_id"] == policy_id]
        policy["riders"] = [row for row in riders if row["policy_id"] == policy_id]
        policy["exclusions"] = [row for row in exclusions if row["policy_id"] == policy_id]
    return policies


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="Natural-language product evidence query")
    parser.add_argument("--env", type=Path, default=DEFAULT_ENV)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--embedding-model", default=DEFAULT_EMBEDDING_MODEL)
    parser.add_argument("--embedding-dimensions", type=int, default=DEFAULT_EMBEDDING_DIMENSIONS)
    parser.add_argument("--threshold", type=float, default=0.55)
    parser.add_argument("--count", type=int, default=8)
    parser.add_argument("--filter", action="append", help="Exact flat metadata filter as key=value; may be repeated")
    parser.add_argument("--hydrate", action="store_true", help="Also load complete normalized policy records")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    env = {**load_env(args.env.resolve()), **os.environ}
    if not env.get("SUPABASE_URL") or not env.get("SUPABASE_SERVICE_ROLE_KEY") or not env.get("OPENAI_KEY"):
        raise RuntimeError("SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, and OPENAI_KEY are required")
    filters = metadata_filters(args.filter)
    cache = EmbeddingCache(args.cache.resolve())
    try:
        embedder = OpenAIEmbeddings(
            env["OPENAI_KEY"],
            model=args.embedding_model,
            dimensions=args.embedding_dimensions,
        )
        query_embedding = embedder.embed_with_cache([args.query], cache, batch_size=1)[0]
    finally:
        cache.close()

    db = SupabaseREST(env["SUPABASE_URL"], env["SUPABASE_SERVICE_ROLE_KEY"])
    matches = db.rpc("match_documents_by_type", {
        "query_embedding": query_embedding,
        "p_source_type": "policy",
        "match_threshold": args.threshold,
        "match_count": args.count,
        "filter_metadata": filters,
    }) or []
    evidence = [evidence_record(match) for match in matches]
    result: dict[str, Any] = {
        "query": args.query,
        "metadata_filter": filters,
        "match_count": len(evidence),
        "evidence": evidence,
    }
    if args.hydrate:
        result["policies"] = hydrate_policies(
            db,
            [row["policy_id"] for row in evidence if row.get("policy_id")],
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
