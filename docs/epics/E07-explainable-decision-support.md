# E07 - Explainable Decision Support

| Field | Value |
|---|---|
| Primary owner | Deborah |
| Priority | P0 |
| Status | In progress |
| Outcome | Synthetic profiles receive reproducible plan-category rankings with visible reasons, exclusions, assumptions, and trade-offs. |

## Scope

- Deterministic protection-gap and affordability calculations.
- Produce and approve a grounded formulation document before enabling ranking.
- Hard eligibility constraints before ranking.
- Transparent weighted fit across eligible synthetic plans.
- Grounded plain-language explanation that cannot alter the calculated result.
- Alternative and insufficient-data outcomes.
- Deterministic reruns and typed before/after deltas for confirmed profile, comparison, or extraction changes.

## Requirements traceability

- **URS:** [URS-FR-009, URS-FR-010, URS-FR-011, URS-FR-012, URS-FR-015, URS-FR-017, URS-FR-019, URS-FR-026, URS-FR-031, URS-NFR-003, URS-NFR-004, URS-NFR-010, URS-NFR-013, URS-NFR-019](../urs/URS.md)
- **PRD:** [PRD-FR-009, PRD-FR-010, PRD-FR-019, PRD-FR-024, PRD-FR-031, PRD-FR-037, PRD-NFR-002, PRD-NFR-003, PRD-NFR-013, PRD-NFR-015, PRD-NFR-016, PRD-NFR-025](../prd/PRD.md)
- **Backlog:** [E07 tickets](../backlog/E07-explainable-decision-support.md)

## Repository evidence

- [`frontend/src/main.js`](../../frontend/src/main.js) calculates death and critical-illness gaps and renders a static three-plan synthetic comparison.
- [`docs/PLAN.md`](../PLAN.md) defines the hybrid decision method, recommendation contract, and reviewed synthetic-profile evaluation.

## Definition of done

- [x] The POC displays calculated gaps, synthetic alternatives, assumptions, and at least one exclusion reason.
- [ ] A versioned formulation document defines sourced formulas, variables, units, unknown handling, affordability, hard exclusions, duplicate coverage, replacement risk, weighted fit, reason codes, and worked examples.
- [ ] The formulation has a named reviewer, approval date, and change history; ranking cannot be released without approval.
- [ ] Plans and rules are data-driven rather than embedded in view markup.
- [ ] Hard constraints produce zero violations across at least 20 reviewed synthetic profiles.
- [ ] At least 90% of top plan categories agree with ground truth written before execution.
- [ ] Every output includes fit components, trade-offs, missing data, confidence, and evidence IDs.
- [ ] Insufficient evidence or profile data can return no recommendation.
- [ ] Existing government, employer, and private coverage is considered without double counting.
- [ ] Replacement and underwriting risks are flagged without recommending cancellation or surrender.
- [ ] Every recommendation records the formulation and ruleset versions used.
- [ ] Confirmed changes rerun the same formulation and return one coherent delta; undo restores or recalculates a complete prior result rather than patching displayed values.

## POC boundary

Outputs are educational comparisons using synthetic plans. The system must not purchase, replace, surrender, or recommend cancelling a policy.