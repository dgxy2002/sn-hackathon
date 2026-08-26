# E12 - Conversational Summary Agent

| Field | Value |
|---|---|
| Primary owner | Tim |
| Priority | P1 |
| Status | Planned |
| Outcome | Users can ask grounded follow-up questions and visibly reshape the final comparison through safe agent actions, confirmed input changes, deterministic reruns, and reversible summary revisions. |

## Scope

- Add an `Ask CoverCheck` conversational panel to the final summary page with suggested prompts and current-session context.
- Answer questions about the active profile, gaps, ranking, assumptions, evidence, and approved plan alternatives.
- Show a live, expandable action timeline while the agent searches, focuses sections, filters comparisons, proposes changes, reruns analysis, and updates the page.
- Let presentation-only actions navigate, focus, sort, filter, and temporarily reshape the comparison immediately.
- Let users request changes to profile inputs, comparison membership, and extracted policy fields.
- Preview old and proposed values and require explicit confirmation before changing decision inputs or reviewed extraction fields.
- Apply confirmed changes through E03/E04 contracts, rerun E07 deterministically, and render only the validated recommendation and delta contracts.
- Highlight changed summary regions and provide current-session revision history, replay, and undo.
- Use only the approved E06 catalogue; preserve citations, dates, freshness, and synthetic labels.
- Execute allowlisted typed application tools through E10/E11 rather than model-authored HTML, JavaScript, selectors, coordinates, SQL, or arbitrary web navigation.

## Requirements traceability

- **URS:** [URS-FR-027, URS-FR-028, URS-FR-029, URS-FR-030, URS-FR-031, URS-FR-032, URS-NFR-002, URS-NFR-003, URS-NFR-004, URS-NFR-007, URS-NFR-010, URS-NFR-011, URS-NFR-013, URS-NFR-018, URS-NFR-019, URS-NFR-020, URS-NFR-021](../urs/URS.md)
- **PRD:** [PRD-FR-032, PRD-FR-033, PRD-FR-034, PRD-FR-035, PRD-FR-036, PRD-FR-037, PRD-FR-038, PRD-NFR-003, PRD-NFR-005, PRD-NFR-010, PRD-NFR-013, PRD-NFR-014, PRD-NFR-015, PRD-NFR-016, PRD-NFR-017, PRD-NFR-022, PRD-NFR-023, PRD-NFR-024, PRD-NFR-025, PRD-NFR-026, PRD-NFR-027](../prd/PRD.md)
- **Backlog:** [E12 tickets](../backlog/E12-conversational-summary-agent.md)

## Agent action boundary

| Action class | Examples | Confirmation |
|---|---|---|
| Read | Explain rank, compare evidence, answer a follow-up | No |
| Presentation | Focus a section, expand evidence, sort, filter, add a temporary comparison column | No |
| Decision input | Change budget, goal, dependant, preference, declared coverage, or canonical comparison membership | Required |
| Extracted policy | Correct a reviewed premium, benefit, term, rider, or exclusion | Required with field provenance |
| Deterministic result | Recalculate gaps, eligibility, fit, ranking, and summary | Performed only after any required confirmation; model cannot author values |

## Definition of done

- [ ] The final summary includes an accessible `Ask CoverCheck` panel with suggested prompts, follow-up context, and visible trust boundaries.
- [ ] The agent answers current-summary questions and explores additional approved plans with dated citations and freshness status.
- [ ] An expandable action trace shows planning, tools, affected page regions, confirmations, deterministic reruns, completion, and failures.
- [ ] Presentation-only actions visibly focus or reshape the page without changing canonical decision versions.
- [ ] Profile, canonical comparison, and extracted-policy changes show a before/after proposal and cannot apply without confirmation.
- [ ] Confirmed changes produce versioned inputs, a deterministic E07 rerun, one coherent summary revision, highlighted deltas, and undo.
- [ ] Model output cannot execute arbitrary code, selectors, coordinates, SQL, unregistered tools, or unapproved-source searches.
- [ ] Conversation, action, evidence, confirmation, revision, model, prompt, tool, formulation, and ruleset versions are replayable within the POC session.
- [ ] Normal Q&A, approved-plan exploration, presentation change, profile change, extraction correction, cancellation, undo, stale evidence, no evidence, invalid action, and dependency failure scenarios pass.
- [ ] The complete flow works in Docker Compose fixture mode and with configured OpenRouter mode using the same contracts.

## POC boundary

The agent operates only within CoverCheck's typed application capabilities and approved catalogue. It cannot browse arbitrary websites, transact, contact advisers, purchase, replace, surrender, or recommend cancelling insurance. Conversation and revision history is disposable with the current synthetic POC session unless retained as a named evaluation fixture.