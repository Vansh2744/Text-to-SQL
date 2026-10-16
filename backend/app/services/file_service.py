"""Ingest an uploaded file into a per-dataset DuckDB file (table name: data).
Ingestion uses a normal connection; queries later use a locked-down read-only one."""
from pathlib import Path

import duckdb
import pandas as pd

TABLE = "data"
ALLOWED = {".csv", ".xlsx", ".parquet"}


class IngestionError(ValueError):
    pass


def ingest(src: Path, ext: str, db_path: Path, max_columns: int) -> dict:
    ext = ext.lower()
    if ext not in ALLOWED:
        raise IngestionError("Unsupported file type.")
    if src.stat().st_size == 0:
        raise IngestionError("File is empty.")
    con = duckdb.connect(str(db_path))
    try:
        if ext == ".csv":
            con.execute(f"CREATE TABLE {TABLE} AS SELECT * FROM read_csv_auto(?)", [str(src)])
        elif ext == ".parquet":
            con.execute(f"CREATE TABLE {TABLE} AS SELECT * FROM read_parquet(?)", [str(src)])
        else:
            df = pd.read_excel(src)
            con.register("df_in", df)
            con.execute(f"CREATE TABLE {TABLE} AS SELECT * FROM df_in")
        info = con.execute(f"DESCRIBE {TABLE}").fetchall()
        if len(info) > max_columns:
            raise IngestionError(f"Too many columns (max {max_columns}).")
        rows = con.execute(f"SELECT count(*) FROM {TABLE}").fetchone()[0]
        return {"row_count": rows, "columns": [{"name": r[0], "type": r[1]} for r in info]}
    except duckdb.Error as e:
        raise IngestionError(f"Could not read file: {str(e).splitlines()[0]}") from e
    finally:
        con.close()
