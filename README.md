# QueryPilot AI
Text-to-SQL analysis over uploaded CSV/XLSX/Parquet. See docs/implementation-status.md for what is verified and what is not.

## Backend
    docker compose up -d                      # Postgres
    cd backend && python -m venv .venv && source .venv/bin/activate
    pip install -e ".[dev]"
    cp .env.example .env                      # set GROQ_API_KEY, GROQ_MODEL
    alembic upgrade head
    uvicorn app.main:app --reload             # docs at http://localhost:8000/docs
    pytest && ruff check .

Try it (dev auth): upload `sample-data/sales.csv` with header `X-Dev-User: me`, then POST `/api/v1/queries/analyze`.
See docs/security.md and docs/api.md.

## Frontend
    cd frontend && npm install && cp .env.example .env.local && npm run dev
Open http://localhost:3000 (dev mode needs the backend run with `AUTH_MODE=dev`).
