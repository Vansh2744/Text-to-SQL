from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.exceptions import AppError
from app.core.security import get_subject
from app.db.session import get_db
from app.models import Dataset, User
from app.services.llm_service import LLMError, LLMProvider, get_provider


def get_current_user(
    request: Request, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)
) -> User:
    subject = get_subject(request, settings)
    user = db.scalar(select(User).where(User.auth_subject == subject))
    if not user:
        user = User(auth_subject=subject)
        db.add(user)
        db.commit()
    return user


def get_owned(db: Session, model, resource_id: str, user: User):
    """Fetch a resource only if the current user owns it; 404 otherwise (no existence leak)."""
    obj = db.get(model, resource_id)
    if obj is None or obj.owner_id != user.id:
        raise AppError(404, "not_found", "Resource not found.")
    return obj


def get_ready_dataset(db: Session, dataset_id: str, user: User) -> Dataset:
    ds = get_owned(db, Dataset, dataset_id, user)
    if ds.status != "ready":
        raise AppError(409, "dataset_not_ready", "Dataset is not ready for querying.")
    return ds


def get_llm(settings: Settings = Depends(get_settings)) -> LLMProvider:
    try:
        return get_provider(settings)
    except LLMError as e:
        raise AppError(503, "llm_not_configured", str(e)) from e
