from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from uuid import uuid4

from .config import CapabilityMode
from .contracts import ExtractionField, ExtractionResult, ExtractionReviewRequest


DEFAULT_MANIFEST = Path(__file__).resolve().parents[1] / "fixtures" / "policies" / "manifest.json"


class ExtractionFixtureNotFoundError(LookupError):
    pass


class ExtractionNotFoundError(LookupError):
    pass


class ExtractionVersionConflictError(ValueError):
    pass


class FixtureExtractionService:
    def __init__(
        self,
        mode: CapabilityMode = "simulated",
        manifest_path: Path = DEFAULT_MANIFEST,
    ) -> None:
        self.mode = mode
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self._documents = {
            document["fixture_id"]: document for document in manifest["documents"]
        }
        self._results: dict[str, ExtractionResult] = {}

    def submit(self, fixture_id: str) -> ExtractionResult:
        document = self._documents.get(fixture_id)
        if document is None:
            raise ExtractionFixtureNotFoundError(fixture_id)
        fields = []
        for truth in document["fields"]:
            value = deepcopy(truth["value"])
            is_unknown = truth["match"] == "unknown" or value == "unknown"
            fields.append(
                ExtractionField(
                    field_name=truth["path"],
                    original_value=None if is_unknown else self._display(value),
                    reviewed_value=None,
                    state="unknown" if is_unknown else "present",
                    confidence=None if is_unknown else 1.0,
                    evidence_ids=[
                        f"{fixture_id}:page-{truth['page']}:"
                        f"{truth['region']['x']}-{truth['region']['y']}-"
                        f"{truth['region']['width']}-{truth['region']['height']}"
                    ],
                )
            )
        result = ExtractionResult(
            extraction_id=f"extraction-{uuid4()}",
            version=1,
            mode=self.mode,
            document_supplied=True,
            review_required=True,
            fields=fields,
        )
        self._results[result.extraction_id] = result
        return result

    def review(
        self,
        extraction_id: str,
        request: ExtractionReviewRequest,
    ) -> ExtractionResult:
        current = self.get(extraction_id)
        if current.version != request.expected_version:
            raise ExtractionVersionConflictError(extraction_id)
        known = {field.field_name: field for field in current.fields}
        reviewed = []
        for field in request.fields:
            original = known.get(field.field_name)
            if original is None or not original.evidence_ids:
                raise ValueError(f"Unsupported extraction field: {field.field_name}")
            reviewed.append(
                field.model_copy(
                    update={
                        "original_value": original.original_value,
                        "evidence_ids": original.evidence_ids,
                    }
                )
            )
        result = current.model_copy(
            update={
                "version": current.version + 1,
                "review_required": False,
                "fields": reviewed,
            }
        )
        self._results[extraction_id] = result
        return result

    def get(self, extraction_id: str) -> ExtractionResult:
        try:
            return self._results[extraction_id]
        except KeyError as error:
            raise ExtractionNotFoundError(extraction_id) from error

    @staticmethod
    def _display(value: object) -> str:
        if isinstance(value, dict):
            return f"{value['value']} {value['unit']}"
        return str(value)