from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_owned, get_ready_dataset
from app.core.config import Settings, get_settings
from app.core.exceptions import AppError
from app.core.ratelimit import limiter
from app.db.session import get_db
from app.models import SavedQuery, User
from app.schemas import AnalysisOut, SavedQueryIn, SavedQueryOut, SavedQueryPatch
from app.services.file_service import TABLE
from app.services.query_service import execute_sql
from app.services.sql_validator import SQLValidationError, validate_sql

router = APIRouter(prefix="/saved-queries", tags=["saved-queries"])


def _check_sql(sql: str) -> str:
    try:
        return validate_sql(sql, {TABLE})
    except SQLValidationError as e:
        raise AppError(422, "sql_validation_failed", str(e)[:300]) from e


@router.post("", response_model=SavedQueryOut, status_code=201)
def create(body: SavedQueryIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ds = get_ready_dataset(db, body.dataset_id, user)
    sq = SavedQuery(owner_id=user.id, dataset_id=ds.id, title=body.title,
                    description=body.description, sql=_check_sql(body.sql))
    db.add(sq)
    db.commit()
    return sq


@router.get("", response_model=list[SavedQueryOut])
def list_saved(limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0),
               db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = select(SavedQuery).where(SavedQuery.owner_id == user.id)
    return db.scalars(q.order_by(SavedQuery.updated_at.desc()).limit(limit).offset(offset)).all()


@router.get("/{saved_id}", response_model=SavedQueryOut)
def get_saved(saved_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return get_owned(db, SavedQuery, saved_id, user)


@router.patch("/{saved_id}", response_model=SavedQueryOut)
def update_saved(saved_id: str, body: SavedQueryPatch, db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
    sq = get_owned(db, SavedQuery, saved_id, user)
    data = body.model_dump(exclude_unset=True)
    if "sql" in data:
        data["sql"] = _check_sql(data["sql"])
    for k, v in data.items():
        setattr(sq, k, v)
    db.commit()
    return sq


@router.delete("/{saved_id}", status_code=204)
def delete_saved(saved_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.delete(get_owned(db, SavedQuery, saved_id, user))
    db.commit()


@router.post("/{saved_id}/run", response_model=AnalysisOut)
def run_saved(saved_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user),
              settings: Settings = Depends(get_settings)):
    """Saved SQL is re-validated on every run."""
    limiter.check(user.id)
    sq = get_owned(db, SavedQuery, saved_id, user)
    ds = get_ready_dataset(db, sq.dataset_id, user)
    return execute_sql(db, user, ds, sq.sql, settings, sq.title)
