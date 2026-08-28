# Real-product Comparison and Ranking Stages - 2026-08-28

## Document control

| Field | Value |
|---|---|
| Status | Contract and synthetic fixture implemented; real-product entry gates pending |
| Decision date | 28 August 2026 |
| Scope | Introduce real-product comparison at the earliest safe point while preserving the synthetic E07 recommendation boundary |
| Governing decision | Extends the [RAG and website integration decision](2026-08-28-rag-website-integration-decisions.md); does not change `docs/PLAN.md` |

## Decision

Real-product data enters the main comparison surface in two deliberately separate stages:

1. **Phase 3B - Real-product evidence comparison:** a read-only, non-ranked side-by-side view of a small comparison-eligible subset. It may ship after the direct E10/E06 read path and the Phase 3 website integration pass. It does not require E07 ranking or E11 consequential orchestration.
2. **Phase 6 - Real-product ranked pilot:** an internal, compliance-approved ranking over a ranking-eligible subset. It may begin only after Phase 5 acceptance, E07 formulation and correctness gates, source and field completeness gates, and an explicit decision reopening DEC-004.

The existing synthetic E07 ranked comparison remains the canonical POC recommendation until Phase 6 is approved and accepted. Public real-product ranking remains blocked by E09 regulatory and production-readiness approval.

## Product states

| State | Minimum meaning | Permitted use |
|---|---|---|
| Searchable evidence | A cached record with explicit approval/evidence state and provenance | Search results and cited questions only |
| Comparison eligible | Reuse is approved; product identity, authoritative URL, document version/as-of evidence, and freshness are reviewable; every displayed field has comparable units and field-level evidence | Neutral, read-only side-by-side evidence comparison |
| Ranking eligible | All comparison gates pass and decision-critical premium assumptions, eligibility, benefits, exclusions, term, effective/version state, and freshness are complete enough for the approved formulation | Deterministic E07 eligibility and ranking after Phase 6 approval |

Searchability never implies comparison eligibility. Comparison eligibility never implies suitability or ranking eligibility. Unknown values remain `Unknown` and cannot be inferred from brochure capture time, similarity score, or neighbouring products.

## Phase 3B - Real-product evidence comparison

### Earliest entry gate

Phase 3B may start when all of the following are true for a deliberately small pilot subset in one product category:

- The E10/E06 read-only API contract is stable and credential boundaries pass.
- Each included source has an approved reuse decision, authoritative URL, unambiguous product identity, and non-stale/non-conflicting evidence state.
- Every displayed value resolves to a quoted source span, date type, product/document version where available, and normalized unit.
- Missing premium, eligibility, exclusion, benefit, term, or effective-date values render as `Unknown` rather than being inferred.
- E08 predeclares comparison fixtures covering complete, partial, stale, conflicting, and no-evidence outcomes.

The full 71-product corpus does not need to become comparison eligible before the pilot starts. Records that fail the gate remain searchable evidence only.

### Experience boundary

- A user may select two to four comparison-eligible products from one category.
- Rows are ordered neutrally, using provider then product name. Retrieval similarity may support discovery but cannot order the comparison table.
- The table shows only source-backed fields and places citations, evidence state, and dates beside the relevant values.
- The surface is labelled **Real-product evidence comparison - not a recommendation**.
- Recommendation badges, fit scores, suitability language, and an "absolute best" claim are prohibited.
- Adding, removing, sorting, or filtering real-product rows is a presentation action. It cannot change the active profile, E07 catalogue, recommendation result, summary revision, or ranking.
- The synthetic ranked recommendation remains visually and semantically separate, even when both surfaces appear on the same page.

### Phase 3B acceptance

- Two to four reviewed products in one category render side by side from the E10/E06 contract.
- One hundred percent of populated comparison cells have field-level evidence, source, and date state.
- Unknown, stale, conflicting, and unsupported values never become verified comparison facts.
- Reordering discovery results cannot change neutral comparison order.
- Before and after recommendation contracts are byte-equivalent when only evidence-comparison presentation changes.
- Desktop, mobile, keyboard, and reduced-motion checks pass.

## Phase 6 - Real-product ranked pilot

### Earliest entry gate

Phase 6 begins only after:

- Phases 0-5, including fixed retrieval evaluation and local PostgreSQL/pgvector parity, are accepted or their exceptions are explicitly approved.
- E07's versioned formulation, hard constraints, affordability, duplicate-coverage, replacement-risk, tie-breaking, confidence, and no-recommendation rules are approved.
- E07 passes zero hard-rule violations and the agreed category/ranking target on independently reviewed fixtures.
- Every candidate product is ranking eligible and has complete source-backed decision inputs required by the formulation.
- DEC-004 is reopened with named product, compliance, and decision-support approval for a bounded internal pilot.
- E08 predeclares real-product ground truth, stale/conflict cases, missing-field abstention, ranking stability, and explanation-fidelity tests.

### Ranked-pilot boundary

- Ranking is deterministic and records profile, catalogue, evidence, formulation, and ruleset versions.
- The model may explain a fixed result but cannot author eligibility, fit, ordering, or numerical values.
- Incomplete, stale, conflicting, or unapproved candidates are excluded with reason codes or cause a no-recommendation result.
- Synthetic mode remains available as a labelled fallback and regression baseline.
- The pilot cannot transact, recommend cancellation or surrender, or claim whole-market coverage or regulated advice.

## Availability answer

| Mode | Earliest pipeline point | Current status |
|---|---|---|
| Synthetic ranked mode | Existing E07 POC surface | API-backed and visible now; formulation approval and full E07 evaluation remain pending |
| Real-product evidence comparison | Phase 3B, after the pilot subset passes its source and field evidence gates | Next comparison milestone |
| Real-product ranked mode | Phase 6, after Phase 5 acceptance, E07 validation, ranking-eligible product data, and explicit DEC-004/compliance approval | Not approved for the current POC |
| Public real-product ranked mode | After Phase 6 plus E09 legal, privacy, security, regulatory, and operational approval | Deferred |

No calendar date is asserted until owners size the incomplete source-governance, product-field, E07, and evaluation work. Passing Phase 3B alone does not authorize Phase 6.

The [integrated runtime and browser acceptance](2026-08-28-integrated-runtime-browser-acceptance.md) verifies the neutral comparison contract, synthetic browser fixture, canonical isolation, responsive rendering, and rejection of configured cached products that fail the gate. It does not accept a real-product Phase 3B subset.

## Ownership and implementation path

| Work | Owner |
|---|---|
| Source permission, product identity, version/freshness, normalized comparison fields | E06 / Darren |
| Typed evidence-comparison API and unchanged canonical-state guarantees | E10 / Tim |
| Main-surface evidence mode and accessible neutral table | E01 / Tim |
| Conversational selection and presentation-only row changes | E12 / Tim |
| Comparison fixtures, invariants, and browser acceptance | E08 / Tim with E06 and E07 reviewers |
| Formulation extension and deterministic real-product ranking | E07 / Deborah |
| DEC-004 and internal ranked-pilot compliance approval | Product/compliance owner with Deborah |
| Public-use approval | E09 / Tim with legal, privacy, security, and compliance reviewers |

## Non-decisions

- This record does not approve any cached source for reuse.
- It does not declare any current product comparison eligible or ranking eligible.
- It does not change the local PostgreSQL/pgvector target.
- It does not place real products into the current E07 synthetic ranking.
- It does not authorize public use or financial advice.