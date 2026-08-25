# Conventions

- Keep frontend and backend module setup independent; there is no root workspace/build command.
- Frontend currently follows vanilla ES-module style: single quotes, no semicolons, two-space indentation; preserve existing accessibility attributes and static asset paths.
- Python scraper uses type annotations, explicit exception classes, `argparse`, session-based HTTP, and nonzero exit behavior; add clear CLI errors rather than silent fallback.
- Keep secrets in `backend/.env`; never commit Supabase service-role credentials.
- Structured agent data must retain provenance, confidence/unknown status, effective date, and synthetic/real marker.
- Eligibility, affordability, and numerical gap calculations must be deterministic and testable; use LLM output only for grounded plain-language explanations.
- Frontend design protocols are on-demand skills under `.agents/skills/`; their quality-gate sequence must run before implementation when invoked.