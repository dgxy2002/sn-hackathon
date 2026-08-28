# E07 Backlog - Explainable Decision Support

**Epic:** [E07 - Explainable Decision Support](../epics/E07-explainable-decision-support.md)
**Owner:** Deborah

## E07-T01 - Demonstrate gap analysis and synthetic comparison

| Field | Value |
|---|---|
| Status | Done |
| Priority | P0 |
| Size | M |
| Depends on | E03-T01 |

**User story:** As a demo user, I need to see protection gaps and multiple synthetic options so I can understand the proposed decision-support output.

**Requirements:** URS-FR-009, URS-FR-010, URS-FR-011; PRD-FR-009, PRD-FR-010.

**Acceptance criteria:**

- [x] Death and critical-illness gaps use visible MoneySense reference points.
- [x] Three synthetic plans show premiums, benefits, downsides, and evidence status.
- [x] The comparison includes assumptions and at least one exclusion reason.

**Evidence:** `comparisonView` in [`frontend/src/main.js`](../../frontend/src/main.js).

## E07-T02 - Implement data-driven rules and plan fixtures

| Field | Value |
|---|---|
| Status | In progress |
| Priority | P0 |
| Size | L |
| Depends on | E03-T02, E07-T06, E08-T01 |

**User story:** As a user, I need rankings driven by visible rules and my profile so different circumstances produce reproducible results.

**Requirements:** URS-FR-009, URS-FR-010, URS-FR-015, URS-FR-017, URS-FR-019, URS-NFR-003, URS-NFR-013; PRD-FR-009, PRD-FR-019, PRD-FR-024, PRD-NFR-002, PRD-NFR-008, PRD-NFR-013, PRD-NFR-016.

**Acceptance criteria:**

- [ ] Plans and rules are separate versioned data fixtures.
- [ ] Gap and affordability formulas are deterministic.
- [ ] Budget, duration, preference, and scenario constraints exclude before ranking.
- [ ] Weighted fit components are returned for eligible plans.
- [ ] Missing critical data can produce no recommendation.

## E07-T03 - Produce grounded explanation contract

| Field | Value |
|---|---|
| Status | Ready |
| Priority | P0 |
| Size | M |
| Depends on | E07-T02, E06-T03 |

**User story:** As a user, I need understandable reasons and trade-offs that remain faithful to the calculated decision.

**Requirements:** URS-FR-011, URS-FR-014, URS-FR-015, URS-NFR-004, URS-NFR-010; PRD-FR-010, PRD-FR-019, PRD-NFR-003, PRD-NFR-010, PRD-NFR-015.

**Acceptance criteria:**

- [ ] The decision contract contains rank, reason codes, exclusions, trade-offs, assumptions, confidence, and evidence IDs.
- [ ] Explanation generation cannot change rank, eligibility, or numerical values.
- [ ] Unsupported evidence is omitted or labelled.
- [ ] The educational boundary and synthetic status remain visible.

## E07-T04 - Validate decision correctness on reviewed profiles

| Field | Value |
|---|---|
| Status | Ready |
| Priority | P0 |
| Size | M |
| Depends on | E07-T02, E07-T03 |

**User story:** As a reviewer, I need prewritten ground truth and deterministic tests so recommendation claims are provably correct for the synthetic catalogue.

**Requirements:** URS-FR-019, URS-NFR-003, URS-NFR-004, URS-NFR-013; PRD-FR-009, PRD-FR-010, PRD-FR-019, PRD-FR-024, PRD-NFR-002, PRD-NFR-013, PRD-NFR-016.

**Acceptance criteria:**

- [ ] At least 20 diverse synthetic profiles have expected category and reasons written before execution.
- [ ] Hard-rule violations equal zero.
- [ ] Top-category agreement is at least 90%.
- [ ] Every output includes assumptions, trade-offs, missing data, and evidence status.
- [ ] The model does not grade its own result.

## E07-T05 - Add affordability, duplication, and replacement safeguards

| Field | Value |
|---|---|
| Status | Ready |
| Priority | P0 |
| Size | M |
| Depends on | E07-T02, E03-T05 |

**User story:** As a policyholder, I need the comparison to account for existing coverage and policy-replacement risks so the POC does not encourage harmful duplication or cancellation.

**Requirements:** URS-FR-009, URS-FR-010, URS-FR-011, URS-FR-014, URS-FR-015, URS-NFR-001, URS-NFR-003; PRD-FR-009, PRD-FR-010, PRD-FR-019, PRD-NFR-002, PRD-NFR-009, PRD-NFR-015.

**Acceptance criteria:**

- [ ] Calculations include existing private, government, and employer coverage without double counting.
- [ ] Affordability includes premium burden, emergency-fund resilience, and ability to maintain premiums through employment change.
- [ ] Existing and proposed benefits, exclusions, and coverage periods are compared where evidence permits.
- [ ] Replacement or underwriting risk is flagged and the system never recommends cancellation or surrender.
- [ ] Missing existing-policy terms produce assumptions or no recommendation, not a fabricated comparison.

## E07-T06 - Approve the grounded ranking formulation

| Field | Value |
|---|---|
| Status | Ready |
| Priority | P0 |
| Size | M |
| Depends on | E03-T02 |

**User story:** As a reviewer, I need one approved formulation document so every gap, exclusion, and ranking can be checked independently of code or model wording.

**Requirements:** URS-FR-009, URS-FR-010, URS-FR-011, URS-FR-026, URS-NFR-003, URS-NFR-013; PRD-FR-009, PRD-FR-019, PRD-FR-031, PRD-NFR-002, PRD-NFR-013.

**Acceptance criteria:**

- [ ] The document cites sources and defines variables, units, formulas, rounding, effective dates, and unknown-value behavior.
- [ ] It defines protection gaps, affordability, hard exclusions, eligibility, duplicate-coverage handling, replacement risk, weighted fit, tie-breaking, confidence, and no-recommendation thresholds.
- [ ] Every decision path has stable reason codes and at least one worked example.
- [ ] A named reviewer approves a version and date; later changes append a change record.
- [ ] Recommendation output records formulation and ruleset versions and E07-T02 cannot complete before approval.

## E07-T07 - Rerun decisions and produce summary deltas

| Field | Value |
|---|---|
| Status | Ready |
| Priority | P1 |
| Size | M |
| Depends on | E07-T02, E07-T03, E07-T06 |

**User story:** As a user changing an input, I need the comparison recalculated by the approved rules and shown as an explainable before/after delta.

**Requirements:** URS-FR-012, URS-FR-031, URS-NFR-003, URS-NFR-019; PRD-FR-037, PRD-NFR-002, PRD-NFR-013, PRD-NFR-025.

**Acceptance criteria:**

- [ ] The service accepts versioned profile, extraction, catalogue, evidence, formulation, and ruleset references plus an optional prior result.
- [ ] The same versioned inputs reproduce the same gaps, eligibility, fit, ranking, assumptions, and reason codes.
- [ ] A typed delta identifies changed inputs, calculations, eligibility, ranking, comparison rows, assumptions, citations, and explanation facts.
- [ ] Insufficient or stale evidence yields focused questions, warnings, or no recommendation rather than inferred values.
- [ ] Undo recalculates or restores a coherent prior result and never patches individual displayed numbers directly.

## E07-T08 - Enable the gated real-product ranked pilot

| Field | Value |
|---|---|
| Status | Ready |
| Priority | P1 |
| Size | L |
| Depends on | E06-T09, E07-T04, E07-T05, E07-T06, E08-T10, DEC-004 Phase 6 approval |

**User story:** As an internal reviewer, I need real products ranked only from complete, approved evidence through the same deterministic formulation so the result can be audited and safely declined when evidence is insufficient.

**Requirements:** URS-FR-010, URS-FR-011, URS-FR-015, URS-FR-026, URS-FR-034, URS-FR-035, URS-NFR-003, URS-NFR-004, URS-NFR-019; PRD-FR-019, PRD-FR-031, PRD-FR-039, PRD-FR-041, PRD-NFR-002, PRD-NFR-015, PRD-NFR-016.

**Acceptance criteria:**

- [ ] A named product, compliance, and decision-support approval reopens DEC-004 for a bounded internal Phase 6 pilot.
- [ ] Only ranking-eligible products with complete formulation-required premiums, eligibility, benefits, exclusions, term, effective/version state, and freshness enter evaluation.
- [ ] The deterministic engine records profile, catalogue, evidence, formulation, and ruleset versions and returns stable eligibility, fit, ordering, reason codes, and no-recommendation outcomes.
- [ ] Incomplete, stale, conflicting, or unapproved products are excluded with reason codes and cannot be repaired by model inference.
- [ ] Model-generated explanation cannot change eligibility, rank, score, values, evidence IDs, or abstention.
- [ ] Synthetic ranked mode remains available as a labelled fallback and regression baseline.
- [ ] The pilot cannot transact, recommend cancellation or surrender, claim whole-market coverage, or present itself as regulated advice.