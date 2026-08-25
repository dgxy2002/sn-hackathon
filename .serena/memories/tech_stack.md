# Tech Stack

- Frontend: vanilla JavaScript ES modules, HTML/CSS, Vite `^8.2.2`; npm lockfile committed.
- Backend data ingestion: Python 3 script using `requests`, `beautifulsoup4`, `python-dotenv`; Supabase REST and SQL schemas.
- Planned, not yet implemented: Amazon Bedrock + likely AgentCore Runtime, RAG/vector storage, OCR, authentication.
- Serena project config enables TypeScript (for JS) and Python language servers in `.serena/project.yml`; current in-process server may need a fresh Serena session to apply newly added Python support.
- No root package manager/workspace config; install/run frontend and backend from their module directories.