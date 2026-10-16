import pytest

from app.services.sql_validator import SQLValidationError, validate_sql

T = {"data"}


@pytest.mark.parametrize("sql", [
    "SELECT sum(quantity * unit_price) AS revenue FROM data",
    "WITH r AS (SELECT region, sum(quantity) q FROM data GROUP BY 1) SELECT * FROM r ORDER BY q DESC",
    "SELECT * FROM data UNION ALL SELECT * FROM data",
    'SELECT "region" FROM "data" LIMIT 5 -- comment',
])
def test_allows_safe(sql):
    assert validate_sql(sql, T)


@pytest.mark.parametrize("sql", [
    "DROP TABLE data",
    "DELETE FROM data",
    "INSERT INTO data VALUES (1)",
    "SELECT 1; DROP TABLE data",
    "SELECT * FROM read_csv('/etc/passwd')",
    "SELECT * FROM '/etc/passwd'",
    "SELECT * FROM other_table",
    "SELECT * FROM main.data",
    "COPY data TO '/tmp/x.csv'",
    "ATTACH 'x.db'",
    "INSTALL httpfs",
    "PRAGMA database_list",
    "SET memory_limit='100GB'",
    "SELECT read_text('/etc/passwd')",
    "SELECT * FROM glob('/*')",
    "",
    "SELEC garbage ((",
])
def test_rejects_unsafe(sql):
    with pytest.raises(SQLValidationError):
        validate_sql(sql, T)
