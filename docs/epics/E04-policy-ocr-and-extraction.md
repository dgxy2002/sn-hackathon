# E04 - Policy OCR and Extraction

| Field | Value |
|---|---|
| Primary owner | Tim |
| Priority | P1 |
| Status | In progress |
| Outcome | OpenRouter `5.6 Luna` converts a synthetic policy document into reviewable structured fields with confidence and page evidence. |

## Scope

- In plain language, E04 reads what the user already has; E05 collects what insurers currently offer.
- Accept representative PDF and image policy documents through the backend API.
- Use the configured OpenRouter document adapter for PDF/image ingestion, OCR, and field extraction.
- Show confidence, page or region evidence, warnings, and unresolved values.
- Route conversational field corrections through the same provenance-preserving review and confirmation path.
- Keep a schema-identical fixture adapter for offline and judged-demo fallback.
- Record provider, exact model slug, prompt, latency, tokens, estimated cost, and corrections.
- Run in the local backend container and use the same image and environment contract on ECS Fargate later.

## Requirements traceability

- **URS:** [URS-FR-007, URS-FR-008, URS-FR-017, URS-FR-018, URS-FR-020, URS-FR-022, URS-FR-024, URS-FR-030, URS-FR-031, URS-NFR-004, URS-NFR-005, URS-NFR-007, URS-NFR-010, URS-NFR-011, URS-NFR-013, URS-NFR-015, URS-NFR-017, URS-NFR-019](../urs/URS.md)
- **PRD:** [PRD-FR-006, PRD-FR-016, PRD-FR-021, PRD-FR-025, PRD-FR-027, PRD-FR-036, PRD-FR-037, PRD-NFR-003, PRD-NFR-004, PRD-NFR-005, PRD-NFR-010, PRD-NFR-017, PRD-NFR-022, PRD-NFR-025](../prd/PRD.md)
- **Backlog:** [E04 tickets](../backlog/E04-policy-ocr-and-extraction.md)

## Repository evidence

- [`frontend/src/main.js`](../../frontend/src/main.js) implements upload and hard-coded extraction review views.
- [`backend/scraper/supabase_schema.sql`](../../backend/scraper/supabase_schema.sql) defines policy, coverage, premium, exclusion, rider, and document-chunk storage foundations.
- [`docs/PLAN.md`](../PLAN.md) defines target fields and the OCR efficiency experiment.

## Definition of done

- [x] The POC UI accepts a file selection or synthetic sample and displays extracted-field states.
- [ ] At least three representative synthetic policy documents are processed through the configured OpenRouter adapter.
- [ ] Every extracted field includes confidence and page or region provenance.
- [ ] Low-confidence or absent values remain unresolved and can be corrected by the user.
- [ ] Conversational corrections retain field provenance, reject stale or unsupported patches, and cannot create a reviewed extraction version before confirmation.
- [ ] The fixture adapter returns the same schema and is visibly labelled as simulated.
- [ ] The demo reports field accuracy, latency, token use, estimated cost, context size, and manual corrections with provider and exact model slug.
- [ ] The extraction capability passes health, termination, and contract checks in the local backend container.

## POC boundary

Use synthetic documents only. Long-term document storage, medical-document processing, and production redaction controls belong to E09.