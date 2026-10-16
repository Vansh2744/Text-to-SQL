from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models import Dataset, QueryHistory, SavedQuery, User
from app.schemas import DatasetOut, HistoryOut, SavedQueryOut

router = APIRouter(tags=["system"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/health/ready")
def ready(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    checks = {}
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "unavailable"
    p = Path(settings.upload_dir)
    checks["storage"] = "ok" if p.exists() or _mk(p) else "unavailable"
    ok = all(v == "ok" for v in checks.values())
    return JSONResponse({"status": "ready" if ok else "degraded", **checks}, 200 if ok else 503)


def _mk(p: Path) -> bool:
    try:
        p.mkdir(parents=True, exist_ok=True)
        return True
    except OSError:
        return False


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    def count(model):
        return db.scalar(select(func.count()).select_from(model).where(model.owner_id == user.id))

    def recent(model, schema, col):
        rows = db.scalars(select(model).where(model.owner_id == user.id)
                          .order_by(col.desc()).limit(5)).all()
        return [schema.model_validate(r).model_dump(mode="json") for r in rows]

    return {
        "dataset_count": count(Dataset), "query_count": count(QueryHistory),
        "recent_queries": recent(QueryHistory, HistoryOut, QueryHistory.created_at),
        "recent_datasets": recent(Dataset, DatasetOut, Dataset.created_at),
        "recent_saved_queries": recent(SavedQuery, SavedQueryOut, SavedQuery.updated_at),
    }
