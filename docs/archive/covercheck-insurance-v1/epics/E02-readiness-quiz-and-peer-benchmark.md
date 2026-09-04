# E02 - Readiness Quiz and Peer Benchmark

| Field | Value |
|---|---|
| Primary owner | Jana |
| Priority | P0 |
| Status | In progress |
| Outcome | A first-time working adult can identify insurance knowledge gaps and compare readiness with a clearly labelled pilot cohort. |

## Scope

- Optional four-question public insurance-readiness check.
- Deterministic readiness score and dimension-level coverage map.
- Constructive peer benchmark with sample size, age range, and collection dates.
- Result copy that encourages curiosity without presenting suitability advice.

## Requirements traceability

- **URS:** [URS-FR-001, URS-FR-002, URS-FR-003, URS-NFR-001, URS-NFR-003, URS-NFR-009](../urs/URS.md)
- **PRD:** [PRD-FR-002, PRD-FR-003, PRD-NFR-002, PRD-NFR-009](../prd/PRD.md)
- **Backlog:** [E02 tickets](../backlog/E02-readiness-quiz-and-peer-benchmark.md)

## Repository evidence

- [`frontend/src/main.js`](../../frontend/src/main.js) defines the questions, `getScore`, `questionView`, and `resultView`.
- [`frontend/src/style.css`](../../frontend/src/style.css) styles the progress, score, benchmark distribution, and result table.
- [`docs/PLAN.md`](../PLAN.md) records scoring intent and peer-comparison guardrails.

## Definition of done

- [x] Four readiness questions can be completed with pointer or keyboard input, or skipped from the landing page.
- [x] The same answers always produce the same score.
- [x] Results distinguish known and unclear coverage dimensions.
- [x] Peer data is labelled as a hackathon pilot and displays cohort context.
- [x] The result routes users into the deeper profile journey.
- [ ] The full 0-100 IRS uses the planned 30/25/25/20 dimensions and exposes component calculations and sources.
- [ ] Unknown values remain unscored rather than becoming negative answers.
- [ ] At least five target users attempt the quiz and at least four complete and explain the result.

## POC boundary

The current screen shows coverage visibility at 50%, protection basics at 25%, and terms awareness at 25%. It remains usable as a conversation-starter POC slice, but it is not the planned full IRS. The epic is not complete until the transparent IRS and minimum observed-user validation are delivered. Larger-sample population calibration remains future work.