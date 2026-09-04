# E02 Backlog - Readiness Quiz and Peer Benchmark

**Epic:** [E02 - Readiness Quiz and Peer Benchmark](../epics/E02-readiness-quiz-and-peer-benchmark.md)
**Owner:** Jana

## E02-T01 - Implement the public readiness quiz

| Field | Value |
|---|---|
| Status | Done |
| Priority | P0 |
| Size | S |
| Depends on | E01-T01 |

**User story:** As a curious first-time worker, I need a short public quiz so I can discover insurance knowledge gaps before sharing profile data.

**Requirements:** URS-FR-001; PRD-FR-002.

**Acceptance criteria:**

- [x] Four questions cover current-cover visibility, total cost, benefit response, and limits/end dates.
- [x] No sign-in is required.
- [x] The check is optional and can be skipped for a direct protection route.
- [x] Progress and selected answers are preserved during the quiz.

**Evidence:** [`frontend/src/main.js`](../../frontend/src/main.js).

## E02-T02 - Calculate and explain the readiness result

| Field | Value |
|---|---|
| Status | Done |
| Priority | P0 |
| Size | S |
| Depends on | E02-T01 |

**User story:** As a quiz participant, I need a repeatable result and coverage map so I can see which details I understand and which remain unclear.

**Requirements:** URS-FR-002, URS-NFR-003; PRD-FR-002, PRD-NFR-002.

**Acceptance criteria:**

- [x] Identical answers produce an identical score.
- [x] The result separates coverage visibility, protection basics, and terms awareness using displayed weights of 50%, 25%, and 25%.
- [x] Copy describes information gaps rather than personal worth or suitability.

**Evidence:** `getScore` and `resultView` in [`frontend/src/main.js`](../../frontend/src/main.js).

## E02-T03 - Render the labelled pilot benchmark

| Field | Value |
|---|---|
| Status | Done |
| Priority | P0 |
| Size | S |
| Depends on | E02-T02 |

**User story:** As a quiz participant, I need context from a clearly described pilot group so comparison creates curiosity without pretending to represent Singapore.

**Requirements:** URS-FR-003, URS-NFR-001, URS-NFR-009; PRD-FR-003, PRD-NFR-009.

**Acceptance criteria:**

- [x] Pilot sample size, age range, and collection dates are shown.
- [x] No unsupported Singapore-wide percentile is claimed.
- [x] Comparison language avoids shame and fear.

**Evidence:** [`frontend/src/main.js`](../../frontend/src/main.js).

## E02-T04 - Validate quiz comprehension with target users

| Field | Value |
|---|---|
| Status | Ready |
| Priority | P1 |
| Size | M |
| Depends on | E02-T03 |

**User story:** As the product team, we need observed target-user evidence so we know whether the quiz and comparison are understandable and motivating.

**Requirements:** URS-FR-002, URS-FR-003, URS-NFR-009; PRD-FR-002, PRD-FR-003.

**Acceptance criteria:**

- [ ] At least five target users attempt the quiz without facilitation.
- [ ] At least four complete it and correctly explain the result.
- [ ] Emotional response and continuation intent are recorded.
- [ ] Confusing or manipulative copy is revised and retested.

## E02-T05 - Implement the full Insurance Readiness Score rubric

| Field | Value |
|---|---|
| Status | Ready |
| Priority | P1 |
| Size | M |
| Depends on | E02-T04, E03-T05 |

**User story:** As a user, I need a transparent readiness score that covers more than policy recall so I can understand foundations, affordability, and action literacy.

**Requirements:** URS-FR-002, URS-FR-003, URS-FR-006, URS-NFR-003, URS-NFR-009; PRD-FR-002, PRD-FR-003, PRD-NFR-002, PRD-NFR-009.

**Acceptance criteria:**

- [ ] The score uses coverage visibility 30%, protection foundations 25%, affordability and resilience 25%, and action literacy 20%.
- [ ] The result exposes the source and calculation for every score component.
- [ ] Unknown inputs remain unknown and do not score as no coverage.
- [ ] Peer percentiles require a relevant cohort of at least 10 and show segment, sample size, and date.
- [ ] Fixture answers cover minimum, maximum, unknown-heavy, and boundary scores.