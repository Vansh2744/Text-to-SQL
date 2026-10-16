from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_llm, get_owned, get_ready_dataset
from app.core.config import Settings, get_settings
from app.core.exceptions import AppError
from app.core.ratelimit import limiter
from app.db.session import get_db
from app.models import Conversation, QueryHistory, User
from app.schemas import AnalysisOut, AnalyzeRequest, ExecuteRequest, HistoryOut
from app.services.llm_service import LLMProvider
from app.services.query_service import analyze_question, execute_sql

router = APIRouter(prefix="/queries", tags=["queries"])


@router.post("/analyze", response_model=AnalysisOut)
def analyze(body: AnalyzeRequest, db: Session = Depends(get_db),
            user: User = Depends(get_current_user), provider: LLMProvider = Depends(get_llm),
            settings: Settings = Depends(get_settings)):
    """Question -> SQL -> validation -> execution -> chart recommendation + explanation."""
    limiter.check(user.id)
    ds = get_ready_dataset(db, body.dataset_id, user)
    conv = None
    if body.conversation_id:
        conv = get_owned(db, Conversation, body.conversation_id, user)
        if conv.dataset_id != ds.id:
            raise AppError(400, "dataset_mismatch", "Conversation belongs to another dataset.")
    return analyze_question(db, user, ds, body.question, provider, settings, conv)


@router.post("/execute", response_model=AnalysisOut)
def execute(body: ExecuteRequest, db: Session = Depends(get_db),
            user: User = Depends(get_current_user), settings: Settings = Depends(get_settings)):
    """Run user-edited SQL. Goes through the same backend validation as generated SQL."""
    limiter.check(user.id)
    ds = get_ready_dataset(db, body.dataset_id, user)
    return execute_sql(db, user, ds, body.sql, settings)


@router.get("/history", response_model=list[HistoryOut])
def history(limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0),
            dataset_id: str | None = None, db: Session = Depends(get_db),
            user: User = Depends(get_current_user)):
    q = select(QueryHistory).where(QueryHistory.owner_id == user.id)
    if dataset_id:
        q = q.where(QueryHistory.dataset_id == dataset_id)
    return db.scalars(q.order_by(QueryHistory.created_at.desc()).limit(limit).offset(offset)).all()


@router.get("/{query_id}", response_model=HistoryOut)
def get_query(query_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return get_owned(db, QueryHistory, query_id, user)


@router.post("/{query_id}/rerun", response_model=AnalysisOut)
def rerun(query_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user),
          settings: Settings = Depends(get_settings)):
    limiter.check(user.id)
    h = get_owned(db, QueryHistory, query_id, user)
    if not h.sql:
        raise AppError(400, "no_sql", "This history entry has no SQL to rerun.")
    ds = get_ready_dataset(db, h.dataset_id, user)
    return execute_sql(db, user, ds, h.sql, settings, h.question)
