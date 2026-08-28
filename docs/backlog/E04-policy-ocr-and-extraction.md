# E04 Backlog - Policy OCR and Extraction

**Epic:** [E04 - Policy OCR and Extraction](../epics/E04-policy-ocr-and-extraction.md)
**Owner:** Tim

## E04-T01 - Implement the extraction review simulation

| Field | Value |
|---|---|
| Status | Done |
| Priority | P1 |
| Size | S |
| Depends on | E01-T02 |

**User story:** As a demo user, I need to see how extracted policy fields would be reviewed so the team can validate the experience before service integration.

**Requirements:** URS-FR-007, URS-FR-008; PRD-FR-006.

**Acceptance criteria:**

- [x] The UI accepts PDF, JPG, PNG, or a synthetic sample action.
- [x] Extracted fields display high, medium, and low confidence states.
- [x] The sample and extraction values are visibly synthetic.

**Evidence:** `uploadView`, `ocrField`, and `ocrView` in [`frontend/src/main.js`](../../frontend/src/main.js).

## E04-T02 - Confirm OpenRouter model and prepare labelled fixtures

| Field | Value |
|---|---|
| Status | In progress |
| Priority | P1 |
| Size | M |
| Depends on | None |

**User story:** As the extraction owner, I need the exact OpenRouter model configuration and a repeatable synthetic dataset so extraction claims can be measured.

**Requirements:** URS-FR-007, URS-FR-022, URS-NFR-005, URS-NFR-013; PRD-FR-006, PRD-FR-027, PRD-NFR-004, PRD-NFR-022.

**Acceptance criteria:**

- [ ] The exact OpenRouter slug represented by `5.6 Luna` is confirmed and assigned to `OPENROUTER_MODEL`.
- [ ] Provider, model, prompt, timeout, and token-limit configuration is documented without a real API key.
- [x] At least three representative synthetic policy pages are labelled with field truth and page regions.
- [x] Fixture licensing and synthetic status are documented.
- [x] Target fields and exact-match rules are frozen.

**Current evidence:** [`backend/fixtures/policies/manifest.json`](../../backend/fixtures/policies/manifest.json), the fixture [README](../../backend/fixtures/policies/README.md), three synthetic SVG policy pages, and [`backend/tests/test_policy_fixtures.py`](../../backend/tests/test_policy_fixtures.py). The exact OpenRouter slug and live-run configuration remain unresolved.

## E04-T03 - Build the OpenRouter extraction adapter

| Field | Value |
|---|---|
| Status | Ready |
| Priority | P1 |
| Size | L |
| Depends on | E04-T02, E03-T02, E08-T01 |

**User story:** As a user, I need document content converted into reviewable structured fields so analysis is based on my policy rather than a hard-coded sample.

**Requirements:** URS-FR-008, URS-FR-017, URS-FR-020, URS-FR-022, URS-NFR-004, URS-NFR-007, URS-NFR-010, URS-NFR-011, URS-NFR-013; PRD-FR-006, PRD-FR-016, PRD-FR-021, PRD-FR-027, PRD-NFR-003, PRD-NFR-005, PRD-NFR-008, PRD-NFR-010, PRD-NFR-017, PRD-NFR-022.

**Acceptance criteria:**

- [ ] The adapter processes the labelled PDF or image fixtures.
- [ ] The configured OpenRouter model performs PDF/image ingestion, OCR, and structured field extraction.
- [ ] Output validates against the extraction contract.
- [ ] Every field retains confidence and page or region provenance.
- [ ] Missing or low-confidence values are not guessed.
- [ ] The UI supports review and correction before confirmation.

## E04-T04 - Measure OpenRouter policy extraction

| Field | Value |
|---|---|
| Status | Ready |
| Priority | P1 |
| Size | M |
| Depends on | E04-T03 |

**User story:** As a judge, I need measured policy-extraction results so quality and efficiency claims are supported by evidence.

**Requirements:** URS-FR-018, URS-FR-019, URS-FR-022, URS-NFR-006, URS-NFR-007, URS-NFR-013; PRD-FR-025, PRD-FR-027, PRD-NFR-005, PRD-NFR-006, PRD-NFR-013, PRD-NFR-016.

**Acceptance criteria:**

- [ ] The configured OpenRouter path processes the frozen labelled pages.
- [ ] Field accuracy, latency, token use, estimated cost, context size, and corrections are recorded.
- [ ] Provider, exact model slug, prompt version, pricing assumptions, and run dates are included.
- [ ] The demo reports measured results without unsupported savings claims.

## E04-T05 - Verify containerized extraction and fixture fallback

| Field | Value |
|---|---|
| Status | Ready |
| Priority | P0 |
| Size | M |
| Depends on | E04-T03, E10-T06 |

**User story:** As a developer, I need live and fixture extraction to run behind the same containerized API contract locally and on AWS later.

**Requirements:** URS-FR-020, URS-FR-021, URS-FR-024, URS-NFR-015, URS-NFR-017; PRD-FR-021, PRD-FR-026, PRD-FR-029, PRD-NFR-017, PRD-NFR-021, PRD-NFR-022.

**Acceptance criteria:**

- [ ] OpenRouter and fixture adapters return the same versioned extraction schema.
- [ ] Adapter mode is selected by environment configuration and returned in API output.
- [ ] The backend container health report includes extraction-provider readiness without exposing credentials.
- [ ] Fixture mode completes when OpenRouter is unavailable and is visibly labelled simulated.
- [ ] The same backend image contract is documented for ECS Fargate.

## E04-T06 - Support confirmed extraction-field corrections

| Field | Value |
|---|---|
| Status | Ready |
| Priority | P1 |
| Size | M |
| Depends on | E04-T01, E10-T08 |

**User story:** As a policyholder, I need conversational corrections to extracted policy fields routed through the same review controls as manual corrections.

**Requirements:** URS-FR-008, URS-FR-030, URS-FR-031, URS-NFR-011, URS-NFR-019; PRD-FR-007, PRD-FR-036, PRD-FR-037, PRD-NFR-010, PRD-NFR-025.

**Acceptance criteria:**

- [ ] A correction proposal identifies the extraction version, field path, old value, proposed value, confidence, source span, and downstream impact.
- [ ] The user sees and confirms each material correction before a reviewed extraction version is created.
- [ ] Unsupported fields, invalid units, stale versions, and missing provenance are rejected visibly.
- [ ] Confirmation preserves original, model-extracted, user-corrected, and active values with timestamps and actor type.
- [ ] Applied corrections invalidate affected recommendation results and trigger no model-authored arithmetic.