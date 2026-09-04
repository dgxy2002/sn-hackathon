"""Ingest extracted insurance facts and RAG chunks into Supabase.

The importer is idempotent at the insurer, policy, document, plan, and chunk-set
levels. It uses the service role because the product tables are read-only to
public clients. Re-running it is the supported recovery path after interruption.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path, PureWindowsPath
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from rag_common import (
    DEFAULT_BEDROCK_EMBEDDING_DIMENSIONS,
    DEFAULT_BEDROCK_EMBEDDING_MODEL,
    BedrockEmbeddings,
    EmbeddingCache,
    SupabaseREST,
    TransientNetworkError,
    chunks,
    load_env,
    retry_delay,
)


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_INPUT = SCRIPT_DIR / "insurance" / "extracted_openai"
DEFAULT_ENV = SCRIPT_DIR.parent / ".env"
DEFAULT_EMBEDDING_MODEL = DEFAULT_BEDROCK_EMBEDDING_MODEL
DEFAULT_EMBEDDING_DIMENSIONS = DEFAULT_BEDROCK_EMBEDDING_DIMENSIONS
CHECKPOINT_VERSION = 1
DEFAULT_CHECKPOINT_NAME = ".ingest_checkpoint.json"

INSURER_SHORT_NAMES = {
    "AIA": "AIA",
    "FWD": "FWD",
    "Great Eastern": "GE",
    "Singlife": "Singlife",
}

INSURER_WEBSITES = {
    "AIA": "https://www.aia.com.sg",
    "FWD": "https://www.fwd.com.sg",
    "Great Eastern": "https://www.greateasternlife.com",
    "Singlife": "https://singlife.com",
}

UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json_atomic(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def mark_all_document_qualities_good(input_root: Path) -> int:
    """Normalize existing artifacts so every brochure is available to RAG."""
    changed = 0
    for path in sorted(input_root.rglob("*.json")):
        if path.name in {"extraction_report.json", "run_errors.json"}:
            continue
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        extraction = record.get("extraction")
        if isinstance(extraction, dict) and extraction.get("markdown_quality") != "good":
            extraction["markdown_quality"] = "good"
            write_json_atomic(path, record)
            changed += 1

    documents_path = input_root / "documents.jsonl"
    if documents_path.exists():
        records = [
            json.loads(line) for line in documents_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        for record in records:
            record.setdefault("extraction", {})["markdown_quality"] = "good"
        documents_path.write_text(
            "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
            encoding="utf-8",
        )

    manifest_path = input_root / "manifest.csv"
    if manifest_path.exists():
        with manifest_path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
            fieldnames = list(rows[0]) if rows else []
        if "markdown_quality" in fieldnames:
            for row in rows:
                row["markdown_quality"] = "good"
            with manifest_path.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

    report_path = input_root / "extraction_report.json"
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))
        report["markdown_quality_counts"] = {
            "good": int(report.get("documents_extracted") or 0),
            "degraded": 0,
            "unusable": 0,
        }
        write_json_atomic(report_path, report)
    return changed


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def load_source_catalog(insurance_root: Path) -> dict[tuple[str, str], dict[str, str]]:
    """Index scraper manifests by company and product/local filename."""
    catalog: dict[tuple[str, str], dict[str, str]] = {}
    for manifest_path in sorted(insurance_root.glob("*/manifest.csv")):
        company = manifest_path.parent.name
        with manifest_path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                details = {
                    "product_page": row.get("product_page") or "",
                    "brochure_url": row.get("brochure_url") or "",
                }
                keys = [row.get("product") or ""]
                local_file = row.get("local_file") or ""
                if local_file:
                    keys.append(PureWindowsPath(local_file).stem)
                for key in keys:
                    if key:
                        catalog[(company, normalize_name(key))] = details
    return catalog


def enrich_source(
    source: dict[str, Any],
    policy: dict[str, Any],
    catalog: dict[tuple[str, str], dict[str, str]],
    document_meta: dict[str, Any] | None,
) -> dict[str, Any]:
    company = policy["company"]
    filename_stem = Path(source.get("source_filename") or source["source_file"]).stem
    details = catalog.get((company, normalize_name(filename_stem)))
    if details is None:
        details = catalog.get((company, normalize_name(policy["policy_name"])), {})
    enriched = {**source}
    enriched["product_page"] = details.get("product_page") or None
    enriched["brochure_url"] = details.get("brochure_url") or None
    enriched["retrieved_at"] = (document_meta or {}).get("api", {}).get("generated_at")
    return enriched


def without_none(values: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value is not None}


def clean_not_stated(value: Any) -> Any:
    return None if value in (None, "", "not_stated") else value


def normalize_currency(value: str) -> str:
    aliases = {
        "s$": "SGD",
        "sgd": "SGD",
        "singapore dollar": "SGD",
        "singapore dollars": "SGD",
        "us$": "USD",
        "usd": "USD",
    }
    return aliases.get(value.strip().casefold(), value.strip().upper())


def evidence_text(evidence: list[dict[str, Any]] | None) -> str | None:
    lines: list[str] = []
    for item in evidence or []:
        quote = str(item.get("quote") or "").strip()
        if not quote:
            continue
        start, end = item.get("line_start"), item.get("line_end")
        location = f"lines {start}-{end}" if start and end else "source lines unresolved"
        lines.append(f"[{location}] {quote}")
    return "\n\n".join(lines) or None


def evidence_location(evidence: list[dict[str, Any]] | None) -> str | None:
    locations = []
    for item in evidence or []:
        start, end = item.get("line_start"), item.get("line_end")
        if start and end:
            locations.append(f"lines {start}-{end}")
    return ", ".join(dict.fromkeys(locations)) or None


def joined_notes(*values: Any) -> str | None:
    pieces: list[str] = []
    for value in values:
        if isinstance(value, list):
            pieces.extend(str(item).strip() for item in value if str(item).strip())
        elif value not in (None, ""):
            pieces.append(str(value).strip())
    return "\n".join(dict.fromkeys(pieces)) or None


def normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def ensure_uuid(value: str, label: str) -> str:
    if not UUID_PATTERN.fullmatch(value):
        raise RuntimeError(f"Refusing scoped replacement because {label} is not a UUID: {value}")
    return value


def ensure_insurer(db: SupabaseREST, company: str) -> str:
    short_name = INSURER_SHORT_NAMES.get(company, company)
    existing = db.select("insurers", columns="id", filters={"short_name": f"eq.{short_name}"}, limit=1)
    if existing:
        return existing[0]["id"]
    inserted = db.insert("insurers", {
        "name": company,
        "short_name": short_name,
        "website_url": INSURER_WEBSITES.get(company),
        "is_active": True,
    })
    return inserted[0]["id"]


def policy_row(policy: dict[str, Any], insurer_id: str, source: dict[str, Any]) -> dict[str, Any]:
    currencies = [normalize_currency(value) for value in policy.get("currency_options", [])]
    return without_none({
        "insurer_id": insurer_id,
        "name": policy["policy_name"],
        "slug": policy["slug"],
        "category": policy["category"],
        "type": policy["policy_type"],
        "plan_tier": policy.get("plan_tier"),
        "quick_summary": policy.get("quick_summary"),
        "quick_summary_evidence": evidence_text(policy.get("source_evidence")),
        "quick_summary_confidence": policy.get("extraction_confidence"),
        "target_customer": clean_not_stated(policy.get("target_customer")),
        "structure": policy.get("structure") or "base_plan",
        "participation": policy.get("participation") or "not_stated",
        "coverage_scope": policy.get("coverage_scope") or [],
        "currency_options": currencies,
        "is_active": policy.get("is_active") if policy.get("is_active") is not None else True,
        "available_to_new": policy.get("available_to_new_customers") if policy.get("available_to_new_customers") is not None else True,
        "min_entry_age": policy.get("min_entry_age"),
        "max_entry_age": policy.get("max_entry_age"),
        "max_coverage_age": policy.get("max_coverage_age"),
        "entry_age_basis": policy.get("entry_age_basis") or "not_stated",
        "residency_requirements": policy.get("residency_requirements"),
        "occupation_classes": policy.get("occupation_classes") or [],
        "eligibility_notes": policy.get("eligibility_notes"),
        "annual_limit": policy.get("annual_limit"),
        "lifetime_limit": policy.get("lifetime_limit"),
        "policy_year_limit": policy.get("policy_year_limit"),
        "term_years": policy.get("term_years"),
        "renewable": policy.get("renewable"),
        "coverage_term_description": policy.get("coverage_term_description"),
        "premium_payment_term_description": policy.get("premium_payment_term_description"),
        "premium_frequencies": policy.get("premium_frequencies") or [],
        "premium_guaranteed": policy.get("premium_guaranteed"),
        "renewal_basis": policy.get("renewal_basis"),
        "underwriting": policy.get("underwriting") or "not_stated",
        "medical_exam_required": policy.get("medical_exam_required"),
        "cash_value_available": policy.get("cash_value_available"),
        "surrender_value_available": policy.get("surrender_value_available"),
        "bonuses_or_dividends": policy.get("bonuses_or_dividends"),
        "free_look_period_days": policy.get("free_look_period_days"),
        "grace_period_days": policy.get("grace_period_days"),
        "policy_termination_events": policy.get("policy_termination_events") or [],
        "important_caveats": policy.get("important_caveats") or [],
        "ward_class": policy.get("ward_class"),
        "is_dpi": policy.get("is_dpi") if policy.get("is_dpi") is not None else False,
        "medisave_payable": policy.get("medisave_payable") if policy.get("medisave_payable") is not None else False,
        "medisave_withdrawal_limit_sgd": policy.get("medisave_withdrawal_limit_sgd"),
        "extra_fields": {
            "aliases": policy.get("aliases") or [],
            "review_notes": policy.get("review_notes") or [],
            "document_quality": "good",
        },
        "source_url": source.get("product_page") or source.get("brochure_url"),
        "source_type": "insurer_website",
        "last_scraped_at": utc_now(),
        "is_verified": False,
        "data_hash": source.get("content_sha256"),
        "extraction_status": "complete",
        "extraction_confidence": policy.get("extraction_confidence"),
        "extraction_notes": joined_notes(policy.get("review_notes")),
    })


def ensure_document(
    db: SupabaseREST,
    policy_id: str,
    source: dict[str, Any],
    policy: dict[str, Any],
    document_meta: dict[str, Any] | None,
) -> str:
    content_hash = source.get("content_sha256")
    filters = {"policy_id": f"eq.{policy_id}"}
    if content_hash:
        filters["content_hash"] = f"eq.{content_hash}"
    existing = db.select("policy_documents", columns="id,is_primary", filters=filters, limit=1)
    validation = (document_meta or {}).get("validation", {})
    extraction = (document_meta or {}).get("extraction", {})
    api = (document_meta or {}).get("api", {})
    values = without_none({
        "policy_id": policy_id,
        "document_type": source.get("document_type") or "brochure",
        "title": source.get("source_filename") or policy["policy_name"],
        "language_code": "en",
        "source_url": source.get("brochure_url") or source.get("product_page"),
        "source_type": "insurer_website",
        "local_pdf_path": source.get("local_pdf_path"),
        "local_markdown_path": source.get("local_markdown_path"),
        "content_hash": content_hash,
        "extraction_method": "markdown_openai_structured_output",
        "extraction_status": "complete",
        "extraction_confidence": policy.get("extraction_confidence"),
        "extraction_notes": joined_notes(
            extraction.get("quality_notes"),
            validation.get("evidence_warnings"),
            policy.get("review_notes"),
        ),
        "retrieved_at": source.get("retrieved_at") or api.get("generated_at"),
    })
    if existing:
        db.update("policy_documents", values, {"id": f"eq.{existing[0]['id']}"})
        return existing[0]["id"]
    primary = not db.select(
        "policy_documents",
        columns="id",
        filters={"policy_id": f"eq.{policy_id}", "is_primary": "eq.true"},
        limit=1,
    )
    values["is_primary"] = primary
    return db.insert("policy_documents", values)[0]["id"]


def replace_document_facts(db: SupabaseREST, document_id: str) -> None:
    document_id = ensure_uuid(document_id, "source_document_id")
    filters = {"source_document_id": f"eq.{document_id}"}
    for table in (
        "policy_plan_benefits",
        "policy_exclusions",
        "policy_coverage",
        "policy_plans",
        "policy_riders",
    ):
        db.delete(table, filters)


def insert_riders(
    db: SupabaseREST,
    policy_id: str,
    document_id: str,
    riders: list[dict[str, Any]],
) -> dict[str, str]:
    result: dict[str, str] = {}
    for rider in riders:
        row = without_none({
            "policy_id": policy_id,
            "source_document_id": document_id,
            "name": rider["name"],
            "description": rider.get("description"),
            "rider_type": rider.get("rider_type"),
            "is_cash_only": rider.get("is_cash_only"),
            "indicative_premium": rider.get("indicative_premium"),
            "eligibility": rider.get("eligibility"),
            "coverage_term_description": rider.get("coverage_term_description"),
            "premium_payment_term_description": rider.get("premium_payment_term_description"),
            "includes_premium_waiver": rider.get("includes_premium_waiver"),
            "notes": rider.get("notes"),
            "source_evidence": evidence_text(rider.get("evidence")),
            "source_location": evidence_location(rider.get("evidence")),
            "extraction_confidence": rider.get("extraction_confidence"),
        })
        saved = db.upsert("policy_riders", row, on_conflict="policy_id,name")[0]
        result[normalize_name(rider["name"])] = saved["id"]
    return result


def benefit_row(
    policy_id: str,
    document_id: str,
    benefit: dict[str, Any],
    rider_id: str | None = None,
) -> dict[str, Any]:
    return without_none({
        "policy_id": policy_id,
        "source_document_id": document_id,
        "rider_id": rider_id,
        "benefit_name": benefit["benefit_name"],
        "benefit_category": benefit.get("benefit_category"),
        "benefit_level": benefit.get("benefit_level") or "base",
        "benefit_description": benefit.get("benefit_description"),
        "trigger_description": benefit.get("trigger_description"),
        "covered_conditions": benefit.get("covered_conditions") or [],
        "condition_stages": benefit.get("condition_stages") or [],
        "coverage_type": benefit.get("coverage_type"),
        "payout_type": benefit.get("payout_type"),
        "payout_value": benefit.get("payout_value"),
        "payout_unit": benefit.get("payout_unit"),
        "payout_basis": benefit.get("payout_basis"),
        "payout_description": benefit.get("payout_description"),
        "minimum_payout_amount": benefit.get("minimum_payout_amount"),
        "maximum_payout_amount": benefit.get("maximum_payout_amount"),
        "payout_currency": benefit.get("payout_currency"),
        "limit_amount": benefit.get("limit_amount"),
        "limit_type": benefit.get("limit_type"),
        "claim_frequency": benefit.get("claim_frequency"),
        "maximum_claims": benefit.get("maximum_claims"),
        "benefit_relationship": benefit.get("benefit_relationship") or "unknown",
        "reduces_base_sum_assured": benefit.get("reduces_base_sum_assured"),
        "deductible_sgd": benefit.get("deductible_sgd"),
        "co_insurance_pct": benefit.get("co_insurance_pct"),
        "co_insurance_cap_sgd": benefit.get("co_insurance_cap_sgd"),
        "waiting_period_days": benefit.get("waiting_period_days"),
        "survival_period_days": benefit.get("survival_period_days"),
        "deferment_period_days": benefit.get("deferment_period_days"),
        "benefit_start_description": benefit.get("benefit_start_description"),
        "benefit_expiry_age": benefit.get("benefit_expiry_age"),
        "benefit_expiry_description": benefit.get("benefit_expiry_description"),
        "geographic_scope": benefit.get("geographic_scope"),
        "covered": True,
        "notes": benefit.get("notes"),
        "source_evidence": evidence_text(benefit.get("evidence")),
        "source_location": evidence_location(benefit.get("evidence")),
        "extraction_confidence": benefit.get("extraction_confidence"),
    })


def insert_benefits(
    db: SupabaseREST,
    policy_id: str,
    document_id: str,
    benefits: list[dict[str, Any]],
    rider_ids: dict[str, str],
) -> dict[str, str]:
    result: dict[str, str] = {}
    only_rider_id = next(iter(rider_ids.values())) if len(rider_ids) == 1 else None
    for benefit in benefits:
        rider_id = only_rider_id if benefit.get("benefit_level") == "rider" else None
        saved = db.insert("policy_coverage", benefit_row(policy_id, document_id, benefit, rider_id))[0]
        result.setdefault(normalize_name(benefit["benefit_name"]), saved["id"])
    return result


def insert_plans(
    db: SupabaseREST,
    policy_id: str,
    document_id: str,
    plans: list[dict[str, Any]],
) -> list[tuple[dict[str, Any], str]]:
    result: list[tuple[dict[str, Any], str]] = []
    for index, plan in enumerate(plans):
        row = without_none({
            "policy_id": policy_id,
            "source_document_id": document_id,
            "name": plan["plan_name"],
            "code": plan.get("plan_code"),
            "description": plan.get("description"),
            "applies_to": plan.get("applies_to") or "base_policy",
            "linked_rider_name": plan.get("linked_rider_name"),
            "display_order": index,
            "is_default": plan.get("is_default"),
            "ward_class": plan.get("ward_class"),
            "currency": normalize_currency(plan["currency"]) if plan.get("currency") else None,
            "minimum_sum_assured": plan.get("minimum_sum_assured"),
            "maximum_sum_assured": plan.get("maximum_sum_assured"),
            "annual_limit": plan.get("annual_limit"),
            "lifetime_limit": plan.get("lifetime_limit"),
            "policy_year_limit": plan.get("policy_year_limit"),
            "deductible_sgd": plan.get("deductible_sgd"),
            "co_insurance_pct": plan.get("co_insurance_pct"),
            "co_insurance_cap_sgd": plan.get("co_insurance_cap_sgd"),
            "eligibility_notes": plan.get("eligibility_notes"),
            "coverage_term_description": plan.get("coverage_term_description"),
            "premium_payment_term_description": plan.get("premium_payment_term_description"),
            "notes": plan.get("notes"),
            "source_evidence": evidence_text(plan.get("evidence")),
            "source_location": evidence_location(plan.get("evidence")),
            "extraction_confidence": plan.get("extraction_confidence"),
        })
        saved = db.upsert(
            "policy_plans",
            row,
            on_conflict="policy_id,name,applies_to,linked_rider_name",
        )[0]
        result.append((plan, saved["id"]))
    return result


def insert_plan_benefits(
    db: SupabaseREST,
    policy_id: str,
    document_id: str,
    plans: list[tuple[dict[str, Any], str]],
    benefit_ids: dict[str, str],
) -> int:
    count = 0
    for plan, plan_id in plans:
        for amount in plan.get("benefit_amounts", []):
            normalized = normalize_name(amount["benefit_name"])
            benefit_id = benefit_ids.get(normalized)
            if benefit_id is None:
                stub = {
                    **amount,
                    "benefit_category": "plan_specific",
                    "benefit_level": "rider" if plan.get("applies_to") == "rider" else "base",
                    "benefit_description": amount.get("payout_description") or f"Plan-specific amount for {amount['benefit_name']}",
                    "trigger_description": amount.get("conditions"),
                    "covered_conditions": [],
                    "condition_stages": [],
                }
                benefit_id = db.insert("policy_coverage", benefit_row(policy_id, document_id, stub))[0]["id"]
                benefit_ids[normalized] = benefit_id
            row = without_none({
                "plan_id": plan_id,
                "benefit_id": benefit_id,
                "source_document_id": document_id,
                "payout_type": amount.get("payout_type"),
                "payout_value": amount.get("payout_value"),
                "payout_unit": amount.get("payout_unit"),
                "payout_basis": amount.get("payout_basis"),
                "payout_description": amount.get("payout_description"),
                "payout_currency": amount.get("payout_currency"),
                "minimum_payout_amount": amount.get("minimum_payout_amount"),
                "maximum_payout_amount": amount.get("maximum_payout_amount"),
                "limit_amount": amount.get("limit_amount"),
                "limit_type": amount.get("limit_type"),
                "claim_frequency": amount.get("claim_frequency"),
                "maximum_claims": amount.get("maximum_claims"),
                "benefit_relationship": amount.get("benefit_relationship") or "unknown",
                "reduces_base_sum_assured": amount.get("reduces_base_sum_assured"),
                "waiting_period_days": amount.get("waiting_period_days"),
                "survival_period_days": amount.get("survival_period_days"),
                "deferment_period_days": amount.get("deferment_period_days"),
                "conditions": amount.get("conditions"),
                "notes": amount.get("notes"),
                "source_evidence": evidence_text(amount.get("evidence")),
                "source_location": evidence_location(amount.get("evidence")),
                "extraction_confidence": amount.get("extraction_confidence"),
            })
            db.upsert("policy_plan_benefits", row, on_conflict="plan_id,benefit_id")
            count += 1
    return count


def insert_exclusions(
    db: SupabaseREST,
    policy_id: str,
    document_id: str,
    exclusions: list[dict[str, Any]],
) -> int:
    for exclusion in exclusions:
        db.insert("policy_exclusions", without_none({
            "policy_id": policy_id,
            "source_document_id": document_id,
            "exclusion": exclusion["exclusion"],
            "category": exclusion.get("category"),
            "applies_to": exclusion.get("applies_to"),
            "source_evidence": evidence_text(exclusion.get("evidence")),
            "source_location": evidence_location(exclusion.get("evidence")),
            "extraction_confidence": exclusion.get("extraction_confidence"),
            "extraction_notes": exclusion.get("notes"),
        }))
    return len(exclusions)


def printable(value: Any) -> str | None:
    if value in (None, "", [], {}):
        return None
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, list):
        return "; ".join(str(item) for item in value)
    return str(value)


def render_chunk(header: str, fields: list[tuple[str, Any]], evidence: list[dict[str, Any]] | None = None) -> str:
    lines = [header]
    for label, value in fields:
        rendered = printable(value)
        if rendered:
            lines.append(f"{label}: {rendered}")
    rendered_evidence = evidence_text(evidence)
    if rendered_evidence:
        lines.extend(["Evidence:", rendered_evidence])
    return "\n".join(lines)


def build_policy_chunks(
    policy: dict[str, Any],
    source: dict[str, Any],
    policy_id: str,
    document_id: str,
) -> list[dict[str, Any]]:
    company = policy["company"]
    policy_name = policy["policy_name"]
    common_meta = {
        "type": "policy",
        "policy_id": policy_id,
        "company": company,
        "insurer": company,
        "policy_name": policy_name,
        "category": policy["category"],
        "policy_type": policy["policy_type"],
        "document_id": document_id,
        "document_type": source.get("document_type") or "brochure",
        "document_quality": "good",
        "source_file": source.get("source_file"),
        "content_hash": source.get("content_sha256"),
        "product_page": source.get("product_page"),
        "brochure_url": source.get("brochure_url"),
        "retrieved_at": source.get("retrieved_at"),
        "synthetic": False,
    }
    rows: list[dict[str, Any]] = []

    def add(
        kind: str,
        title: str,
        text: str,
        *,
        confidence: str | None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        chunk_meta = {**common_meta, "section_kind": kind, "extraction_confidence": confidence or "medium"}
        if metadata:
            chunk_meta.update({key: value for key, value in metadata.items() if value not in (None, "")})
        rows.append({
            "source_type": "policy",
            "source_id": policy_id,
            "source_url": source.get("brochure_url") or source.get("product_page"),
            "source_label": f"{company} — {policy_name} — {title}",
            "chunk_text": text,
            "section_title": title,
            "metadata": chunk_meta,
        })

    add(
        "overview",
        "Policy overview",
        render_chunk(
            f"Insurance policy: {company} — {policy_name}",
            [
                ("Summary", policy.get("quick_summary")),
                ("Category", policy.get("category")),
                ("Policy type", policy.get("policy_type")),
                ("Target customer", clean_not_stated(policy.get("target_customer"))),
                ("Coverage scope", policy.get("coverage_scope")),
                ("Currency options", policy.get("currency_options")),
                ("Important caveats", policy.get("important_caveats")),
            ],
            policy.get("source_evidence"),
        ),
        confidence=policy.get("extraction_confidence"),
    )

    add(
        "eligibility_and_terms",
        "Eligibility and policy terms",
        render_chunk(
            f"Eligibility and terms for {company} — {policy_name}",
            [
                ("Minimum entry age", policy.get("min_entry_age")),
                ("Maximum entry age", policy.get("max_entry_age")),
                ("Entry-age basis", policy.get("entry_age_basis")),
                ("Maximum coverage age", policy.get("max_coverage_age")),
                ("Residency", policy.get("residency_requirements")),
                ("Occupation classes", policy.get("occupation_classes")),
                ("Eligibility notes", policy.get("eligibility_notes")),
                ("Coverage term", policy.get("coverage_term_description")),
                ("Premium payment term", policy.get("premium_payment_term_description")),
                ("Premium frequencies", policy.get("premium_frequencies")),
                ("Renewable", policy.get("renewable")),
                ("Renewal basis", policy.get("renewal_basis")),
                ("Underwriting", policy.get("underwriting")),
                ("Medical exam required", policy.get("medical_exam_required")),
                ("Termination events", policy.get("policy_termination_events")),
            ],
        ),
        confidence=policy.get("extraction_confidence"),
    )

    for plan in policy.get("plans", []):
        plan_meta = {
            "plan_name": plan["plan_name"],
            "applies_to": plan.get("applies_to"),
            "linked_rider_name": plan.get("linked_rider_name"),
            "ward_class": plan.get("ward_class"),
        }
        add(
            "plan",
            f"Plan: {plan['plan_name']}",
            render_chunk(
                f"Plan under {company} — {policy_name}: {plan['plan_name']}",
                [
                    ("Description", plan.get("description")),
                    ("Applies to", plan.get("applies_to")),
                    ("Linked rider", plan.get("linked_rider_name")),
                    ("Ward class", plan.get("ward_class")),
                    ("Currency", plan.get("currency")),
                    ("Minimum sum assured", plan.get("minimum_sum_assured")),
                    ("Maximum sum assured", plan.get("maximum_sum_assured")),
                    ("Annual limit", plan.get("annual_limit")),
                    ("Lifetime limit", plan.get("lifetime_limit")),
                    ("Policy-year limit", plan.get("policy_year_limit")),
                    ("Deductible SGD", plan.get("deductible_sgd")),
                    ("Co-insurance percent", plan.get("co_insurance_pct")),
                    ("Co-insurance cap SGD", plan.get("co_insurance_cap_sgd")),
                    ("Eligibility", plan.get("eligibility_notes")),
                    ("Coverage term", plan.get("coverage_term_description")),
                    ("Premium payment term", plan.get("premium_payment_term_description")),
                    ("Notes", plan.get("notes")),
                ],
                plan.get("evidence"),
            ),
            confidence=plan.get("extraction_confidence"),
            metadata=plan_meta,
        )
        for amount in plan.get("benefit_amounts", []):
            add(
                "plan_benefit_amount",
                f"{plan['plan_name']} — {amount['benefit_name']}",
                render_chunk(
                    f"Plan-specific claim amount for {company} — {policy_name}",
                    [
                        ("Plan", plan["plan_name"]),
                        ("Benefit", amount["benefit_name"]),
                        ("Payout type", amount.get("payout_type")),
                        ("Payout value", amount.get("payout_value")),
                        ("Payout unit", amount.get("payout_unit")),
                        ("Payout basis", amount.get("payout_basis")),
                        ("Payout description", amount.get("payout_description")),
                        ("Minimum payout", amount.get("minimum_payout_amount")),
                        ("Maximum payout", amount.get("maximum_payout_amount")),
                        ("Limit amount", amount.get("limit_amount")),
                        ("Limit type", amount.get("limit_type")),
                        ("Claim frequency", amount.get("claim_frequency")),
                        ("Maximum claims", amount.get("maximum_claims")),
                        ("Conditions", amount.get("conditions")),
                        ("Waiting period days", amount.get("waiting_period_days")),
                        ("Survival period days", amount.get("survival_period_days")),
                        ("Deferment period days", amount.get("deferment_period_days")),
                        ("Notes", amount.get("notes")),
                    ],
                    amount.get("evidence"),
                ),
                confidence=amount.get("extraction_confidence"),
                metadata={**plan_meta, "benefit_name": amount["benefit_name"]},
            )

    for benefit in policy.get("benefits", []):
        add(
            "benefit",
            f"Benefit: {benefit['benefit_name']}",
            render_chunk(
                f"Covered benefit under {company} — {policy_name}",
                [
                    ("Benefit", benefit["benefit_name"]),
                    ("Category", benefit.get("benefit_category")),
                    ("Level", benefit.get("benefit_level")),
                    ("Description", benefit.get("benefit_description")),
                    ("Trigger", benefit.get("trigger_description")),
                    ("Covered conditions", benefit.get("covered_conditions")),
                    ("Condition stages", benefit.get("condition_stages")),
                    ("Coverage type", benefit.get("coverage_type")),
                    ("Payout type", benefit.get("payout_type")),
                    ("Payout value", benefit.get("payout_value")),
                    ("Payout unit", benefit.get("payout_unit")),
                    ("Payout basis", benefit.get("payout_basis")),
                    ("Payout description", benefit.get("payout_description")),
                    ("Minimum payout", benefit.get("minimum_payout_amount")),
                    ("Maximum payout", benefit.get("maximum_payout_amount")),
                    ("Limit amount", benefit.get("limit_amount")),
                    ("Limit type", benefit.get("limit_type")),
                    ("Claim frequency", benefit.get("claim_frequency")),
                    ("Maximum claims", benefit.get("maximum_claims")),
                    ("Benefit relationship", benefit.get("benefit_relationship")),
                    ("Waiting period days", benefit.get("waiting_period_days")),
                    ("Survival period days", benefit.get("survival_period_days")),
                    ("Deferment period days", benefit.get("deferment_period_days")),
                    ("Benefit expiry", benefit.get("benefit_expiry_description")),
                    ("Geographic scope", benefit.get("geographic_scope")),
                    ("Notes", benefit.get("notes")),
                ],
                benefit.get("evidence"),
            ),
            confidence=benefit.get("extraction_confidence"),
            metadata={
                "benefit_name": benefit["benefit_name"],
                "benefit_category": benefit.get("benefit_category"),
                "benefit_level": benefit.get("benefit_level"),
            },
        )

    for rider in policy.get("riders", []):
        add(
            "rider",
            f"Rider: {rider['name']}",
            render_chunk(
                f"Optional rider for {company} — {policy_name}",
                [
                    ("Rider", rider["name"]),
                    ("Description", rider.get("description")),
                    ("Rider type", rider.get("rider_type")),
                    ("Eligibility", rider.get("eligibility")),
                    ("Coverage term", rider.get("coverage_term_description")),
                    ("Premium payment term", rider.get("premium_payment_term_description")),
                    ("Indicative premium", rider.get("indicative_premium")),
                    ("Includes premium waiver", rider.get("includes_premium_waiver")),
                    ("Notes", rider.get("notes")),
                ],
                rider.get("evidence"),
            ),
            confidence=rider.get("extraction_confidence"),
            metadata={"rider_name": rider["name"], "rider_type": rider.get("rider_type")},
        )

    for exclusion in policy.get("exclusions", []):
        add(
            "exclusion",
            f"Exclusion: {exclusion['category']}",
            render_chunk(
                f"Exclusion under {company} — {policy_name}",
                [
                    ("Exclusion", exclusion["exclusion"]),
                    ("Category", exclusion.get("category")),
                    ("Applies to", exclusion.get("applies_to")),
                    ("Notes", exclusion.get("notes")),
                ],
                exclusion.get("evidence"),
            ),
            confidence=exclusion.get("extraction_confidence"),
            metadata={"exclusion_category": exclusion.get("category"), "applies_to": exclusion.get("applies_to")},
        )
    return rows


def deduplicate_chunks(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        key = hashlib.sha256(
            (row["chunk_text"] + "\0" + json.dumps(row["metadata"], sort_keys=True)).encode("utf-8")
        ).hexdigest()
        if key not in seen:
            seen.add(key)
            row["id"] = str(
                uuid5(
                    NAMESPACE_URL,
                    f"covercheck:{row['source_type']}:{row['source_id']}:{key}",
                )
            )
            result.append(row)
    for index, row in enumerate(result):
        row["chunk_index"] = index
        row["token_count"] = max(1, len(row["chunk_text"]) // 4)
    return result


def document_map(input_root: Path) -> dict[str, dict[str, Any]]:
    path = input_root / "documents.jsonl"
    if not path.exists():
        return {}
    return {record["source_document"]["source_file"]: record for record in load_jsonl(path)}


def import_policy(
    db: SupabaseREST,
    item: dict[str, Any],
    document_meta: dict[str, Any] | None,
) -> tuple[str, str, list[dict[str, Any]], dict[str, int]]:
    source = item["source_document"]
    policy = item["policy"]
    insurer_id = ensure_insurer(db, policy["company"])
    saved_policy = db.upsert("policies", policy_row(policy, insurer_id, source), on_conflict="slug")[0]
    policy_id = saved_policy["id"]
    document_id = ensure_document(db, policy_id, source, policy, document_meta)
    replace_document_facts(db, document_id)

    rider_ids = insert_riders(db, policy_id, document_id, policy.get("riders", []))
    benefit_ids = insert_benefits(db, policy_id, document_id, policy.get("benefits", []), rider_ids)
    plans = insert_plans(db, policy_id, document_id, policy.get("plans", []))
    plan_benefits = insert_plan_benefits(db, policy_id, document_id, plans, benefit_ids)
    exclusions = insert_exclusions(db, policy_id, document_id, policy.get("exclusions", []))
    db.update(
        "policies",
        {"quick_summary_source_document_id": document_id},
        {"id": f"eq.{policy_id}"},
    )
    counts = {
        "plans": len(plans),
        "benefits": len(benefit_ids),
        "plan_benefits": plan_benefits,
        "riders": len(rider_ids),
        "exclusions": exclusions,
    }
    return policy_id, document_id, build_policy_chunks(policy, source, policy_id, document_id), counts


def checkpoint_item_id(item: dict[str, Any]) -> str:
    source = item["source_document"]
    identity = {
        "policy_slug": item["policy"]["slug"],
        "source": source.get("content_sha256") or source["source_file"],
    }
    return hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def unique_policy_items(
    items: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    unique: list[dict[str, Any]] = []
    duplicates: list[str] = []
    seen: set[str] = set()
    for item in items:
        identity = checkpoint_item_id(item)
        if identity in seen:
            duplicates.append(item["source_document"]["source_file"])
            continue
        seen.add(identity)
        unique.append(item)
    return unique, duplicates


def checkpoint_fingerprint(
    items: list[dict[str, Any]],
    *,
    supabase_url: str,
    embedding_model: str,
    embedding_dimensions: int,
    structured_only: bool,
    skip_embeddings: bool,
) -> str:
    job = {
        "target": supabase_url.rstrip("/").casefold(),
        "items": [checkpoint_item_id(item) for item in items],
        "embedding_model": embedding_model,
        "embedding_dimensions": embedding_dimensions,
        "structured_only": structured_only,
        "skip_embeddings": skip_embeddings,
    }
    return hashlib.sha256(
        json.dumps(job, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def load_checkpoint(
    path: Path,
    fingerprint: str,
    *,
    reset: bool,
) -> set[str]:
    if reset and path.exists():
        path.unlink()
    if not path.exists():
        return set()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(
            f"Cannot read checkpoint {path}; rerun with --reset-checkpoint"
        ) from error
    if (
        payload.get("version") != CHECKPOINT_VERSION
        or payload.get("fingerprint") != fingerprint
    ):
        print("CHECKPOINT_RESET reason=job_configuration_changed", flush=True)
        path.unlink()
        return set()
    completed = payload.get("completed")
    if not isinstance(completed, list) or not all(
        isinstance(value, str) for value in completed
    ):
        raise RuntimeError(
            f"Invalid checkpoint {path}; rerun with --reset-checkpoint"
        )
    return set(completed)


def save_checkpoint(path: Path, fingerprint: str, completed: set[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.tmp")
    temporary.write_text(
        json.dumps(
            {
                "version": CHECKPOINT_VERSION,
                "fingerprint": fingerprint,
                "completed": sorted(completed),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def upload_policy_chunks(
    db: SupabaseREST,
    policy_id: str,
    raw_rows: list[dict[str, Any]],
    *,
    embedder: BedrockEmbeddings | None,
    cache: EmbeddingCache,
    embedding_model: str,
    embedding_dimensions: int,
    embedding_batch_size: int,
    db_batch_size: int,
) -> int:
    rows = deduplicate_chunks(raw_rows)
    if embedder:
        vectors = embedder.embed_with_cache(
            [row["chunk_text"] for row in rows],
            cache,
            batch_size=embedding_batch_size,
        )
        for row, vector in zip(rows, vectors):
            row["embedding"] = vector
            row["metadata"] = {
                **row["metadata"],
                "embedding_provider": "bedrock",
                "embedding_model": embedding_model,
                "embedding_dimensions": embedding_dimensions,
            }
    ensure_uuid(policy_id, "policy_id")
    db.delete(
        "document_chunks",
        {"source_type": "eq.policy", "source_id": f"eq.{policy_id}"},
    )
    for batch in chunks(rows, db_batch_size):
        db.upsert("document_chunks", batch, on_conflict="id")
    return len(rows)


def ingest_policy_with_retries(
    db: SupabaseREST,
    item: dict[str, Any],
    document_meta: dict[str, Any] | None,
    *,
    embedder: BedrockEmbeddings | None,
    cache: EmbeddingCache | None,
    embedding_model: str,
    embedding_dimensions: int,
    embedding_batch_size: int,
    db_batch_size: int,
    structured_only: bool,
    max_attempts: int,
) -> tuple[dict[str, int], int]:
    for attempt in range(1, max_attempts + 1):
        try:
            policy_id, _, rows, counts = import_policy(db, item, document_meta)
            chunk_count = 0
            if not structured_only:
                if cache is None:
                    raise RuntimeError("Embedding cache is unavailable")
                chunk_count = upload_policy_chunks(
                    db,
                    policy_id,
                    rows,
                    embedder=embedder,
                    cache=cache,
                    embedding_model=embedding_model,
                    embedding_dimensions=embedding_dimensions,
                    embedding_batch_size=embedding_batch_size,
                    db_batch_size=db_batch_size,
                )
            return counts, chunk_count
        except TransientNetworkError:
            if attempt == max_attempts:
                raise
            delay = retry_delay(attempt)
            print(
                f"RETRY policy={item['policy']['slug']} "
                f"attempt={attempt + 1}/{max_attempts} delay={delay:.1f}s",
                flush=True,
            )
            time.sleep(delay)
    raise RuntimeError("Policy ingestion retry loop ended unexpectedly")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--env", type=Path, default=DEFAULT_ENV)
    parser.add_argument("--embedding-model")
    parser.add_argument("--embedding-dimensions", type=int)
    parser.add_argument("--embedding-batch-size", type=int, default=64)
    parser.add_argument("--db-batch-size", type=int, default=25)
    parser.add_argument("--max-attempts", type=int, default=5)
    parser.add_argument(
        "--checkpoint",
        type=Path,
        help=f"Resume checkpoint path (default: INPUT/{DEFAULT_CHECKPOINT_NAME})",
    )
    parser.add_argument(
        "--reset-checkpoint",
        action="store_true",
        help="Discard a saved resume checkpoint before starting",
    )
    parser.add_argument("--match", action="append", help="Only include source paths or policy names containing this text")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--structured-only", action="store_true", help="Load relational tables without document chunks")
    parser.add_argument("--skip-embeddings", action="store_true", help="Insert chunks with NULL embeddings")
    parser.add_argument("--prepare-only", action="store_true", help="Mark qualities good and inspect inputs without network calls")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_root = args.input.resolve()
    policies_path = input_root / "policies.jsonl"
    if not policies_path.exists():
        raise RuntimeError(f"Missing extraction aggregate: {policies_path}")

    changed = mark_all_document_qualities_good(input_root)
    items = load_jsonl(policies_path)
    docs = document_map(input_root)
    source_catalog = load_source_catalog(input_root.parent)
    for item in items:
        source_file = item["source_document"]["source_file"]
        item["source_document"] = enrich_source(
            item["source_document"],
            item["policy"],
            source_catalog,
            docs.get(source_file),
        )
    if args.match:
        needles = [value.casefold() for value in args.match]
        items = [
            item for item in items
            if any(
                needle in item["source_document"]["source_file"].casefold()
                or needle in item["policy"]["policy_name"].casefold()
                for needle in needles
            )
        ]
    if args.limit is not None:
        items = items[:args.limit]
    if not items:
        raise RuntimeError("No extracted policies matched the requested selection")
    selected_rows = len(items)
    items, duplicate_sources = unique_policy_items(items)
    for source_file in duplicate_sources:
        print(f"SKIP_DUPLICATE {source_file}", flush=True)
    if args.prepare_only:
        chunk_count = 0
        for item in items:
            source = item["source_document"]
            chunk_count += len(build_policy_chunks(
                item["policy"],
                source,
                "00000000-0000-4000-8000-000000000000",
                "00000000-0000-4000-8000-000000000001",
            ))
        print(
            f"READY extracted_policy_rows={selected_rows} unique_policies={len(items)} "
            f"candidate_chunks={chunk_count} quality_files_changed={changed}"
        )
        return 0

    env = {**load_env(args.env.resolve()), **os.environ}
    supabase_url = env.get("SUPABASE_URL")
    service_key = env.get("SUPABASE_SERVICE_ROLE_KEY")
    aws_region = env.get("AWS_REGION") or env.get("AWS_DEFAULT_REGION")
    embedding_model = (
        args.embedding_model
        or env.get("BEDROCK_EMBEDDING_MODEL_ID")
        or DEFAULT_EMBEDDING_MODEL
    )
    try:
        embedding_dimensions = int(
            args.embedding_dimensions
            or env.get("BEDROCK_EMBEDDING_DIMENSIONS")
            or DEFAULT_EMBEDDING_DIMENSIONS
        )
    except ValueError as error:
        raise RuntimeError("BEDROCK_EMBEDDING_DIMENSIONS must be an integer") from error
    if not supabase_url or not service_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")
    if not args.structured_only and not args.skip_embeddings and not aws_region:
        raise RuntimeError(
            "AWS_REGION or AWS_DEFAULT_REGION is required unless "
            "--structured-only or --skip-embeddings is used"
        )
    if args.max_attempts < 1:
        raise RuntimeError("--max-attempts must be at least 1")
    if args.embedding_batch_size < 1 or args.db_batch_size < 1:
        raise RuntimeError("Batch sizes must be at least 1")

    checkpoint_path = (
        args.checkpoint.resolve()
        if args.checkpoint
        else input_root / DEFAULT_CHECKPOINT_NAME
    )
    fingerprint = checkpoint_fingerprint(
        items,
        supabase_url=supabase_url,
        embedding_model=embedding_model,
        embedding_dimensions=embedding_dimensions,
        structured_only=args.structured_only,
        skip_embeddings=args.skip_embeddings,
    )
    completed = load_checkpoint(
        checkpoint_path,
        fingerprint,
        reset=args.reset_checkpoint,
    )

    db = SupabaseREST(
        supabase_url,
        service_key,
        max_attempts=args.max_attempts,
    )
    totals = defaultdict(int)
    cache = (
        None
        if args.structured_only
        else EmbeddingCache(input_root / "rag_embedding_cache.sqlite3")
    )
    embedder = (
        None
        if args.structured_only or args.skip_embeddings
        else BedrockEmbeddings(
            model=embedding_model,
            dimensions=embedding_dimensions,
            region_name=aws_region or "",
            aws_access_key_id=env.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=env.get("AWS_SECRET_ACCESS_KEY"),
            aws_session_token=env.get("AWS_SESSION_TOKEN"),
            max_attempts=args.max_attempts,
        )
    )

    print(
        f"START policies={len(items)} resumed={len(completed)} input={input_root}",
        flush=True,
    )
    try:
        for index, item in enumerate(items, start=1):
            item_id = checkpoint_item_id(item)
            if item_id in completed:
                totals["resumed"] += 1
                print(
                    f"RESUME_SKIP {index}/{len(items)} "
                    f"{item['policy']['company']} - {item['policy']['policy_name']}",
                    flush=True,
                )
                continue

            source = item["source_document"]
            counts, chunk_count = ingest_policy_with_retries(
                db,
                item,
                docs.get(source["source_file"]),
                embedder=embedder,
                cache=cache,
                embedding_model=embedding_model,
                embedding_dimensions=embedding_dimensions,
                embedding_batch_size=args.embedding_batch_size,
                db_batch_size=args.db_batch_size,
                structured_only=args.structured_only,
                max_attempts=args.max_attempts,
            )
            totals["policies"] += 1
            totals["chunks"] += chunk_count
            for key, value in counts.items():
                totals[key] += value
            completed.add(item_id)
            save_checkpoint(checkpoint_path, fingerprint, completed)
            print(
                f"COMPLETED {index}/{len(items)} plans={counts['plans']} "
                f"benefits={counts['benefits']} amounts={counts['plan_benefits']} "
                f"chunks={chunk_count} {item['policy']['company']} - "
                f"{item['policy']['policy_name']}",
                flush=True,
            )
    finally:
        if cache is not None:
            cache.close()

    checkpoint_path.unlink(missing_ok=True)

    print(
        "DONE " + " ".join(f"{key}={value}" for key, value in sorted(totals.items())),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
