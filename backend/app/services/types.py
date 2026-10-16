_NUMERIC = {"TINYINT", "SMALLINT", "INTEGER", "BIGINT", "HUGEINT", "UTINYINT", "USMALLINT",
            "UINTEGER", "UBIGINT", "FLOAT", "DOUBLE", "DECIMAL"}


def base_type(t: str) -> str:
    return t.split("(")[0].strip().upper()


def is_numeric(t: str) -> bool:
    return base_type(t) in _NUMERIC


def is_temporal(t: str) -> bool:
    return base_type(t).startswith(("DATE", "TIMESTAMP"))


def quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'
