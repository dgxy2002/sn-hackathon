# Suggested Commands

## Frontend

```bash
cd frontend
npm ci
npm run dev
npm run build
npm run preview
```

## Python scraper

```bash
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/scraper/requirements.txt
backend/.venv/bin/python backend/scraper/card_scraper.py --dry-run --limit 3
backend/.venv/bin/python backend/scraper/card_scraper.py --help
```

Write-enabled scraper runs require Supabase schema plus credentials in `backend/.env`; start with dry-run.

## Serena

```bash
serena memories check
```

Run from repository root to validate memory references after memory changes.