# sn-hackathon

CoverCheck SG is a local-first insurance-readiness POC. The browser journey and
comparison remain visibly synthetic. Its final-page panel calls a typed FastAPI
agent that can search read-only evidence from 79 cached brochure documents,
representing 71 normalized policy products after deduplication,
propose a budget change, rerun the deterministic result after confirmation, and
replay or undo the revision. The invocation coordinator supports grounded
explanation through Amazon Bedrock while E07 retains sole ownership of plan
eligibility, scores, and ranking. Local PostgreSQL is the default cached adapter;
an optional Supabase adapter uses the same response contract.

Real-product evidence remains read-only and cannot alter the synthetic plan
ranking. The approved bridge, evidence-state rules, provider split, date
research, and delivery order are recorded in the
[RAG and website integration decisions](docs/evaluation/2026-08-28-rag-website-integration-decisions.md).

The current browser POC starts with two direct routes: **I do not have a plan**
and **Review a plan I have**. A four-question readiness check remains available
as an optional, no-sign-in detour. Consent does not collect a name, email, NRIC,
medical details, payment data, or beneficiary information.

The no-plan route asks for only five decision inputs: monthly take-home income,
total liabilities, primary protection goal, protection-versus-savings
preference, and maximum additional monthly premium. Private-policy status is
preset to No and all private-policy amounts are sent as `not_applicable`. The
existing-plan route adds four user-verified figures: current monthly premium,
death benefit, total permanent disability benefit, and advanced critical
illness benefit. A synthetic extraction sample demonstrates reviewable policy
fields; selected personal-file contents are not processed by this POC.

The deterministic formulation uses annual income x 9 plus liabilities for
death and TPD targets, and annual income x 4 for the critical-illness target.
Monthly expenses are not a critical input because the current calculation does
not use them. Four labelled synthetic plans are eligible for ranking. The 71
normalized cached real products remain read-only evidence and cannot enter the
ranking; no real product has passed the separate comparison or ranking gates.

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

Amazon Bedrock is the required live E11 explanation provider. Set
`ORCHESTRATION_MODE=live`, `LLM_PROVIDER=bedrock`, `AWS_REGION`, and
`BEDROCK_MODEL_ID`; boto3 uses its standard local credential chain and ECS uses
a task role. The model receives the immutable recommendation plus compact
personalization context and can return explanation text only. Invalid output or
provider failure produces a typed failed run without changing the deterministic
recommendation. Simulated mode uses the same explanation contract without AWS
credentials.

The credentialed Compose path, including corporate TLS interception, has been
validated end to end. The dated evidence and remaining non-production gates are
recorded in the
[Bedrock and personalization integration record](docs/evaluation/2026-09-03-bedrock-personalization-integration.md).

## Docker Compose demo

Docker Compose starts the built web app, cached-evidence API, singleton scraper
worker, and PostgreSQL 16 with pgvector enabled. No cloud credential is required.

```bash
cp .env.example .env
docker compose up --build -d
docker compose ps
```

On a corporate network that intercepts TLS, point
`CORPORATE_CA_CERT_PATH` in `.env` to the organization-provided PEM or CRT
bundle and use the opt-in build override:

```bash
docker compose -f compose.yaml -f compose.corporate-ca.yaml up --build -d
```

BuildKit exposes the CA only to the dependency-install build steps. The backend
image installs it into the system trust bundle so boto3 can call Bedrock at
runtime. Do not add the certificate file itself to the repository, and never
disable TLS verification.

Open `http://localhost:4173`. The web container proxies `/api` to the backend,
so no backend URL or secret is embedded in the browser bundle. The API remains
directly inspectable at `http://localhost:8000/health`.

```bash
docker compose down
```

Use `docker compose down --volumes` only when the local PostgreSQL volume should
also be removed.

The backend queries the Compose database for cached evidence. Runtime migrations
load the committed corpus idempotently, and the database-backed singleton scraper
waits when no approved source is due. Optional object storage remains unconfigured.
No cached source is approved for live fetching or real-product comparison.

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
the configured OpenRouter boundary for user-document extraction and the Amazon
Bedrock boundary for E11 grounded explanation.

Supabase remains the optional live adapter. Local PostgreSQL/pgvector retrieval
is the accepted local POC path; source permission and real-product Phase 3B
eligibility remain separate gates.

Never place provider, database, or object-store secrets in the frontend or in
version control. The exact `OPENROUTER_MODEL` value remains blank until project
decision DEC-002 is resolved.