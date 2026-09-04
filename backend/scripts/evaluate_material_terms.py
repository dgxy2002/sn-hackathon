from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.contracts_v2 import DocumentSpan, SourceRegion
from app.material_extraction import MATERIAL_TERM_TAXONOMY, MaterialExtractionService


DEFAULT_CORPUS = (
    Path(__file__).resolve().parents[1] / "evaluation" / "material_terms_v1.json"
)


@dataclass(frozen=True)
class EvaluationMetrics:
    case_count: int
    expected_present: int
    predicted_present: int
    exact_matches: int
    false_positives: int
    false_negatives: int
    expected_unknown: int
    correct_unknown: int
    citation_bound: int
    precision: float
    recall: float
    unknown_accuracy: float
    citation_binding: float


def evaluate_material_terms(corpus_path: Path = DEFAULT_CORPUS) -> EvaluationMetrics:
    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    extractor = MaterialExtractionService()
    exact_matches = 0
    false_positives = 0
    false_negatives = 0
    expected_present_count = 0
    predicted_present_count = 0
    expected_unknown_count = 0
    correct_unknown_count = 0
    citation_bound_count = 0

    for case in corpus["cases"]:
        case_id = case["case_id"]
        text = case["text"]
        content_sha256 = hashlib.sha256(text.encode()).hexdigest()
        span = DocumentSpan(
            span_id=f"span-{case_id}",
            analysis_id=f"analysis-{case_id}",
            document_id=f"document-{case_id}",
            region=SourceRegion(page=1),
            redacted_text=text,
            content_sha256=content_sha256,
            parser_version="gold-set-1.0.0",
        )
        result = extractor.extract(
            span.analysis_id,
            [span],
            f"evaluate-{case_id}",
        )
        terms = {term.taxonomy_key: term for term in result.terms}
        expected_present: dict[str, Any] = case["expected_present"]

        for taxonomy_key in MATERIAL_TERM_TAXONOMY:
            term = terms[taxonomy_key]
            expected = expected_present.get(taxonomy_key)
            if expected is None:
                expected_unknown_count += 1
                if term.value.state == "unknown":
                    correct_unknown_count += 1
                elif term.value.state == "present":
                    false_positives += 1
            else:
                expected_present_count += 1
                if term.value.state == "present" and term.value.value == expected:
                    exact_matches += 1
                else:
                    false_negatives += 1
                    if term.value.state == "present":
                        false_positives += 1

            if term.value.state == "present":
                predicted_present_count += 1
                if term.source_span_ids == [span.span_id]:
                    citation_bound_count += 1

    precision_denominator = exact_matches + false_positives
    precision = exact_matches / precision_denominator if precision_denominator else 1.0
    recall = exact_matches / expected_present_count if expected_present_count else 1.0
    unknown_accuracy = (
        correct_unknown_count / expected_unknown_count
        if expected_unknown_count
        else 1.0
    )
    citation_binding = (
        citation_bound_count / predicted_present_count
        if predicted_present_count
        else 1.0
    )
    return EvaluationMetrics(
        case_count=len(corpus["cases"]),
        expected_present=expected_present_count,
        predicted_present=predicted_present_count,
        exact_matches=exact_matches,
        false_positives=false_positives,
        false_negatives=false_negatives,
        expected_unknown=expected_unknown_count,
        correct_unknown=correct_unknown_count,
        citation_bound=citation_bound_count,
        precision=precision,
        recall=recall,
        unknown_accuracy=unknown_accuracy,
        citation_binding=citation_binding,
    )


def main() -> int:
    metrics = evaluate_material_terms()
    print(json.dumps(asdict(metrics), indent=2, sort_keys=True))
    return 0 if (
        metrics.precision >= 0.95
        and metrics.recall >= 0.90
        and metrics.unknown_accuracy == 1.0
        and metrics.citation_binding == 1.0
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())