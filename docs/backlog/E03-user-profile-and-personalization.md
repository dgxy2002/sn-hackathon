# E03 Backlog - User Profile and Personalization

**Epic:** [E03 - User Profile and Personalization](../epics/E03-user-profile-and-personalization.md)
**Owner:** Jana

## E03-T01 - Implement minimum structured onboarding

| Field | Value |
|---|---|
| Status | Done |
| Priority | P0 |
| Size | M |
| Depends on | E01-T02 |

**User story:** As a user, I need a manageable questionnaire so the POC can understand my situation without asking for unnecessary sensitive data.

**Requirements:** URS-FR-004, URS-FR-005; PRD-FR-004.

**Acceptance criteria:**

- [x] The flow collects life stage, cash flow, dependants, debt, existing cover, goals, budget, and preference.
- [x] Account and consent precede profile collection.
- [x] Detailed diagnoses, NRIC, payment data, and beneficiary identities are not requested.

**Evidence:** `onboardingSteps`, `onboardingFields`, and `onboardingView` in [`frontend/src/main.js`](../../frontend/src/main.js).

## E03-T02 - Freeze the versioned profile contract

| Field | Value |
|---|---|
| Status | In progress |
| Priority | P1 |
| Size | M |
| Depends on | E03-T01 |

**User story:** As an integrating system, I need a versioned profile with field provenance and unknown states so downstream components interpret user information consistently.

**Requirements:** URS-FR-005, URS-FR-006, URS-FR-017, URS-NFR-003, URS-NFR-011, URS-NFR-013; PRD-FR-005, PRD-FR-015, PRD-NFR-008, PRD-NFR-013.

**Acceptance criteria:**

- [x] A schema defines profile version, as-of date, consent, field values, provenance, and unknown state.
- [x] Representative complete and incomplete fixtures validate against the schema.
- [x] Absence and zero are represented differently.
- [ ] E07 and E08 owners approve the contract.

## E03-T03 - Ask focused missing-field questions

| Field | Value |
|---|---|
| Status | Done |
| Priority | P1 |
| Size | M |
| Depends on | E03-T02 |

**User story:** As a user with incomplete information, I need the system to ask only decision-relevant follow-ups or decline to rank so it does not invent my circumstances.

**Requirements:** URS-FR-006, URS-FR-015; PRD-FR-005, PRD-FR-009.

**Acceptance criteria:**

- [x] Decision-critical fields are declared by the decision ruleset.
- [x] Missing critical values produce targeted questions.
- [x] Unknown policy terms remain unknown after follow-up.
- [x] The flow can return an insufficient-data state.

## E03-T04 - Re-run and explain material profile changes

| Field | Value |
|---|---|
| Status | In progress |
| Priority | P1 |
| Size | M |
| Depends on | E03-T02, E07-T02, E08-T02 |

**User story:** As a returning user, I need changed goals or circumstances to update the result with an explanation so personalization is visible and trustworthy.

**Requirements:** URS-FR-012, URS-FR-017, URS-NFR-013; PRD-FR-011, PRD-FR-015, PRD-NFR-013.

**Acceptance criteria:**

- [ ] Goal, budget, dependant, and policy changes create a new profile version.
- [x] Material changes rerun gap and plan analysis.
- [x] The output identifies changed inputs and their effect.
- [ ] At least three synthetic change scenarios pass.

## E03-T05 - Complete Financial Needs Analysis profile coverage

| Field | Value |
|---|---|
| Status | In progress |
| Priority | P1 |
| Size | M |
| Depends on | E03-T02 |

**User story:** As a first-time working adult, I need the profile to cover the circumstances that materially affect protection needs and affordability without collecting unnecessary sensitive data.

**Requirements:** URS-FR-005, URS-FR-006, URS-NFR-001, URS-NFR-005; PRD-FR-004, PRD-FR-005, PRD-FR-015, PRD-NFR-004, PRD-NFR-009.

**Acceptance criteria:**

- [ ] The profile covers life stage, employment changes, goals, target amounts and dates, income, expenses, savings, assets, liabilities, dependants, support duration, government cover, employer cover, private policies, health-care preferences, product preferences, and sustainable premium budget.
- [ ] Investment-risk and knowledge questions appear only when investment-linked products are in scope.
- [ ] Government coverage distinguishes MediShield Life, Integrated Shield Plans, CareShield Life, DPS, and HPS where relevant.
- [ ] Detailed diagnoses, NRIC, payment data, and beneficiary identities remain excluded from the POC.
- [ ] Each field documents why it affects a calculation, constraint, or explanation.

## E03-T06 - Implement the no-policy profile API path

| Field | Value |
|---|---|
| Status | Ready |
| Priority | P0 |
| Size | M |
| Depends on | E03-T02, E10-T04 |

**User story:** As a user without an existing policy document, I need to skip upload and continue with an honest unknown-coverage state.

**Requirements:** URS-FR-006, URS-FR-015, URS-FR-023, URS-FR-024, URS-NFR-011, URS-NFR-015; PRD-FR-015, PRD-FR-028, PRD-NFR-008, PRD-NFR-015.

**Acceptance criteria:**

- [x] The profile contract represents `has_current_policy: false` separately from missing or unknown policy details.
- [x] The coordinator bypasses extraction when no policy is supplied.
- [x] Existing-policy values remain unknown and no synthetic coverage is added.
- [x] Gap and recommendation services return assumptions, focused questions, or insufficient data as defined by the formulation.
- [ ] API tests cover policy supplied, no policy, unknown policy status, and changed policy status through the local backend container.

## E03-T07 - Support confirmed versioned profile patches

| Field | Value |
|---|---|
| Status | In progress |
| Priority | P1 |
| Size | M |
| Depends on | E03-T02, E10-T08 |

**User story:** As a user, I need conversational profile changes represented as reviewable patches so the agent cannot silently alter decision inputs.

**Requirements:** URS-FR-030, URS-FR-031, URS-NFR-011, URS-NFR-019; PRD-FR-033, PRD-FR-036, PRD-FR-037, PRD-NFR-023, PRD-NFR-025.

**Acceptance criteria:**

- [x] A profile patch contains the base version, changed fields, old values, proposed values, reason, and affected calculations.
- [ ] Budget, goal, dependant, preference, declared-coverage, and other decision-input changes require confirmation.
- [x] Validation preserves explicit unknown values and rejects stale, disallowed, or conflicting patches.
- [x] Confirmation creates a new immutable profile version; cancellation leaves the active version unchanged.
- [x] Applied and rejected proposals retain typed audit events without hidden model reasoning.

**Current evidence:** The [integrated runtime and browser acceptance](../evaluation/2026-08-28-integrated-runtime-browser-acceptance.md) verifies the no-policy path and confirmed/cancelled budget patches. Goal, dependant, preference, and declared-coverage proposal generation remain open.