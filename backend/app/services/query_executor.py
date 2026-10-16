import datetime as dt
import decimal
import threading
import time
from dataclasses import dataclass
from pathlib import Path

import duckdb


class QueryTimeout(Exception):
    pass


class QueryExecutionError(Exception):
    pass


class DatasetFilesMissing(Exception):
    """Dataset metadata exists but its analytical file is gone (wiped disk, other volume)."""


@dataclass
class QueryResult:
    columns: list[dict]
    rows: list[list]
    row_count: int
    truncated: bool
    duration_ms: int


def _to_json(v):
    if isinstance(v, decimal.Decimal):
        return float(v)
    if isinstance(v, (dt.date, dt.datetime, dt.time)):
        return v.isoformat()
    if isinstance(v, (bytes, bytearray)):
        return v.hex()
    if isinstance(v, (list, tuple, dict)):
        return str(v)
    return v


def execute_query(
    db_path: str | Path,
    sql: str,
    *,
    max_rows: int,
    timeout_s: float,
    memory_limit: str = "512MB",
    threads: int = 2,
) -> QueryResult:
    """Run already-validated SQL on a read-only connection with no external access."""
    if not Path(db_path).exists():
        raise DatasetFilesMissing(str(db_path))
    con = duckdb.connect(
        str(db_path),
        read_only=True,
        config={
            "enable_external_access": False,
            "memory_limit": memory_limit,
            "threads": threads,
            "lock_configuration": True,
        },
    )
    timer = threading.Timer(timeout_s, con.interrupt)
    start = time.perf_counter()
    try:
        timer.start()
        cur = con.execute(sql)
        cols = [{"name": d[0], "type": str(d[1])} for d in cur.description]
        fetched = cur.fetchmany(max_rows + 1)
    except duckdb.InterruptException as e:
        raise QueryTimeout(f"Query exceeded {timeout_s}s.") from e
    except duckdb.Error as e:
        raise QueryExecutionError(str(e).splitlines()[0]) from e
    finally:
        timer.cancel()
        con.close()
    truncated = len(fetched) > max_rows
    rows = [[_to_json(v) for v in r] for r in fetched[:max_rows]]
    return QueryResult(cols, rows, len(rows), truncated, int((time.perf_counter() - start) * 1000))
