# Project Core

- Before You Commit is a local-first Singapore life-insurance commitment reality check built for the IGNITE Agentic AI Hackathon.
- `PLAN.md` is the sole active product, architecture, migration, and acceptance authority. Superseded material under `docs/archive/` is historical only.
- The active product path is `/api/v2`: real PDF upload, local parsing/OCR, privacy review, source-bound term extraction, human confirmation, and deletion.
- Preserve explicit unknowns, source hashes/spans, transient raw data, and deterministic ownership of facts and statuses.
- Never send raw files or extracted text to a model. Model access remains optional and requires redacted, validated, consented inputs.
- Keep results neutral: evidence completeness and follow-up questions only, with no recommendation, suitability judgment, or action directive.
- Frontend guidance is in `mem:frontend/core`; backend guidance is in `mem:backend/core`; commands and completion checks have dedicated memories.
