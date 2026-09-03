# Bedrock and Personalization Integration - 2026-09-03

## Scope

This record accepts the repository integration of Jana's deterministic personalization work and Deborah's Amazon Bedrock intent. It does not accept a credentialed live Bedrock invocation, real-product ranking, OpenRouter extraction, or AWS deployment.

The integration keeps E07 as the sole author of gaps, eligibility, scores, ordering, assumptions, exclusions, and evidence references. Bedrock receives the immutable recommendation plus compact E03 context and may return explanation prose only.

| Field | Value |
|---|---|
| Integration branch | `integration/bedrock-personalization` |
| Provider interface | Fixture or Amazon Bedrock Runtime Converse API |
| Live provider configuration | `LLM_PROVIDER=bedrock`, `BEDROCK_MODEL_ID`, `AWS_REGION` |
| Extraction provider boundary | OpenRouter remains independently scoped to E04 |
| Credentials used in this acceptance | None; Bedrock was mocked |

## Integrated behavior

- The coordinator invokes explanation only after deterministic evaluation completes.
- The Bedrock adapter sends the immutable recommendation and compact goal context rather than raw documents.
- Strict response parsing rejects malformed JSON, extra fields, and plan identifiers that are not present in the deterministic eligible-plan result.
- Provider failure produces typed failed run events while preserving the deterministic recommendation for inspection.
- Provider, model or inference-profile ID, prompt version, latency, token counts, and outcome are recorded.
- The frontend renders explanation as escaped text and clears it after a confirmed revision or undo so stale prose cannot accompany a changed recommendation.
- Goal classification recognizes common project and protection intents, including word-based timeframes, and focused questions do not ask no-policy users about nonexistent private cover.

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

## Open gates

- No AWS credentials were available, so model access, IAM permissions, regional availability, model or inference-profile entitlement, live latency, and output quality were not exercised.
- Estimated priced cost is not yet calculated even though token counts are captured.
- OpenRouter E04 extraction remains blocked on the exact model-slug decision.
- Full changed-goal browser acceptance, broader profile and extraction revisions, AWS deployment, and production security remain open.
- Real-product comparison and ranking gates are unchanged; the implemented E07 ranking remains synthetic and deterministic.
