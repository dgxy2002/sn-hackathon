# E07 - Explainable Decision Support

| Field | Value |
|---|---|
| Primary owner | Deborah |
| Priority | P0 |
| Status | In progress |
| Outcome | Synthetic profiles receive reproducible rankings now; a bounded real-product ranked pilot may use the same deterministic controls only after the Phase 6 gate. |

## Scope

- Deterministic protection-gap and affordability calculations.
- Produce and approve a grounded formulation document before enabling ranking.
- Hard eligibility constraints before ranking.
- Transparent weighted fit across eligible synthetic plans.
- Grounded plain-language explanation that cannot alter the calculated result.
- Alternative and insufficient-data outcomes.
- Deterministic reruns and typed before/after deltas for confirmed profile, comparison, or extraction changes.
- A separately approved Phase 6 extension that admits only ranking-eligible real products and preserves no-recommendation behavior.

## Requirements traceability

- **URS:** [URS-FR-009, URS-FR-010, URS-FR-011, URS-FR-012, URS-FR-015, URS-FR-017, URS-FR-019, URS-FR-026, URS-FR-031, URS-NFR-003, URS-NFR-004, URS-NFR-010, URS-NFR-013, URS-NFR-019](../urs/URS.md)
- **PRD:** [PRD-FR-009, PRD-FR-010, PRD-FR-019, PRD-FR-024, PRD-FR-031, PRD-FR-037, PRD-NFR-002, PRD-NFR-003, PRD-NFR-013, PRD-NFR-015, PRD-NFR-016, PRD-NFR-025](../prd/PRD.md)
- **Backlog:** [E07 tickets](../backlog/E07-explainable-decision-support.md)
- **Phase 6:** URS-FR-034, URS-FR-035; PRD-FR-039, PRD-FR-041.

## Repository evidence

- [`backend/app/decision_support.py`](../../backend/app/decision_support.py) calculates deterministic gaps, exclusions, fit, and ranking from versioned fixtures; [`frontend/src/main.js`](../../frontend/src/main.js) renders the returned contract.
- [`docs/PLAN.md`](../PLAN.md) defines the hybrid decision method, recommendation contract, and reviewed synthetic-profile evaluation.

## Definition of done

- [x] The POC displays calculated gaps, synthetic alternatives, assumptions, and at least one exclusion reason.
- [x] Death and TPD targets equal annual income x 9 plus liabilities; the critical-illness target equals annual income x 4.
- [x] Monthly expenses are non-critical because the current formulation does not use them; liabilities are critical because they change death and TPD targets.
- [ ] A versioned formulation document defines sourced formulas, variables, units, unknown handling, affordability, hard exclusions, duplicate coverage, replacement risk, weighted fit, reason codes, and worked examples.
- [ ] The formulation has a named reviewer, approval date, and change history; ranking cannot be released without approval.
- [x] Plans and rules are data-driven rather than embedded in view markup.
- [ ] Hard constraints produce zero violations across at least 20 reviewed synthetic profiles.
- [ ] At least 90% of top plan categories agree with ground truth written before execution.
- [ ] Every output includes fit components, trade-offs, missing data, confidence, and evidence IDs.
- [x] Insufficient evidence or profile data can return no recommendation.
- [x] Existing government, employer, and private coverage is considered without double counting.
- [x] Replacement and underwriting risks are flagged without recommending cancellation or surrender.
- [x] Every recommendation records the formulation and ruleset versions used.
- [x] Confirmed changes rerun the same formulation and return one coherent delta; undo restores or recalculates a complete prior result rather than patching displayed values.
- [x] Real-product ranked mode remains disabled until Phase 3B acceptance, all synthetic E07 correctness gates, ranking-eligible product data, predeclared E08 tests, and explicit DEC-004/compliance approval pass.
- [ ] Once approved for the internal pilot, real-product ranking is deterministic, versioned, independently evaluated, and able to abstain without model-authored repairs.

**Acceptance evidence:** [Integrated runtime and browser acceptance](../evaluation/2026-08-28-integrated-runtime-browser-acceptance.md) and [Gen-Z journey review](../evaluation/2026-09-03-gen-z-journey-and-project-truth.md). The ruleset remains a draft implementation: independent formulation approval and the 20-profile correctness evaluation are still required.

## POC boundary

Current POC outputs are educational comparisons using synthetic plans. Phase 3B real-product evidence is non-ranked. A Phase 6 internal ranked pilot does not authorize public use, purchase, replacement, surrender, or cancellation recommendations.