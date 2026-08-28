# sn-hackathon

CoverCheck SG is a local-first insurance-readiness POC. The browser journey and
comparison remain visibly synthetic. Its final-page panel calls a typed FastAPI
agent that can also search read-only evidence from 79 cached insurer brochures.
The credential-free cached adapter is the default; an optional Supabase adapter
uses the same response contract.

Real-product evidence remains read-only and cannot alter the synthetic plan
ranking. The approved bridge, evidence-state rules, provider split, date
research, and delivery order are recorded in the
[RAG and website integration decisions](docs/evaluation/2026-08-28-rag-website-integration-decisions.md).

## Frontend

```bash
cd frontend
npm ci
cp .env.example .env
npm run dev
```

The Vite app is available at `http://localhost:5173` by default.

## Backend fixture API

Python 3.11 or later is recommended.

```bash
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
PYTHONPATH=backend backend/.venv/bin/uvicorn app.main:app \
	--env-file backend/.env --reload --port 8000
```

Cached and fixture modes need no production credential. Verify the service at
`http://localhost:8000/health` and discover capability modes at
`http://localhost:8000/v1/capabilities`.

The frontend reads `VITE_API_URL` at build or development-server startup. When
using a non-default frontend port, add its exact origin to `ALLOWED_ORIGINS` in
`backend/.env`; wildcard origins are rejected.

## Docker Compose demo

Docker Compose starts the built web app, cached-evidence API, and a healthy
PostgreSQL 16 instance with pgvector enabled. No cloud credential is required.

```bash
cp .env.example .env
docker compose up --build -d
docker compose ps
```

Open `http://localhost:4173`. The web container proxies `/api` to the backend,
so no backend URL or secret is embedded in the browser bundle. The API remains
directly inspectable at `http://localhost:8000/health`.

```bash
docker compose down
```

Use `docker compose down --volumes` only when the local PostgreSQL volume should
also be removed.

The Compose PostgreSQL service currently proves container and pgvector startup
only. The API intentionally reports its database dependency as not configured
and uses the committed cached corpus; local PostgreSQL retrieval, migrations,
the singleton scraper loop, and optional object storage remain pending epics.

Run the focused backend checks with:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=backend \
	backend/.venv/bin/python -m pytest backend/tests -q
```

Run the complete current verification set with:

```bash
bash scripts/verify-poc.sh
```

## Insurance RAG CLI

The extraction, Supabase ingestion, retrieval, and evaluation workflow is
documented in the [RAG operator guide](backend/scraper/RAG_README.md). It uses
OpenAI for offline brochure extraction and embeddings; this is separate from
the configured OpenRouter boundary for user-document and orchestration work.

Supabase remains the optional live adapter. Local PostgreSQL/pgvector retrieval
remains the required POC target and is not implied by the Compose bootstrap.

Never place provider, database, or object-store secrets in the frontend or in
version control. The exact `OPENROUTER_MODEL` value remains blank until project
decision DEC-002 is resolved.