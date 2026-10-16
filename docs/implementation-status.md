# Implementation status

## Done and tested (50 backend tests, ruff clean, Alembic migration applies)
- Phase 1/2: config + startup validation, SQLAlchemy models, Alembic migration, Clerk JWT verification, dev auth mode, ownership checks (404 on foreign resources)
- Phase 3: secure upload (CSV/XLSX/Parquet), ingestion to per-dataset DuckDB, schema, preview, profile, rename, delete
- Phase 4: Groq provider abstraction, prompts, structured response parsing, error mapping
- Phase 5: SQLGlot validator, locked-down executor, concurrency + rate limits
- Phase 7 (backend): chart recommendation validated against result columns, grounded explanations with deterministic fallback
- Phase 8 (backend): query history, rerun, conversations with scoped follow-up context, saved queries, dashboard stats

- Frontend: dashboard, datasets (upload, inspect, rename, delete), query workspace (Monaco SQL editor, schema sidebar, suggestions, charts, results table with sort/filter/pagination/CSV export, follow-up conversations, save), history with rerun, saved queries, settings. Clerk when configured, dev mode otherwise.
- Frontend checks run: tsc clean, next build OK, 9 Vitest tests pass, live smoke test (CORS preflight, upload, execute, validation rejection, all pages return 200)

## Not done
- Never opened in a real browser: no visual/responsive/accessibility review, no Playwright e2e, Monaco and Clerk flows untested
- No ESLint config; no component tests for the upload/workspace flows
- Not run: live Groq call (the workspace Ask button needs a real GROQ_API_KEY/GROQ_MODEL), real Postgres (tests use SQLite; migration verified on SQLite only), Clerk token verification against a real tenant
- Docker Compose `api` profile and Dockerfile are written but never built or run

## Next
Browser review of the UI, Playwright e2e with a stubbed LLM, S3-compatible storage, worker for ingestion.
