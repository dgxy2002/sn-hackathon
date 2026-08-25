# Frontend

- Location: `frontend/`; current state is Vite starter-style vanilla JS, not React.
- Entry: `frontend/src/main.js`; global styles: `frontend/src/style.css`; static icons/assets under `frontend/public/` and `frontend/src/assets/`.
- Uses ES modules, single quotes, no semicolons, two-space indentation in JS; CSS uses custom properties and nested CSS syntax accepted by current Vite toolchain.
- `package.json` scripts: `dev`, `build`, `preview`; no lint/test/typecheck script exists.
- Design work should select relevant repository-local VibeCurb protocols from `.agents/skills/`; do not apply all skills indiscriminately.
- User journey and UX/trust constraints are defined in `PLAN.md`; preserve educational-not-advice boundary and synthetic/real labels.