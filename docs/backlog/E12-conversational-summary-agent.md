# E12 Backlog - Conversational Summary Agent

**Epic:** [E12 - Conversational Summary Agent](../epics/E12-conversational-summary-agent.md)
**Owner:** Tim

## E12-T01 - Freeze the conversation and revision experience

| Field | Value |
|---|---|
| Status | In progress |
| Priority | P1 |
| Size | M |
| Depends on | E07-T03, E10-T02 |

**User story:** As the feature team, we need one accepted interaction and data contract so visible agent actions cannot bypass capability ownership or trust boundaries.

**Requirements:** URS-FR-027, URS-FR-029, URS-FR-030, URS-FR-031, URS-FR-032, URS-NFR-018, URS-NFR-019; PRD-FR-032, PRD-FR-033, PRD-FR-035, PRD-FR-036, PRD-FR-037, PRD-FR-038, PRD-NFR-023, PRD-NFR-024, PRD-NFR-025.

**Acceptance criteria:**

- [ ] Schemas define conversation, message, intent, tool plan, action event, proposal, confirmation, summary revision, delta, and undo lineage.
- [ ] Read, presentation, decision-input, extraction-field, and deterministic-result actions have explicit confirmation and ownership rules.
- [x] Supported summary regions and typed tool targets are allowlisted.

**Current evidence:** [`backend/app/contracts.py`](../../backend/app/contracts.py), [`backend/app/conversations.py`](../../backend/app/conversations.py), and the frontend action map in [`frontend/src/main.js`](../../frontend/src/main.js). Proposal, confirmation, revision, delta, undo, and cross-owner acceptance remain pending.
- [ ] Idle, planning, acting, waiting-for-confirmation, completed, unsupported, cancelled, and failed states are defined.
- [ ] E03, E04, E06, E07, E10, and E11 owners accept their contract boundaries.

## E12-T02 - Integrate the final-page agent and action trace

| Field | Value |
|---|---|
| Status | In progress |
| Priority | P1 |
| Size | L |
| Depends on | E01-T05, E12-T01 |

**User story:** As a user on the final summary, I need a conversational panel and visible agent activity so I can ask for help and understand what changes the page.

**Requirements:** URS-FR-027, URS-FR-029, URS-FR-031, URS-NFR-002, URS-NFR-021; PRD-FR-032, PRD-FR-035, PRD-NFR-027.

**Acceptance criteria:**

- [x] The summary page includes `Ask CoverCheck`, suggested prompts, message history, composer, stop action, and current agent state.
- [x] Expandable action items show tool, target, status, evidence count, and affected summary region without exposing hidden model reasoning.
- [x] The page visibly focuses, expands, sorts, filters, or adds temporary comparison content as presentation actions complete.
- [x] New and changed regions have stable layout, visible focus, reduced-motion behavior, and screen-reader announcements.
- [ ] Loading, confirmation, unsupported, failure, completed, replay, and undo controls are keyboard operable.

**Current evidence:** [`frontend/src/api.js`](../../frontend/src/api.js), [`frontend/src/main.js`](../../frontend/src/main.js), [`frontend/src/style.css`](../../frontend/src/style.css), and the [fixture-agent smoke test](../evaluation/2026-08-26-fixture-agent-smoke-test.md). Confirmation, replay, and undo controls remain pending.

## E12-T03 - Integrate contextual answers and plan exploration

| Field | Value |
|---|---|
| Status | Ready |
| Priority | P1 |
| Size | L |
| Depends on | E06-T08, E10-T04, E12-T02 |

**User story:** As a curious user, I need to ask why a result appeared and explore the cached real-product catalogue without losing evidence state or mistaking exploration for a recommendation.

**Requirements:** URS-FR-027, URS-FR-028, URS-FR-029, URS-NFR-004, URS-NFR-019; PRD-FR-032, PRD-FR-033, PRD-FR-034, PRD-FR-035, PRD-NFR-003, PRD-NFR-015, PRD-NFR-022.

**Acceptance criteria:**

- [ ] Follow-up questions retain the active profile, recommendation, evidence, and prior-turn context within the session cap.
- [x] Search is restricted to E06 cached catalogue records and returns approval, unverified, stale, unknown, and no-evidence states explicitly.
- [ ] Alternative plans retain eligibility, evidence spans, source, document as-of date, product effective date, retrieval date, freshness, and synthetic labels.
- [x] Real-product alternatives remain read-only and can be explored without entering or changing E07 synthetic ranking.
- [x] Every factual answer links to evidence or is visibly labelled synthetic, unknown, or unsupported.

**Current evidence:** [`backend/app/evidence.py`](../../backend/app/evidence.py), [`backend/app/conversations.py`](../../backend/app/conversations.py), [`frontend/src/main.js`](../../frontend/src/main.js), and the [cached evidence browser smoke test](../evaluation/2026-08-28-cached-evidence-browser-smoke-test.md). Structured affordability and eligibility filters, temporary comparison columns, Supabase browser parity, and consequential revision paths remain pending.

**Delivery order:** Read-only questions and catalogue exploration call the typed E10/E06 evidence service directly. E11 remains required for the consequential proposal, confirmation, deterministic-rerun, revision, replay, and undo path in E12-T04 and E12-T05.

## E12-T04 - Integrate proposals, confirmation, and dynamic revisions

| Field | Value |
|---|---|
| Status | Ready |
| Priority | P1 |
| Size | L |
| Depends on | E03-T07, E04-T06, E07-T07, E10-T08, E11-T08, E12-T02 |

**User story:** As a user, I need requested input changes previewed and confirmed before the agent recalculates and rewrites my summary.

**Requirements:** URS-FR-030, URS-FR-031, URS-NFR-010, URS-NFR-011, URS-NFR-019; PRD-FR-033, PRD-FR-036, PRD-FR-037, PRD-NFR-010, PRD-NFR-023, PRD-NFR-025.

**Acceptance criteria:**

- [ ] Profile, canonical comparison, and extracted-field proposals identify old, proposed, unknown, and unchanged values.
- [ ] The user can confirm or cancel before any canonical input version changes.
- [ ] Confirmation creates versioned inputs and invokes E07 rather than accepting model-authored calculations or rankings.
- [ ] The page updates all affected summary regions from one validated revision and highlights before/after deltas.
- [ ] Stale proposals, conflicts, validation failures, and interrupted runs cannot partially update the canonical summary.

## E12-T05 - Add replay, undo, and feature evaluation

| Field | Value |
|---|---|
| Status | Ready |
| Priority | P1 |
| Size | M |
| Depends on | E08-T09, E12-T03, E12-T04 |

**User story:** As a user and reviewer, I need to undo changes and replay actions so dynamic behavior remains understandable and testable.

**Requirements:** URS-FR-031, URS-FR-032, URS-NFR-007, URS-NFR-013, URS-NFR-020, URS-NFR-021; PRD-FR-038, PRD-NFR-005, PRD-NFR-013, PRD-NFR-016, PRD-NFR-026, PRD-NFR-027.

**Acceptance criteria:**

- [ ] Applied summary revisions expose a clear undo action and revision lineage.
- [ ] Undo restores or deterministically recalculates the prior coherent profile, extraction, recommendation, and summary state.
- [ ] A replay view shows ordered intents, tools, evidence, confirmations, reruns, revisions, metrics, and terminal outcome.
- [ ] Predeclared scenarios cover Q&A, plan exploration, presentation change, confirmed and cancelled changes, extraction correction, undo, stale evidence, invalid action, dependency failure, and loop cap.
- [ ] Conversation and revision state is removed with the POC session unless retained as a named synthetic fixture.

## E12-T06 - Select real products for evidence comparison

| Field | Value |
|---|---|
| Status | Ready |
| Priority | P1 |
| Size | M |
| Depends on | E01-T06, E06-T09, E10-T09, E12-T02 |

**User story:** As a user exploring the catalogue, I need the agent to add or remove eligible real products from a factual comparison without implying that it has recommended them.

**Requirements:** URS-FR-028, URS-FR-029, URS-FR-033, URS-NFR-018, URS-NFR-019, URS-NFR-022; PRD-FR-033 to PRD-FR-035, PRD-FR-040, PRD-NFR-023, PRD-NFR-028, PRD-NFR-029.

**Acceptance criteria:**

- [ ] The agent may select, add, remove, sort, or filter only comparison-eligible products through registered presentation tools.
- [ ] Mixed-category, stale, conflicting, unsupported, or non-comparison-eligible selections fail visibly.
- [ ] The action trace labels evidence comparison as non-ranked and shows selected product IDs, gate state, evidence count, and affected region.
- [ ] Retrieval relevance cannot become table order, fit score, recommendation language, or canonical comparison membership.
- [ ] No confirmation is required because the action is presentation-only, but active profile, catalogue, recommendation, and revision references remain unchanged.
- [ ] Fixture and configured evidence adapters return the same action and comparison contracts.