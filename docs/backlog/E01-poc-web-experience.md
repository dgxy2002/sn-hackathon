# E01 Backlog - POC Web Experience

**Epic:** [E01 - POC Web Experience](../epics/E01-poc-web-experience.md)
**Owner:** Tim

## E01-T01 - Establish the Vite application shell

| Field | Value |
|---|---|
| Status | Done |
| Priority | P0 |
| Size | S |
| Depends on | None |

**User story:** As a demo user, I need the POC to load quickly in a browser so I can start the readiness journey.

**Requirements:** URS-FR-001, URS-NFR-006; PRD-FR-001, PRD-NFR-006.

**Acceptance criteria:**

- [x] A Vite development command is available.
- [x] The application has a branded HTML entry point.
- [x] The production build completes successfully.

**Evidence:** [`frontend/package.json`](../../frontend/package.json), [`frontend/index.html`](../../frontend/index.html).

## E01-T02 - Implement the complete simulated journey

| Field | Value |
|---|---|
| Status | Done |
| Priority | P0 |
| Size | M |
| Depends on | E01-T01 |

**User story:** As a target user, I need to move from landing to comparison without team assistance so I can understand the proposed product experience.

**Requirements:** URS-FR-001, URS-FR-004, URS-FR-013; PRD-FR-001, PRD-FR-004.

**Acceptance criteria:**

- [x] Landing, quiz, result, account, onboarding, upload, extraction, and comparison views are reachable.
- [x] Back and forward actions preserve browser-session state.
- [x] The result journey links to the MAS representatives register.

**Evidence:** [`frontend/src/main.js`](../../frontend/src/main.js).

## E01-T05 - Render dynamic validated summary revisions

| Field | Value |
|---|---|
| Status | In progress |
| Priority | P1 |
| Size | L |
| Depends on | E01-T03, E07-T07, E10-T08 |

**User story:** As a user, I need the final comparison to respond visibly to validated agent actions without losing trust, accessibility, or internal consistency.

**Requirements:** URS-FR-029, URS-FR-031, URS-NFR-002, URS-NFR-021; PRD-FR-032, PRD-FR-035, PRD-FR-037, PRD-NFR-027.

**Acceptance criteria:**

- [ ] The final page renders conversation, action-event, proposal, summary-revision, and delta contracts without trusting model-authored markup.
- [ ] Presentation actions can focus, expand, sort, and filter existing summary regions.
- [ ] Applied revisions update all affected score, gap, comparison, assumption, evidence, and explanation regions atomically.
- [ ] Changed values are highlighted with stable layout, visible focus, reduced-motion behavior, and screen-reader announcements.
- [ ] Confirmation, cancellation, conflict, failure, replay, and undo states remain operable on narrow and wide viewports.

**Current evidence:** [`frontend/src/main.js`](../../frontend/src/main.js), [`frontend/src/style.css`](../../frontend/src/style.css), and the [fixture-agent smoke test](../evaluation/2026-08-26-fixture-agent-smoke-test.md) cover typed conversation/action rendering, allowlisted focus and filtering, live status, and narrow/wide layouts. Proposal, revision, delta, replay, and undo rendering remain pending.

## E01-T03 - Deliver responsive and accessible interaction states

| Field | Value |
|---|---|
| Status | Done |
| Priority | P0 |
| Size | M |
| Depends on | E01-T01 |

**User story:** As a desktop or mobile user, I need readable and operable controls so the POC does not depend on one viewport or a mouse.

**Requirements:** URS-NFR-002; PRD-NFR-001.

**Acceptance criteria:**

- [x] Layouts adapt to narrow and wide viewports.
- [x] Quiz answers support keyboard input.
- [x] Reduced-motion preference is respected.
- [x] Core controls use semantic labels and visible focus states.

**Evidence:** [`frontend/src/style.css`](../../frontend/src/style.css), [`frontend/src/main.js`](../../frontend/src/main.js).

## E01-T04 - Display POC trust boundaries

| Field | Value |
|---|---|
| Status | Done |
| Priority | P0 |
| Size | S |
| Depends on | E01-T02 |

**User story:** As a user, I need to know what is synthetic and what the product cannot do so I do not mistake the demo for regulated advice.

**Requirements:** URS-FR-014, URS-NFR-005; PRD-FR-012, PRD-NFR-004.

**Acceptance criteria:**

- [x] Educational-not-advice messaging is visible.
- [x] Synthetic plans and simulated storage behavior are labelled.
- [x] No interface offers purchase, surrender, replacement, or cancellation actions.

**Evidence:** [`frontend/src/main.js`](../../frontend/src/main.js).

## E01-T06 - Render real-product evidence comparison mode

| Field | Value |
|---|---|
| Status | Ready |
| Priority | P1 |
| Size | M |
| Depends on | E01-T03, E06-T09, E10-T09 |

**User story:** As a user, I need selected real products displayed side by side without recommendation signals so I can inspect sourced differences before relying on a ranked result.

**Requirements:** URS-FR-033, URS-NFR-002, URS-NFR-022; PRD-FR-040, PRD-NFR-027, PRD-NFR-028, PRD-NFR-029.

**Acceptance criteria:**

- [ ] Two to four comparison-eligible products from one category render in a dedicated evidence mode on the main comparison surface.
- [ ] Rows use provider then product name ordering and show no rank, score, best-plan badge, or suitability language.
- [ ] Every populated cell exposes its source, evidence span, date/version state, and normalized unit; unresolved values show `Unknown`.
- [ ] The synthetic ranked recommendation remains visually and semantically separate.
- [ ] Adding, removing, sorting, or filtering evidence rows leaves active profile, E07 catalogue, recommendation, and revision references unchanged.
- [ ] Desktop, mobile, keyboard, screen-reader, and reduced-motion checks pass.