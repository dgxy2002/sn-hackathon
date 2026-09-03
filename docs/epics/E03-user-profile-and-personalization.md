# E03 - User Profile and Personalization

| Field | Value |
|---|---|
| Primary owner | Jana |
| Priority | P1 |
| Status | In progress |
| Outcome | The POC gathers and versions enough explicit user context through the backend API to explain which protection gaps and plan attributes matter, even when the user has no policy document. |

## Scope

- Collect the five common decision inputs used by the current formulation: income, liabilities, goal, product preference, and additional-premium ceiling.
- For an existing plan, add only current premium, death, TPD, and advanced critical-illness benefits.
- Preserve unknown values instead of treating them as no coverage.
- Ask targeted follow-up questions when a decision-critical field is missing.
- Recalculate outputs after a confirmed supported change; the working conversational mutation is monthly budget.
- Represent conversational profile changes as versioned proposals that require confirmation before activation.
- Expose profile create, read, and version behavior through the E10 API contract.
- Represent policy state as Yes, No, or Unsure; No makes private-policy amounts not applicable, while Unsure preserves unknowns.
- Keep profile normalization deterministic and independent of an LLM.
- Run inside the local backend container and remain portable to the same image on ECS Fargate.

## Requirements traceability

- **URS:** [URS-FR-004, URS-FR-005, URS-FR-006, URS-FR-012, URS-FR-015, URS-FR-017, URS-FR-023, URS-FR-024, URS-FR-030, URS-FR-031, URS-NFR-011, URS-NFR-013, URS-NFR-015, URS-NFR-019](../urs/URS.md)
- **PRD:** [PRD-FR-004, PRD-FR-005, PRD-FR-011, PRD-FR-015, PRD-FR-028, PRD-FR-033, PRD-FR-036, PRD-FR-037, PRD-NFR-008, PRD-NFR-013, PRD-NFR-015, PRD-NFR-023, PRD-NFR-025](../prd/PRD.md)
- **Backlog:** [E03 tickets](../backlog/E03-user-profile-and-personalization.md)

## Repository evidence

- [`frontend/src/main.js`](../../frontend/src/main.js) contains one common minimum-input step, one existing-plan-only cover step, and an in-memory `state.profile`.
- [`backend/app/personalization.py`](../../backend/app/personalization.py) classifies goal context deterministically, builds compact versioned explanation context, and selects focused questions without asking no-policy users for nonexistent private cover.
- [`backend/tests/test_personalization.py`](../../backend/tests/test_personalization.py) covers project goal wording, word-based timeframes, context output, and the no-policy question path.
- [`docs/PLAN.md`](../PLAN.md) defines the fuller Financial Needs Analysis-inspired profile and shared user-profile contract.

## Definition of done

- [x] A versioned profile contract identifies value, source, and unknown status for decision-critical fields.
- [x] The UI collects the minimum POC profile through a multi-step form.
- [x] Every required UI field changes the current calculation, a hard constraint, deterministic priority weighting, or explanation.
- [x] Missing decision-critical fields trigger a focused question or an insufficient-data result.
- [x] The profile API distinguishes present, unknown, not-applicable, and explicitly no-current-policy states.
- [x] A user can skip policy upload and reach analysis without fabricated coverage values.
- [x] A confirmed budget change reruns the analysis and identifies the changed input and ranking effect.
- [ ] Goal, dependant, preference, declared-cover, and extraction-field proposals are supported with the same confirmation boundary.
- [x] A conversational profile patch shows old and proposed values, rejects stale versions, requires confirmation, and creates an immutable active version.
- [x] The profile contract passes through the local backend container and uses the same contract intended for ECS.
- [x] Current-policy, no-policy, and unsure-policy synthetic profiles follow distinct browser paths.

**Acceptance evidence:** [Integrated runtime and browser acceptance](../evaluation/2026-08-28-integrated-runtime-browser-acceptance.md), [Bedrock and personalization integration](../evaluation/2026-09-03-bedrock-personalization-integration.md), and [Gen-Z journey review](../evaluation/2026-09-03-gen-z-journey-and-project-truth.md). Confirmed conversational mutation is currently limited to monthly budget; broader patch types remain open.

## POC boundary

Detailed diagnoses, NRIC, payment data, beneficiary identities, episodic memory, and production profile persistence are excluded. A broad Financial Needs Analysis questionnaire is deferred; no field should return to the POC unless its decision effect is documented.