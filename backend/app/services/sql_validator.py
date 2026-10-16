"""AST-based read-only SQL policy. Defense in depth: the executor also runs
queries on a read-only connection with external access disabled."""
import sqlglot
from sqlglot import exp
from sqlglot.errors import SqlglotError


class SQLValidationError(ValueError):
    pass


_FORBIDDEN_NODES = tuple(
    getattr(exp, n)
    for n in (
        "Insert", "Update", "Delete", "Drop", "Create", "Alter", "Command", "Copy", "Set",
        "Use", "Merge", "Transaction", "Attach", "Detach", "Pragma", "Describe", "Show",
    )
    if hasattr(exp, n)
)
_FORBIDDEN_FUNC_PREFIXES = ("read_", "write_", "glob", "query", "getenv", "install", "load")


def validate_sql(sql: str, allowed_tables: set[str]) -> str:
    """Return normalized single SELECT statement or raise SQLValidationError."""
    if not sql or not sql.strip():
        raise SQLValidationError("Empty SQL.")
    try:
        statements = [s for s in sqlglot.parse(sql, read="duckdb") if s is not None]
    except SqlglotError as e:
        raise SQLValidationError(f"Could not parse SQL: {e}") from e
    if len(statements) != 1:
        raise SQLValidationError("Exactly one statement is allowed.")
    tree = statements[0]
    if not isinstance(tree, (exp.Select, exp.Union, exp.Subquery)):
        raise SQLValidationError("Only SELECT queries are allowed.")

    allowed = {t.lower() for t in allowed_tables}
    cte_names = {c.alias_or_name.lower() for c in tree.find_all(exp.CTE)}

    for node in tree.walk():
        if isinstance(node, _FORBIDDEN_NODES):
            raise SQLValidationError(f"{type(node).__name__} is not allowed.")
        if isinstance(node, exp.Anonymous) and node.name.lower().startswith(_FORBIDDEN_FUNC_PREFIXES):
            raise SQLValidationError(f"Function '{node.name}' is not allowed.")
        if isinstance(node, exp.Table):
            if not isinstance(node.this, exp.Identifier):
                raise SQLValidationError("Table functions and file paths are not allowed.")
            if node.args.get("db") or node.args.get("catalog"):
                raise SQLValidationError("Qualified table names are not allowed.")
            name = node.name.lower()
            if name not in allowed and name not in cte_names:
                raise SQLValidationError(f"Unknown table '{node.name}'.")
    return tree.sql(dialect="duckdb")
