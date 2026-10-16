# Security

**SQL safety (defense in depth)**
1. LLM output is untrusted. `validate_sql` (SQLGlot AST allowlist) runs on generated, edited, saved and rerun SQL: one statement, `SELECT` only, no DDL/DML/COPY/ATTACH/PRAGMA/SET, no table functions or file paths, only the dataset table and its CTEs, no `read_*`/`glob`/`query*` functions.
2. Execution uses a **read-only** DuckDB connection with `enable_external_access=false`, memory/thread limits, locked configuration, a timeout (interrupt) and a row cap.
3. Each dataset has its own DuckDB file, so a query cannot see another dataset.

**AuthN/AuthZ**: Clerk JWTs are verified server-side (RS256 via JWKS, issuer, expiry). User ids are never taken from request bodies. Every resource lookup checks `owner_id` and returns 404 (no existence leak). `AUTH_MODE=dev` is rejected at startup when `APP_ENV=production`.

**Uploads**: extension allowlist, size cap, content sniffing (Parquet magic, XLSX zip structure), server-generated storage keys (filename never used as a path), column cap.

**Limits**: per-user rate limit (in-memory), bounded concurrent queries, retry cap on LLM correction.

**Known limitations**: rate limiter is per-process; XLSX is parsed by pandas/openpyxl in-process (zip-bomb risk, bounded only by upload size); prompt injection via data values cannot be fully prevented, only contained by validation + read-only execution; no per-user quotas on stored data yet.
