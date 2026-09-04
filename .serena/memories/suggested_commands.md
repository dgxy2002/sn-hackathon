# Suggested Commands

## Runtime

```powershell
docker compose up --build -d
docker compose ps
```

## Frontend

```bash
cd frontend
npm ci
npm run build
npm run dev
npm run preview
```

## Backend tests in Docker

```powershell
$backend = (Resolve-Path '.\backend').Path
docker compose run --rm --no-deps -v "${backend}:/app" -w /app backend python -m pytest tests -q
```

Focused v2 files are `test_analysis_routes_v2.py`, `test_config_v2.py`, `test_contracts_v2.py`, `test_document_routes_v2.py`, `test_extraction_routes_v2.py`, and `test_system_routes.py`.

## Serena

```bash
serena memories check
```

Run from repository root to validate memory references after memory changes.
