# Workflow Diagram

## User and decision workflow

```mermaid
flowchart TD
    A[Open CoverCheck SG]
    B{Choose starting route}
    C[Optional four-question readiness check]
    D[Show three readiness categories and labelled pilot context]
    E[Consent without account creation]
    F[Provide five decision inputs]
    G{Current private plan?}
    H[Add four verified current-plan figures]
    I[Use synthetic sample extraction]
    J[Review fields, confidence, and page evidence]
    K[Build normalized profile with explicit field states]
    L[Calculate protection gaps and affordability]
    M[Retrieve dated product evidence]
    M1[Compare selected real-product evidence without ranking]
    N[Apply hard constraints and rank eligible synthetic plans]
    O[Explain synthetic reasons, trade-offs, and assumptions]
    P[Ask CoverCheck a follow-up or request]
    S{Request type}
    T[Answer with dated evidence]
    U[Focus, sort, filter, or temporarily compare]
    V[Preview old and proposed decision inputs]
    W{User confirms?}
    X[Create input versions and rerun E07]
    Y[Apply and highlight one summary revision]
    Z[Replay or undo revision]
    Q[Continue exploring or verify an authorized representative]

    A --> B
    B -- Check basics first --> C --> D --> B
    B -- No plan or review a plan --> E --> F --> G
    G -- Yes --> H --> I --> J --> K
    G -- No --> R[Mark current-policy fields not applicable] --> K
    G -- Unsure --> R1[Preserve current-policy fields as unknown] --> K
    K --> L
    L --> N --> O --> P --> S
    L --> M --> M1 --> P
    S -- Question --> T --> Q
    S -- Presentation --> U --> Q
    S -- Profile, comparison, or policy change --> V --> W
    W -- Cancel --> Q
    W -- Confirm --> X --> Y --> Z --> Q
    Q -- Ask another request --> P
    Q -- Circumstances changed outside agent --> F

    classDef implemented fill:#e7f4ed,stroke:#246b45,color:#123b28;
    classDef simulated fill:#fff3d6,stroke:#a66500,color:#573900;
    classDef planned fill:#edf1f7,stroke:#53657d,color:#263545,stroke-dasharray: 5 4;
    class A,B,C,D,E,F,G,H,K,L,M,N,O,P,Q,R,R1,S,T,U,V,W,X,Y,Z implemented;
    class I,J,M1 simulated;
```

## Current POC status

| Workflow slice | Current behavior |
|---|---|
| Landing, quiz, and result | Neutral Singapore hero with direct no-plan/existing-plan routes; optional four-question check and result are implemented |
| Consent and profile | No account data; one five-input step for all users and one four-figure current-plan step only when applicable |
| Policy upload | File selection is navigation only; personal document content is not processed |
| No-policy path | The API skips extraction and preserves existing-policy values as not applicable; Unsure remains unknown |
| Extraction review | Synthetic, hard-coded fields and confidence values |
| Gap analysis | Death/TPD target is annual income x 9 plus liabilities; critical-illness target is annual income x 4 |
| Product retrieval | Local PostgreSQL, cached-corpus, synthetic, and optional Supabase adapters expose one E10 evidence contract; fixed retrieval evaluation remains pending |
| Ranking | API-backed deterministic ranking over the labelled synthetic plan catalogue |
| Adaptation | Confirmed budget changes create immutable profile and summary revisions, rerun E07, show deltas, and support replay and undo; other patch types remain pending |
| Conversational summary | The final-page panel and FastAPI service provide typed Q&A, cached evidence, action traces, focus/filter actions, budget proposals, confirmation, cancellation, revisions, replay, and undo |
| Approved next slice | Phase 3B: compare a small comparison-eligible real-product subset with cited fields, neutral ordering, explicit unknowns, and no effect on E07 synthetic ranking |

## Workflow invariant

Unknown values remain unknown. The workflow must return an insufficient-data outcome rather than invent policy terms, eligibility, or user circumstances. Brochure as-of dates, product effective dates, and retrieval dates remain distinct. Phase 3B real-product evidence is read-only and non-ranked. Real products can enter deterministic ranking only through the separately approved Phase 6 gate. Presentation actions cannot mutate canonical inputs, and consequential changes cannot reach the summary without confirmation and a deterministic E07 rerun.