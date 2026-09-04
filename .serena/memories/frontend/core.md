# Frontend

- Location: `frontend/`; Vite 8 with vanilla JavaScript, CSS, and individually imported Lucide icons.
- Entry: `frontend/src/main.js`; transport: `frontend/src/api.js`; global styles: `frontend/src/style.css`.
- Active journey: upload -> privacy review -> source-bound term review -> reviewed summary -> deletion.
- Browser transport uses canonical `/api/v2` URLs through the NGINX `/api` proxy.
- Uses ES modules, single quotes, no semicolons, two-space indentation in JS; CSS uses custom properties and nested CSS syntax accepted by current Vite toolchain.
- `package.json` scripts: `dev`, `build`, `preview`; no lint/test/typecheck script exists.
- Keep stage-change scroll reset, desktop/mobile layouts, explicit unknown copy, privacy metadata-only responses, and the non-advice boundary.
- User journey and UX/trust constraints are defined in `PLAN.md`.
