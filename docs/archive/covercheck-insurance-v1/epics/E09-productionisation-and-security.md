# E09 - Productionisation and Security

| Field | Value |
|---|---|
| Primary owner | Tim |
| Priority | P3 |
| Status | Deferred |
| Outcome | After POC validation, the system can be hardened for real users, sensitive documents, and regulated operating conditions. |

## Scope

- Production identity, authorization, tenancy, and durable user state.
- Encryption, retention, deletion, audit logging, redaction, and incident response.
- Deployment automation, monitoring, backups, availability, and cost controls.
- Legal, privacy, and financial-regulation review for Singapore.
- Explicit public-launch approval and automatic-disable policy for real-product ranked mode after an accepted internal Phase 6 pilot.
- Abuse cases, penetration testing, dependency scanning, and operational runbooks.

Basic `.env` exclusion, AWS Secrets Manager mapping, non-root containers, health checks, and secret-safe logging are POC delivery safeguards owned by E10/E11. This epic owns later rotation, access governance, auditing, resilience, and production approval rather than blocking the local-first POC.

## Requirements traceability

- **URS:** [URS-NFR-005, URS-NFR-008, URS-NFR-014](../urs/URS.md)
- **PRD:** [PRD-NFR-004, PRD-NFR-007, PRD-NFR-019](../prd/PRD.md)
- **Backlog:** [E09 tickets](../backlog/E09-productionisation-and-security.md)
- **Public ranked mode:** URS-FR-035; PRD-FR-041.

## Repository evidence

- [`backend/scraper/card_scraper.py`](../../backend/scraper/card_scraper.py) loads Supabase credentials from environment variables.
- [`backend/scraper/supabase_schema.sql`](../../backend/scraper/supabase_schema.sql) provides initial row-level-security policies and database roles.
- [`frontend/src/main.js`](../../frontend/src/main.js) labels educational and synthetic POC output.
- [`docs/PLAN.md`](../PLAN.md) defines the product trust boundary and production exclusions.

## Definition of done

- [ ] A reviewed threat model covers identity, documents, agent tools, retrieval, and model-data exposure.
- [ ] Users can access only their own encrypted data and can request export and deletion.
- [ ] Secrets are centrally managed, rotated, and absent from client bundles and logs.
- [ ] Audit, monitoring, backup, recovery, retention, and incident-response controls are tested.
- [ ] Security, privacy, and regulatory reviews approve the intended public use and wording.
- [ ] Public real-product ranked mode has an explicit launch decision covering scope, sources, conflicts, disclaimers, monitoring, rollback, complaints, and accountable owners.
- [ ] Load, resilience, dependency, and penetration tests meet agreed service targets.

## POC boundary

This epic is intentionally low priority and deferred. The POC still must not expose credentials, use real customer policy documents, misrepresent synthetic data, or cross the educational-not-advice boundary.