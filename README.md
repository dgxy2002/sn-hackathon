# Before You Commit

Before You Commit is a local-first financial commitment reality check for people
reviewing a Singapore life-insurance offer or newly issued policy. It turns the
user's own PDF bundle into an inspectable brief: what the documents say, which
claims are conditional or contradicted, what remains unknown, and which questions
to resolve before signing or before a free-look deadline.

The product does not rank products, assess suitability, or tell a user to buy,
cancel, surrender, or replace a policy. The active product and migration contract
is [PLAN.md](PLAN.md).

## Trust model

- Raw uploads and raw extracted text stay inside an isolated local processing
  workspace and are deleted at the end of processing.
- User documents are never added to the public evidence corpus or test fixtures.
- Only explicitly consented, redacted, validated structured fields may be sent to
  Amazon Bedrock.
- Deterministic code owns facts, calculations, claim statuses, and citation
  validation. Model output is explanatory and fails closed.
- Uploaded-document evidence and official public guidance remain separate evidence
  planes throughout the API and interface.
- Missing, unknown, unreadable, absent, and not-applicable values are distinct.

## Runtime

- Vite frontend served through unprivileged NGINX.
- FastAPI backend with versioned Pydantic contracts.
- PostgreSQL 16 with pgvector for official guidance, redacted session artifacts,
  task state, revisions, and content-free metrics.
- A bounded worker for allowlisted official-guidance refresh.
- Amazon Bedrock for optional constrained explanation in the judged path.

No cloud credential is required for local deterministic development.

## Docker Compose

```bash
cp .env.example .env
docker compose up --build -d
docker compose ps
```

Open `http://localhost:4173`. The web container proxies `/api` to the backend.
The API is directly inspectable at `http://localhost:8000/health`; the new API
surface is rooted at `/api/v2`.

On a corporate network that intercepts TLS, set `CORPORATE_CA_CERT_PATH` in
`.env` and use the opt-in build override:

```bash
docker compose -f compose.yaml -f compose.corporate-ca.yaml up --build -d
```

BuildKit exposes the CA only to dependency-install steps. Never commit the
certificate or disable TLS verification.

To stop the runtime:

```bash
docker compose down
```

Use `docker compose down --volumes` only when the local PostgreSQL data should
also be deleted.

## Local development

Python 3.11 or later is recommended.

```powershell
python -m venv backend/.venv
backend/.venv/Scripts/python -m pip install -r backend/requirements.txt
backend/.venv/Scripts/python -m uvicorn app.main:app `
  --app-dir backend --env-file backend/.env --reload --port 8000
```

```powershell
Set-Location frontend
npm ci
Copy-Item .env.example .env
npm run dev
```

The Vite development server is available at `http://localhost:5173` by default.
When using another origin, add its exact value to `ALLOWED_ORIGINS`; wildcard
origins are rejected.

## API

Create an expiring analysis session:

```http
POST /api/v2/analyses
Content-Type: application/json

{
  "purpose": "considering_offer",
  "model_consent": {
    "enabled": false,
    "acknowledged_at": null
  }
}
```

All v2 mutation endpoints use strict request contracts. Uploads are streamed and
size-limited, and later analysis stages require accepted, hash-bound upstream
artifacts. Stable error envelopes do not expose parser, provider, filesystem, or
document content.

## Tests

With a local backend environment:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
$env:PYTHONPATH = 'backend'
backend/.venv/Scripts/python -m pytest backend/tests -q
```

Or use the backend image without requiring a host Python environment:

```powershell
docker compose run --rm --no-deps -e DATABASE_URL= `
  -v "${PWD}/backend:/app" backend python -m pytest tests -q
```

Run the versioned synthetic material-term evaluation baseline:

```powershell
docker compose run --rm --no-deps -e DATABASE_URL= `
  -v "${PWD}/backend:/app" backend python -m scripts.evaluate_material_terms
```

This corpus checks deterministic exact match, unknown preservation, and source
binding. It does not replace Gate 3 evaluation against representative documents.

Never place provider, database, document, or object-store secrets in the frontend
or in version control.
