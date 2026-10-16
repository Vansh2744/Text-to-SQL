# Deployment

**Frontend (Vercel)**: root `frontend/`. Env: `NEXT_PUBLIC_API_URL` (backend URL), `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`, `CLERK_SECRET_KEY`. Do not set `NEXT_PUBLIC_DEV_USER` in production.

**Backend (Render/Railway)**: root `backend/`, Dockerfile provided (binds to `$PORT`).
- Run `alembic upgrade head` as an explicit release/pre-deploy step.
- Required env: `APP_ENV=production`, `AUTH_MODE=clerk`, `CLERK_ISSUER`, `CLERK_JWKS_URL`, `DATABASE_URL` (managed Postgres, `postgresql+psycopg://...`), `FRONTEND_ORIGIN` (exact Vercel origin; CORS allows only this), `GROQ_API_KEY`, `GROQ_MODEL`.
- Startup fails if `AUTH_MODE=dev` with `APP_ENV=production`, or if Clerk settings are missing.
- Health checks: `/api/v1/health` (liveness), `/api/v1/health/ready` (DB + storage).

**Storage**: uploads and `.duckdb` files live in `UPLOAD_DIR`. Platform filesystems are ephemeral unless you attach a persistent disk and point `UPLOAD_DIR` at it; without one, datasets disappear on restart while their metadata remains. A persistent disk ties you to one instance. For multiple instances, implement an S3-compatible `storage` class (not implemented yet).

**Resources**: each query holds up to `DUCKDB_MEMORY_LIMIT` per connection and `MAX_CONCURRENT_QUERIES` run at once; size the instance for roughly limit x concurrency plus the app. Upload cap `MAX_UPLOAD_SIZE_MB`. Ingestion runs inside the upload request, so very large files can hit platform request timeouts; move ingestion to a worker if that happens.

**Not verified**: nothing here has been deployed or tested on Render, Railway or Vercel.
