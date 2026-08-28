# Workflow Diagram

## User and decision workflow

```mermaid
flowchart TD
    A[Open CoverCheck SG]
    B[Complete five-question readiness quiz]
    C[Calculate deterministic readiness score]
    D[Show known gaps and labelled pilot benchmark]
    E[Create mock account and consent]
    F[Complete five-step profile]
    G{Have a policy document?}
    H[Select PDF, image, or synthetic sample]
    I[Extract fields with confidence and page evidence]
    J[Review and correct unresolved fields]
    K[Build normalized user and policy profile]
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

    A --> B --> C --> D --> E --> F --> G
    G -- Yes --> H --> I --> J --> K
    G -- No or skip --> R[Mark current-policy fields unknown] --> K
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
    class A,B,C,D,E,F,G,H,K,L,M,N,P,Q,R,S,T,U,V,W,X,Y,Z implemented;
    class I,J,O,M1 simulated;
```

## Current POC status

| Workflow slice | Current behavior |
|---|---|
| Quiz and result | Implemented in the browser |
| Account and profile | Mock account plus versioned, disposable five-step profile through the API |
| Policy upload | File selection works; document content is not processed |
| No-policy path | The API skips extraction and preserves existing-policy values as unknown |
| Extraction review | Synthetic, hard-coded fields and confidence values |
| Gap analysis | Deterministic death and critical-illness calculations |
| Product retrieval | Local PostgreSQL, cached-corpus, synthetic, and optional Supabase adapters expose one E10 evidence contract; fixed retrieval evaluation remains pending |
| Ranking | API-backed deterministic ranking over the labelled synthetic plan catalogue |
| Adaptation | Confirmed budget changes create immutable profile and summary revisions, rerun E07, show deltas, and support replay and undo; other patch types remain pending |
| Conversational summary | The final-page panel and FastAPI service provide typed Q&A, cached evidence, action traces, focus/filter actions, budget proposals, confirmation, cancellation, revisions, replay, and undo |
| Approved next slice | Phase 3B: compare a small comparison-eligible real-product subset with cited fields, neutral ordering, explicit unknowns, and no effect on E07 synthetic ranking |

## Workflow invariant

Unknown values remain unknown. The workflow must return an insufficient-data outcome rather than invent policy terms, eligibility, or user circumstances. Brochure as-of dates, product effective dates, and retrieval dates remain distinct. Phase 3B real-product evidence is read-only and non-ranked. Real products can enter deterministic ranking only through the separately approved Phase 6 gate. Presentation actions cannot mutate canonical inputs, and consequential changes cannot reach the summary without confirmation and a deterministic E07 rerun.