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
    N[Apply hard constraints and rank eligible plans]
    O[Explain reasons, trade-offs, assumptions, and evidence]
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
    L --> M --> N --> O --> P --> S
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
    class A,B,C,D,E,F,H,L,Q implemented;
    class I,J,O simulated;
    class G,K,M,N,P,R,S,T,U,V,W,X,Y,Z planned;
```

## Current POC status

| Workflow slice | Current behavior |
|---|---|
| Quiz and result | Implemented in the browser |
| Account and profile | Mock account plus in-memory five-step profile |
| Policy upload | File selection works; document content is not processed |
| No-policy path | Navigation can continue, but the explicit API state and tests are pending |
| Extraction review | Synthetic, hard-coded fields and confidence values |
| Gap analysis | Deterministic death and critical-illness calculations |
| Product retrieval | Not implemented; links and product evidence are embedded |
| Ranking | Static synthetic comparison with a budget rationale |
| Adaptation | User can navigate back, but outputs are not versioned or change-explained |
| Conversational summary | Not implemented; there is no contextual Q&A, typed action trace, confirmation proposal, dynamic revision, replay, or undo |

## Workflow invariant

Unknown values remain unknown. The workflow must return an insufficient-data outcome rather than invent policy terms, eligibility, or user circumstances. Presentation actions cannot mutate canonical inputs, and consequential changes cannot reach the summary without confirmation and a deterministic E07 rerun.