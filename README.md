# sn-hackathon

CoverCheck SG is a local-first insurance-readiness POC. The browser journey is
currently synthetic. Its final-page panel calls a typed FastAPI fixture agent,
while a separate Supabase-backed RAG CLI can retrieve cited evidence from 79
cached insurer brochures. The two slices are not yet connected.

Real-product evidence remains read-only and cannot alter the synthetic plan
ranking. The approved bridge, evidence-state rules, provider split, date
research, and delivery order are recorded in the
[RAG and website integration decisions](docs/evaluation/2026-08-28-rag-website-integration-decisions.md).

## Frontend

```bash
cd frontend
npm ci
npm run dev
```

The Vite app is available at `http://localhost:5173` by default.

## Backend fixture API

Python 3.11 or later is recommended.

```bash
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
PYTHONPATH=backend backend/.venv/bin/uvicorn app.main:app --reload --port 8000
```

Fixture mode needs no production credential. Verify the service at
`http://localhost:8000/health` and discover capability modes at
`http://localhost:8000/v1/capabilities`.

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

Supabase is the implemented interim adapter. Local PostgreSQL/pgvector in
Docker Compose remains the required POC runtime target.

Never place provider, database, or object-store secrets in the frontend or in
version control. The exact `OPENROUTER_MODEL` value remains blank until project
decision DEC-002 is resolved.