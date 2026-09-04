# Conventions

- Keep frontend and backend module setup independent; there is no root workspace/build command.
- Frontend currently follows vanilla ES-module style: single quotes, no semicolons, two-space indentation; preserve existing accessibility attributes and static asset paths.
- Python uses type annotations, explicit exception classes, strict Pydantic contracts, and stable content-free error envelopes.
- Treat `.env` as user-owned. Never commit credentials or expose them to the frontend, logs, documents, tests, or generated artifacts.
- Structured findings must retain provenance, source hashes/spans, confidence, explicit value state, and confirmation state.
- Parsing, privacy detection, extraction, calculations, and statuses must be deterministic and testable; an optional LLM may only render validated redacted inputs.
- Keep raw files and extracted text in transient local workspaces and verify cleanup after success, failure, cancellation, expiry, and deletion.
- Frontend design protocols are on-demand skills under `.agents/skills/`; their quality-gate sequence must run before implementation when invoked.
