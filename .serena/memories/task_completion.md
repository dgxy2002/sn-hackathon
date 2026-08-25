# Task Completion

Run checks for the touched module; do not claim lint/test/typecheck because none are configured yet.

## Frontend changes

```bash
cd frontend
npm ci
npm run build
```

For visual changes, also run the Vite app and verify relevant desktop/mobile states; apply the invoked VibeCurb skill's visual-diff and accessibility gates.

## Scraper changes

```bash
backend/.venv/bin/python -m py_compile backend/scraper/card_scraper.py
backend/.venv/bin/python backend/scraper/card_scraper.py --help
backend/.venv/bin/python backend/scraper/card_scraper.py --dry-run --limit 3
```

Do not run a write-enabled scraper as routine validation. If dependencies are absent, create/install the venv using `mem:suggested_commands`.

## Repository/customization changes

```bash
git diff --check
serena memories check
```

Also verify each `.agents/skills/<name>/SKILL.md` has YAML `name` equal to the folder name and a non-empty `description`.