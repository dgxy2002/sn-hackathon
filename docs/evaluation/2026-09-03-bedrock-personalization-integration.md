# Bedrock, Personalization, and FA-Profile Integration - 2026-09-03

## Scope

This record accepts the repository integration of Jana's deterministic
personalization work, Deborah's Amazon Bedrock intent, and the implemented
financial-adviser interview feedback. It now includes credentialed local
Bedrock and Docker Compose acceptance. It does not accept real-product ranking,
OpenRouter extraction, AWS deployment, or production suitability.

The integration keeps E07 as the sole author of gaps, eligibility, scores, ordering, assumptions, exclusions, and evidence references. Bedrock receives the immutable recommendation plus compact E03 context and may return explanation prose only.

| Field | Value |
|---|---|
| Original team integration branch | `integration/bedrock-personalization` |
| Completion branch | `feature/complete-poc` |
| Provider interface | Fixture or Amazon Bedrock Runtime Converse API |
| Live provider configuration | `LLM_PROVIDER=bedrock`, `BEDROCK_MODEL_ID`, `AWS_REGION` |
| Extraction provider boundary | OpenRouter remains independently scoped to E04 |
| Credentials used in this acceptance | Local ignored environment only; no secret or certificate committed |

## Integrated behavior

- The coordinator invokes explanation only after deterministic evaluation completes.
- The Bedrock adapter sends the immutable recommendation and compact goal context rather than raw documents.
- Strict response parsing rejects malformed JSON, extra fields, and plan identifiers that are not present in the deterministic eligible-plan result.
- Provider failure produces typed failed run events while preserving the deterministic recommendation for inspection.
- Provider, model or inference-profile ID, prompt version, latency, token counts, and outcome are recorded.
- The frontend renders explanation as escaped text and clears it after a confirmed revision or undo so stale prose cannot accompany a changed recommendation.
- Goal classification recognizes common project and protection intents, including word-based timeframes, and focused questions do not ask no-policy users about nonexistent private cover.
- The simplified frontend uses an optional four-question check with displayed categories weighted 50/25/25, followed by direct no-plan or existing-plan routes.
- The common profile captures only income, liabilities, goal, product preference, and additional-premium ceiling. The existing-plan route adds current premium, death, TPD, and advanced critical-illness amounts.
- Current-policy status supports Yes, No, and Unsure. No-policy fields become not applicable; unsure fields remain unknown and are not deducted from calculated gaps.
- User protection priorities are normalized and applied by the deterministic coverage-fit calculation. Bedrock only explains the resulting immutable order.
- Affordability separates a 5% adviser-interview demo marker from the 15% MoneySense educational upper reference. An absent current premium remains unknown rather than displaying 0%.
- Restarted browser scenarios receive a fresh profile identifier, preventing immutable-version collisions while retaining revision lineage within a scenario.

## Validation

| Check | Observed outcome |
|---|---|
| Backend suite | `49 passed` using the workspace virtual environment |
| Bedrock safety tests | Mocked Converse responses cannot change deterministic ranks or introduce unknown plan IDs |
| Provider failure tests | Recommendation is retained and invocation terminates with typed failure state |
| Frontend production build | Vite 8.2.2 build completed successfully |
| Compose validation | `docker compose config --quiet` completed successfully |
| Editor diagnostics | No backend or frontend source errors reported |
| Repository whitespace check | `git diff --check` completed without findings |
| Credentialed Bedrock invocation | Completed through the Docker/Nginx/API path using Bedrock Converse; one recorded run used 1,529 input and 453 output tokens |
| Corporate TLS path | Frontend and backend images built with an external BuildKit CA secret; boto3 reached Bedrock without disabling verification |
| Compose runtime | PostgreSQL, scraper, backend, and web services reported healthy |
| Browser: current policy | Consent, minimum common profile, four current-plan figures, synthetic extraction review, live explanation, comparison, budget revision, and undo completed |
| Browser: no policy | Repeated post-restart scenario completed without profile-version conflict; private cover was not invented and current affordability stayed unknown |
| Browser: unsure policy | Completed without extraction; no private amount was deducted and the verification warning rendered |
| Browser network/console | Invocation and evidence requests returned HTTP 200; no console errors or warnings were observed |
| Priority sensitivity | Death-first and CI-first profiles produced different deterministic leaders; CI-first ranked the synthetic CI fixture first |
| Simplified route follow-up | No-plan, existing-plan, and optional four-question routes completed against the rebuilt Compose stack; budget confirmation, replay, and undo returned HTTP 200 |

The 49-test result above belongs to the original team-integration acceptance.
The completion pass intentionally used production builds, Python compilation,
direct deterministic probes, API/browser smoke paths, diagnostics, and
`git diff --check` instead of rerunning the complete suite.

## Open gates

- Estimated priced cost is not yet calculated even though token counts are captured.
- OpenRouter E04 extraction remains blocked on the exact model-slug decision.
- AWS deployment, production security, legal/compliance review, and independent review of the draft gap formulation remain open.
- Real-product comparison and ranking gates are unchanged; the implemented E07 ranking remains synthetic and deterministic.
