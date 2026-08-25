# Backend Scraper/Data

- Location: `backend/scraper/`.
- `card_scraper.py` scrapes SingSaver credit-card data and writes via Supabase REST; this is current implemented data ingestion, while insurance/RAG agents remain planned.
- Dependencies in `backend/scraper/requirements.txt`: BeautifulSoup 4, python-dotenv, requests.
- Default env file: `backend/.env`; accepted URL vars: `SUPABASE_URL` or `NEXT_PUBLIC_SUPABASE_URL`; service-key vars: `SUPABASE_SERVICE_ROLE_KEY` or `SUPABASE_KEY`. Never expose or commit service-role keys.
- CLI flags: `--env-file`, `--limit`, `--only`, `--delay`, `--timeout`, `--dry-run`, `--skip-details`, `--verbose`.
- Apply `backend/scraper/credit_card_schema.sql` before DB writes; `supabase_schema.sql` contains broader insurance, policy, document chunk, and scrape-log schema.
- Prefer `--dry-run --limit N` for cheap validation before any write-enabled run.