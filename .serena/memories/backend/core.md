# Backend

- Active package: `backend/app/` with `main.py`, `api_v2.py`, `contracts_v2.py`, `analysis_service.py`, `document_service.py`, `material_extraction.py`, and `scraper_worker.py`.
- `main.py` exposes health and `/api/v2` only. Product behavior belongs behind strict v2 contracts.
- Keep raw PDFs, extracted text, and page images inside opaque per-analysis local workspaces. Preserve size/page limits, TTL, idempotency, and cleanup behavior.
- `material_extraction.py` owns deterministic source-bound candidates and explicit unknown/conflict states; no LLM is required.
- PostgreSQL schema is `backend/docker/postgres-init.sql`; Compose database URLs derive from the configured PostgreSQL role/database.
- `scraper_worker.py` is reserved for allowlisted official guidance and must use normalized evidence records.
