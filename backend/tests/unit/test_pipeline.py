import json

import pytest

from app.core.config import Settings
from app.services.file_service import ingest
from app.services.llm_service import LLMError, get_provider
from app.services.query_executor import QueryExecutionError, QueryTimeout, execute_query
from app.services.sql_generator import generate_sql, parse_response
from app.services.sql_validator import validate_sql

CSV = "order_id,product,quantity,unit_price,region\n1,A,2,10.5,N\n2,B,1,20,S\n3,A,4,10.5,N\n"


@pytest.fixture
def db(tmp_path):
    src = tmp_path / "s.csv"
    src.write_text(CSV)
    path = tmp_path / "ds.duckdb"
    return path, ingest(src, ".csv", path, max_columns=50)


def test_ingest_schema(db):
    _, info = db
    assert info["row_count"] == 3
    assert [c["name"] for c in info["columns"]][:2] == ["order_id", "product"]


def test_execute_and_truncate(db):
    path, _ = db
    r = execute_query(path, "SELECT region, sum(quantity*unit_price) AS rev FROM data GROUP BY 1 ORDER BY 2 DESC",
                      max_rows=1, timeout_s=5)
    assert r.truncated and r.row_count == 1 and r.rows[0][0] == "N"


def test_external_access_blocked_at_engine_level(db):
    path, _ = db
    with pytest.raises(QueryExecutionError):
        execute_query(path, "SELECT * FROM read_csv('/etc/passwd')", max_rows=5, timeout_s=5)


def test_timeout(db):
    path, _ = db
    with pytest.raises(QueryTimeout):
        execute_query(path, "SELECT count(*) FROM range(100000000000) a, range(1000) b",
                      max_rows=5, timeout_s=1)


def test_generator_with_fake_llm(db):
    _, info = db

    class Fake:
        def complete(self, system, user):
            return json.dumps({"sql": "SELECT count(*) AS n FROM data", "explanation": "x"})

    out = generate_sql(Fake(), "how many rows?", "data", info["columns"])
    assert validate_sql(out["sql"], {"data"})


@pytest.mark.parametrize("bad", ["not json", "{}", '{"sql": ""}'])
def test_parse_errors(bad):
    with pytest.raises(LLMError):
        parse_response(bad)


def test_missing_key():
    with pytest.raises(LLMError):
        get_provider(Settings(groq_api_key="", groq_model=""))


def test_concurrent_queries_on_same_dataset(db):
    """Regression: DuckDB shares an instance per file; parallel requests used to fail with
    'configuration has been locked' (e.g. profile + preview fired together by the UI)."""
    import threading

    path, _ = db
    errors = []

    def worker():
        try:
            for _ in range(20):
                execute_query(path, "SELECT * FROM data", max_rows=5, timeout_s=5)
        except Exception as e:
            errors.append(repr(e))

    threads = [threading.Thread(target=worker) for _ in range(6)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert errors == []


@pytest.mark.parametrize("stmt", [
    "SET enable_external_access=true", "SET memory_limit='100GB'", "SET lock_configuration=false",
])
def test_configuration_stays_locked(db, stmt):
    from app.services.query_executor import QueryExecutionError

    path, _ = db
    with pytest.raises(QueryExecutionError):
        execute_query(path, stmt, max_rows=1, timeout_s=5)
