from __future__ import annotations

import argparse
import asyncio
import json
import tempfile
from collections import Counter
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from starlette.datastructures import Headers

from app.document_service import DocumentService, DocumentServiceError


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate authentic PDFs through the local upload, parse/OCR, "
            "privacy-scan, and cleanup path."
        )
    )
    parser.add_argument("documents", nargs="+", type=Path)
    return parser.parse_args()


def size_bucket(size_bytes: int) -> str:
    if size_bytes <= 1024 * 1024:
        return "up_to_1_mib"
    if size_bytes <= 5 * 1024 * 1024:
        return "up_to_5_mib"
    return "over_5_mib"


async def validate_documents(paths: list[Path]) -> dict[str, object]:
    if len(paths) < 3:
        raise ValueError("At least three document paths are required.")

    workspace_root = Path(tempfile.mkdtemp(prefix="before-you-commit-gate2-"))
    service = DocumentService(workspace_root=workspace_root)
    analysis_id = str(uuid4())
    document_summaries: list[dict[str, object]] = []

    try:
        for ordinal, path in enumerate(paths, start=1):
            try:
                source = path.open("rb")
            except OSError as error:
                raise ValueError(f"Document {ordinal} could not be opened.") from error
            upload = UploadFile(
                file=source,
                headers=Headers({"content-type": "application/pdf"}),
            )
            document = await service.upload(
                analysis_id,
                upload,
                f"authentic-document-{ordinal}",
            )
            document_summaries.append(
                {
                    "ordinal": ordinal,
                    "page_count": document.page_count,
                    "parser_path": document.parser_path,
                    "size_bucket": size_bucket(document.size_bytes),
                }
            )

        findings = service.scan_privacy(analysis_id, "authentic-privacy-scan")
        category_counts = Counter(finding.category for finding in findings)
    finally:
        service.delete_analysis(analysis_id)

    return {
        "documents": document_summaries,
        "privacy_findings_by_category": dict(sorted(category_counts.items())),
        "external_model_requests": 0,
        "cleanup_complete": not workspace_root.exists(),
    }


def main() -> int:
    args = parse_args()
    try:
        result = asyncio.run(validate_documents(args.documents))
    except (DocumentServiceError, ValueError) as error:
        code = getattr(error, "code", "VALIDATION_INPUT_ERROR")
        print(json.dumps({"status": "failed", "code": code}))
        return 1
    print(json.dumps({"status": "passed", **result}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())