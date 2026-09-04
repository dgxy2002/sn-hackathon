# Task Completion

Run checks for the touched module and keep `PLAN.md` implementation evidence current.

## Frontend changes

```bash
cd frontend
npm ci
npm run build
```

For visual changes, run the Compose app and verify relevant desktop/mobile states, console/network output, text fit, stage scroll position, and the authentic PDF journey.

## Backend changes

```powershell
$backend = (Resolve-Path '.\backend').Path
docker compose run --rm --no-deps -v "${backend}:/app" -w /app backend python -m pytest tests -q
```

Also rebuild affected images, check `/health`, inspect OpenAPI paths after route changes, and prove transient workspaces are removed after deletion tests.

## Repository/customization changes

```bash
git diff --check
serena memories check
```

Also verify each `.agents/skills/<name>/SKILL.md` has YAML `name` equal to the folder name and a non-empty `description`.
