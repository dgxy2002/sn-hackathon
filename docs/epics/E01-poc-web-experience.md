# E01 - POC Web Experience

| Field | Value |
|---|---|
| Primary owner | Tim |
| Priority | P0 |
| Status | In progress |
| Outcome | A target user can complete the CoverCheck SG POC journey and inspect validated conversational actions and dynamic summary revisions in a responsive web interface. |

## Scope

- Vite application shell and visual system.
- Landing page, quiz, result, mock sign-up, onboarding, upload, extraction review, and comparison views.
- Back navigation, form handling, keyboard quiz controls, and reduced-motion support.
- Clear educational-not-advice and synthetic-data messaging.
- Typed final-page conversation, action, confirmation, delta, replay, and undo rendering without model-authored markup.
- Read-only rendering of real-product evidence with source, date type, approval/evidence state, and a visible boundary from synthetic recommendations.
- A dedicated, neutrally ordered real-product evidence-comparison mode for two to four comparison-eligible products.

## Requirements traceability

- **URS:** [URS-FR-001, URS-FR-004, URS-FR-013, URS-FR-014, URS-FR-029, URS-FR-031, URS-NFR-002, URS-NFR-006, URS-NFR-021](../urs/URS.md)
- **PRD:** [PRD-FR-001, PRD-FR-004, PRD-FR-012, PRD-FR-032, PRD-FR-035, PRD-FR-037, PRD-NFR-001, PRD-NFR-006, PRD-NFR-027](../prd/PRD.md)
- **Backlog:** [E01 tickets](../backlog/E01-poc-web-experience.md)
- **Phase 3B:** URS-FR-033, URS-NFR-022; PRD-FR-040, PRD-NFR-028, PRD-NFR-029.

## Repository evidence

- [`frontend/src/main.js`](../../frontend/src/main.js) contains the view state machine and interactions.
- [`frontend/src/style.css`](../../frontend/src/style.css) contains the responsive visual system.
- [`frontend/index.html`](../../frontend/index.html) provides the application entry document.
- [`frontend/package.json`](../../frontend/package.json) provides working Vite development and build scripts.

## Definition of done

- [x] The journey renders from landing through comparison without a backend.
- [x] Quiz, forms, navigation, and synthetic upload actions are interactive.
- [x] The interface adapts to desktop and mobile layouts.
- [x] Synthetic recommendations and the educational boundary are visible.
- [x] `npm --prefix frontend run build` completes successfully.
- [x] The final page renders typed agent progress, proposals, confirmations, changed regions, replay, and undo without executing model-authored markup or selectors.
- [x] Read-only RAG results render across applicable views with citations, distinct date fields, evidence state, and no visual implication that an explored real product is recommended.
- [ ] Phase 3B evidence mode compares two to four eligible real products with neutral ordering, cited cells, explicit unknowns, and no recommendation signals or canonical-state changes.
- [x] Dynamic summary states remain responsive, keyboard operable, visibly focused, and compatible with reduced motion.

**Acceptance evidence:** [Integrated runtime and browser acceptance](../evaluation/2026-08-28-integrated-runtime-browser-acceptance.md). The neutral browser surface currently proves the contract with explicitly labelled synthetic fixtures; no real product has passed the Phase 3B gate.

## POC boundary

Authentication, durable state, agent interpretation, and tool execution are not owned by this epic. E01 renders only validated E10/E12 contracts; production browser support remains deferred.