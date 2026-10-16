"""Orchestrates: generate -> validate -> execute -> visualize/explain -> record history."""
import logging
import threading

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.exceptions import AppError
from app.models import Conversation, Dataset, Message, QueryHistory, User
from app.services.explanation_service import explain
from app.services.file_service import TABLE
from app.services.llm_service import LLMError, LLMProvider
from app.services.query_executor import (
    QueryExecutionError,
    QueryResult,
    QueryTimeout,
    execute_query,
)
from app.services.sql_generator import generate_sql
from app.services.sql_validator import SQLValidationError, validate_sql
from app.services.visualization_service import recommend
from app.storage import storage

log = logging.getLogger("querypilot.query")
_slots: threading.BoundedSemaphore | None = None


def _run(ds: Dataset, sql: str, settings: Settings) -> QueryResult:
    global _slots
    if _slots is None:
        _slots = threading.BoundedSemaphore(settings.max_concurrent_queries)
    if not _slots.acquire(timeout=5):
        raise AppError(429, "busy", "The server is busy. Try again shortly.")
    try:
        path = storage.dataset_dir(ds.owner_id, ds.storage_key) / "data.duckdb"
        return execute_query(
            path, sql, max_rows=settings.max_result_rows, timeout_s=settings.query_timeout_seconds,
            memory_limit=settings.duckdb_memory_limit, threads=settings.duckdb_threads,
        )
    finally:
        _slots.release()


def _record(db: Session, user: User, ds: Dataset, *, question, sql, status, category=None,
            result: QueryResult | None = None, conv: Conversation | None = None) -> QueryHistory:
    h = QueryHistory(
        owner_id=user.id, dataset_id=ds.id, conversation_id=conv.id if conv else None,
        question=question, sql=sql, status=status, error_category=category,
        duration_ms=result.duration_ms if result else None,
        row_count=result.row_count if result else None,
    )
    db.add(h)
    db.commit()
    log.info("query status=%s dataset=%s category=%s", status, ds.id, category)
    return h


def _context(db: Session, conv: Conversation | None) -> list[dict]:
    """Last few question/SQL pairs of this conversation (never from other datasets)."""
    if not conv:
        return []
    rows = db.scalars(
        select(QueryHistory)
        .where(QueryHistory.conversation_id == conv.id, QueryHistory.status == "success")
        .order_by(QueryHistory.created_at.desc()).limit(3)
    ).all()
    return [{"question": r.question or "", "sql": r.sql or ""} for r in reversed(rows)]


def _result_dict(h: QueryHistory, res: QueryResult, sql, question, viz, explanation, attempts, conv):
    return {
        "query_id": h.id, "question": question, "sql": sql, "columns": res.columns,
        "rows": res.rows, "row_count": res.row_count, "truncated": res.truncated,
        "duration_ms": res.duration_ms, "visualization": viz, "explanation": explanation,
        "attempts": attempts, "conversation_id": conv.id if conv else None,
    }


def _raise_final(kind: str, msg: str):
    if kind == "validation_error":
        raise AppError(422, "sql_validation_failed", msg[:300])
    raise AppError(400, "query_failed", msg[:300])


def analyze_question(db: Session, user: User, ds: Dataset, question: str, provider: LLMProvider,
                     settings: Settings, conv: Conversation | None = None) -> dict:
    columns = ds.schema_json["columns"]
    history = _context(db, conv)
    error = prev = None
    last: tuple[str, str] = ("query_failed", "Unknown error")
    attempts = 0
    for _ in range(settings.sql_retry_limit + 1):
        attempts += 1
        try:
            gen = generate_sql(provider, question, TABLE, columns, history, error, prev)
        except LLMError as e:
            _record(db, user, ds, question=question, sql=prev, status="llm_error",
                    category="llm", conv=conv)
            raise AppError(502, "llm_unavailable",
                           "The AI provider failed or returned an unusable answer.") from e
        raw = gen["sql"]
        try:
            sql = validate_sql(raw, {TABLE})
        except SQLValidationError as e:
            error, prev, last = str(e), raw, ("validation_error", str(e))
            continue
        try:
            res = _run(ds, sql, settings)
        except QueryTimeout as e:
            _record(db, user, ds, question=question, sql=sql, status="timeout",
                    category="timeout", conv=conv)
            raise AppError(504, "query_timeout", "The query took too long.") from e
        except QueryExecutionError as e:
            error, prev, last = str(e), sql, ("execution_error", str(e))
            continue
        viz = recommend(res.columns, res.rows, gen.get("visualization"))
        text = explain(provider, question, res.columns, res.rows, res.truncated)
        h = _record(db, user, ds, question=question, sql=sql, status="success", result=res, conv=conv)
        if conv:
            _add_messages(db, conv, question, sql, text, h.id)
        return _result_dict(h, res, sql, question, viz, text, attempts, conv)
    _record(db, user, ds, question=question, sql=prev, status=last[0], category=last[0], conv=conv)
    _raise_final(*last)


def execute_sql(db: Session, user: User, ds: Dataset, sql: str, settings: Settings,
                question: str | None = None) -> dict:
    """Run user-supplied/edited/saved SQL through the exact same validation + execution path."""
    try:
        clean = validate_sql(sql, {TABLE})
    except SQLValidationError as e:
        _record(db, user, ds, question=question, sql=sql, status="validation_error",
                category="validation_error")
        raise AppError(422, "sql_validation_failed", str(e)[:300]) from e
    try:
        res = _run(ds, clean, settings)
    except QueryTimeout as e:
        _record(db, user, ds, question=question, sql=clean, status="timeout", category="timeout")
        raise AppError(504, "query_timeout", "The query took too long.") from e
    except QueryExecutionError as e:
        _record(db, user, ds, question=question, sql=clean, status="execution_error",
                category="execution_error")
        raise AppError(400, "query_failed", str(e)[:300]) from e
    h = _record(db, user, ds, question=question, sql=clean, status="success", result=res)
    viz = recommend(res.columns, res.rows)
    return _result_dict(h, res, clean, question, viz, None, 1, None)


def _add_messages(db: Session, conv: Conversation, question: str, sql: str, text: str, qid: str):
    db.add(Message(conversation_id=conv.id, role="user", content=question))
    db.add(Message(conversation_id=conv.id, role="assistant", content=text, sql=sql, query_id=qid))
    if conv.title == "New conversation":
        conv.title = question[:60]
    db.commit()
