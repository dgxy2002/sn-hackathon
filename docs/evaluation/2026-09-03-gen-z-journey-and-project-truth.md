# Gen-Z Journey and Project-Truth Review - 2026-09-03

## Purpose

This record documents the focused simplification of the CoverCheck SG browser
journey and reconciles the project DOD with behavior observed in the current
repository. It does not approve real-product comparison, real-product ranking,
public customer use, or the draft insurance formulation.

## Gen-Z perspective

### What already worked

- The final comparison exposes formulas, assumptions, exclusions, evidence
  state, affordability, and a safe adviser-verification link.
- Synthetic ranking and cached real-product evidence remain visibly separate.
- The conversational budget change has a clear proposal, confirmation,
  deterministic rerun, replay, and undo boundary.
- The visual direction feels specific to Singapore rather than like a generic
  financial dashboard.

### What created friction or mistrust

- The earlier funnel made a readiness quiz and mock account feel mandatory
  before the user could answer the question they arrived with.
- The expanded adviser-style profile asked for many facts that the current
  calculation did not use.
- Prefilled profile values risked looking like facts the user had supplied.
- Parent-focused wording assumed every young adult inherited a plan and sounded
  unnatural for users who had no private cover.
- Ranking labels could be misread as real-product advice unless the synthetic
  boundary was repeated beside the result.

### Changes made

- Added a neutral daylight Singapore skyline hero with two primary routes:
  **I do not have a plan** and **Review a plan I have**.
- Kept readiness as an optional four-question check rather than a gate.
- Removed mock name and email collection; retained explicit consent.
- Removed fake defaults and broad profile questions not used by the current
  formulation.
- Reduced the common route to five decision inputs: monthly take-home income,
  total liabilities, goal, protection-versus-savings preference, and maximum
  additional monthly premium.
- Preset no-plan policy status and skipped policy/extraction questions. Existing
  private-policy amounts are `not_applicable`; Unsure remains `unknown`.
- Limited the existing-plan addition to four verified figures: current premium,
  death benefit, TPD benefit, and advanced critical-illness benefit.
- Clarified that personal-file contents are not processed and that the review
  uses a synthetic sample policy.
- Repeated **closest demo fit** and **synthetic plan data** language around the
  deterministic comparison.

## Verified acceptance

| Check | Observed outcome |
|---|---|
| Frontend production build | Vite 8.2.2 production build completed successfully in the web image |
| Compose runtime | Web, backend, singleton scraper, and PostgreSQL/pgvector reported healthy |
| Desktop hero | 1440 x 900 inspection showed both direct routes, optional check, image credit, and no horizontal overflow |
| Mobile hero | 502 x 846 inspection showed both routes and optional check with document width equal to viewport width |
| No-plan route | Consent -> five inputs -> deterministic comparison completed; extraction was skipped and private-policy fields were `not_applicable` |
| Existing-plan route | Consent -> five inputs -> four current-plan figures -> synthetic extraction review -> comparison completed |
| Optional readiness route | Four questions -> three-category result -> either protection route completed |
| Deterministic gaps | For S$4,500 monthly income and zero liabilities, death/TPD were S$486,000 and CI was S$216,000 |
| Live explanation | Bedrock explanation rendered after the immutable deterministic result |
| Conversation | Budget S$150 -> S$100 produced a confirmation proposal and coherent revision; replay returned six ordered events; undo restored S$150 |
| Browser health | Integrated API requests returned HTTP 200/201 and the accepted route produced no console warning or error |
| Input validity | Normal whole-dollar values such as S$4,500 income and S$120 budget passed browser validation |
| Critical fields | Unknown monthly expenses did not block ranking; unknown liabilities returned the focused outstanding-loans question |
| Goal priorities | Family-first and income-first profiles produced different deterministic fit scores while retaining reproducible ordering in the checked fixture |
| Editor diagnostics | No diagnostics were reported in the changed frontend, decision-support, or personalization files |

The complete automated suite was not rerun during this focused pass. The prior
49-test result remains historical evidence in the Bedrock integration record;
this pass used production builds, the live containerized routes, focused runtime
checks, and editor diagnostics.

## Deterministic decision boundary

The current draft formulation uses:

- death target = annual income x 9 + liabilities;
- TPD target = annual income x 9 + liabilities;
- critical-illness target = annual income x 4.

Liabilities are therefore decision critical. Monthly expenses are not critical
because the current formulas and hard constraints do not consume them. The
independent formulation review and 20-profile correctness evaluation remain
open; these formulas are transparent POC references, not personal advice.

Bedrock receives the immutable recommendation and compact context only. It may
produce plain-language explanation but cannot write gaps, exclusions,
eligibility, scores, order, evidence IDs, or revision values.

## Project truth

### 1. Working synthetic judged POC

- Direct no-plan and existing-plan browser routes.
- Optional four-question readiness check with labelled pilot context.
- Explicit consent and field-state semantics.
- Deterministic gaps, hard constraints, fit scores, and ranking over four
  labelled synthetic plans.
- Credentialed Bedrock explanation of the immutable result.
- Typed conversation, budget proposal/confirmation, rerun, replay, and undo.
- Four-service local Compose topology.

### 2. Neutral cached real evidence

- 79 cached brochure documents normalize to 71 deduplicated product records.
- Records may be searched and discussed with source/date/evidence state.
- Real records cannot change the synthetic catalogue, gaps, eligibility,
  scores, order, or summary revision.

### 3. Gated real-product comparison and ranking

- No real-product subset has passed the Phase 3B comparison gate.
- Real-product ranking remains disabled behind the later Phase 6 data,
  formulation, evaluation, DEC-004, and compliance gates.
- A successful evidence search does not imply comparison or ranking eligibility.

### 4. Deferred production controls

- Production identity, customer-document processing and retention, legal and
  compliance approval, public-source permissions, AWS deployment, priced-cost
  reporting, full monitoring, resilience, incident response, and security
  hardening remain open.
- OpenRouter extraction remains blocked on its exact model-slug decision.

## DOD conclusion and next improvements

The repository does not need a ground-up rewrite. The deterministic backend,
typed contracts, Bedrock boundary, and Compose topology are useful foundations;
the earlier problem was the breadth and order of the browser funnel.

Highest-value remaining work:

1. Obtain independent approval of the draft formulation and run the predeclared
   20-profile correctness evaluation.
2. Rehearse and record the five-minute judged path using the shorter funnel.
3. Add priced Bedrock cost reporting and finish the declared failure/loop-cap
   matrix.
4. Implement broader conversational mutations only when a judged scenario needs
   them; do not restore broad questionnaire fields by default.
5. Keep Phase 3B and Phase 6 closed until their evidence and compliance gates
   are explicitly accepted.

## Visual evidence and attribution

- [Desktop hero](artifacts/genz-hero-wide.png)
- [Mobile hero](artifacts/genz-hero-mobile.png)

Hero image: Dietmar Rabich, Wikimedia Commons, CC BY-SA 4.0,
`Singapore (SG), Marina Bay -- 2019 -- 4439-48.jpg`.
