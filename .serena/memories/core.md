# Project Core

- Singapore IGNITE Agentic AI Hackathon prototype for first-time working adults to understand inherited insurance, readiness gaps, and evidence-backed comparisons.
- Product boundary: educational comparison/readiness assistant, not regulated financial advice; do not transact, recommend cancellation, or present synthetic data as real.
- Top-level plan and acceptance criteria: `PLAN.md`; training requirements: `docs/IGNITE-Agentic-AI-Hackathon-Training-Session.md`.
- Modules: frontend conventions/runbook in `mem:frontend/core`; scraper/data conventions/runbook in `mem:backend/core`.
- Stack/dependency summary: `mem:tech_stack`; runnable commands: `mem:suggested_commands`; completion checks: `mem:task_completion`.
- Shared agent contracts in `PLAN.md`: versioned user profile, plan record with source/effective date and synthetic flag, recommendation result with reasons/evidence/assumptions.
- Agent invariants: deterministic eligibility/calculations; LLM explains but does not decide hard rules; preserve unknown values; every product claim needs source + date; bound loops and log usage.
- Repository-local VibeCurb design protocols live under `.agents/skills/`; invoke only the relevant skill for frontend/design work.