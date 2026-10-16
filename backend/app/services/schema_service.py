from pathlib import Path

from app.core.config import Settings
from app.services.file_service import TABLE
from app.services.query_executor import execute_query
from app.services.types import is_numeric, quote_ident


def profile_dataset(db_path: Path, columns: list[dict], settings: Settings) -> list[dict]:
    """Per-column null/distinct counts and numeric min/max/avg in a single bounded query."""
    parts = []
    for i, c in enumerate(columns):
        q = quote_ident(c["name"])
        parts.append(f"count(*) FILTER (WHERE {q} IS NULL) AS n{i}")
        parts.append(f"approx_count_distinct({q}) AS d{i}")
        if is_numeric(c["type"]):
            parts.append(f"min({q}) AS lo{i}, max({q}) AS hi{i}, avg({q}) AS av{i}")
    res = execute_query(
        db_path, f"SELECT {', '.join(parts)} FROM {TABLE}", max_rows=1,
        timeout_s=settings.query_timeout_seconds, memory_limit=settings.duckdb_memory_limit,
        threads=settings.duckdb_threads,
    )
    row = dict(zip([c["name"] for c in res.columns], res.rows[0], strict=True))
    out = []
    for i, c in enumerate(columns):
        p = {"name": c["name"], "type": c["type"], "null_count": row[f"n{i}"],
             "distinct_count": row[f"d{i}"]}
        if is_numeric(c["type"]):
            p.update(min=row[f"lo{i}"], max=row[f"hi{i}"], avg=row[f"av{i}"])
        out.append(p)
    return out
