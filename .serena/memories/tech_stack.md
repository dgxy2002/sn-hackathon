# Tech Stack

- Frontend: vanilla JavaScript ES modules, HTML/CSS, Vite `^8.2.2`, Lucide; npm lockfile committed.
- Backend: Python 3.11, FastAPI, Pydantic, PyMuPDF, local Tesseract OCR, psycopg, pytest, uvicorn, and optional boto3.
- Runtime: unprivileged NGINX, PostgreSQL 16 with pgvector, backend API, and bounded official-guidance worker under Docker Compose.
- Implemented: `/api/v2` session lifecycle, streamed PDF processing, text/OCR paths, privacy review, premium-term extraction/review, and deletion.
- Planned: durable v2 repositories, allowlisted official-guidance RAG, claims/orchestration, source inspection/export, and constrained optional Bedrock rendering.
- Serena project config enables TypeScript (for JS) and Python language servers in `.serena/project.yml`; current in-process server may need a fresh Serena session to apply newly added Python support.
- No root package manager/workspace config; install/run frontend and backend from their module directories.
