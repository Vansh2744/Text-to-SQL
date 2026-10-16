import shutil
import zipfile
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, Query, UploadFile
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_owned, get_ready_dataset
from app.core.config import Settings, get_settings
from app.core.exceptions import AppError
from app.core.ratelimit import limiter
from app.db.session import get_db
from app.models import Conversation, Dataset, Message, QueryHistory, SavedQuery, User
from app.schemas import DatasetOut, DatasetPatch
from app.services.file_service import ALLOWED, TABLE, IngestionError, ingest
from app.services.query_executor import execute_query
from app.services.schema_service import profile_dataset
from app.storage import storage

router = APIRouter(prefix="/datasets", tags=["datasets"])


def _sniff(path: Path, ext: str) -> None:
    """Check real content, not the filename or browser MIME type."""
    head = path.read_bytes()[:8192]
    ok = True
    if ext == ".parquet":
        ok = head[:4] == b"PAR1"
    elif ext == ".xlsx":
        ok = zipfile.is_zipfile(path) and "xl/workbook.xml" in zipfile.ZipFile(path).namelist()
    elif ext == ".csv":
        ok = b"\x00" not in head
    if not ok:
        raise AppError(400, "invalid_file", "File content does not match its extension.")


@router.post("/upload", response_model=DatasetOut, status_code=201)
def upload(file: UploadFile, db: Session = Depends(get_db), user: User = Depends(get_current_user),
           settings: Settings = Depends(get_settings)):
    limiter.check(user.id)
    original = Path(file.filename or "").name
    ext = Path(original).suffix.lower()
    if ext not in ALLOWED:
        raise AppError(400, "unsupported_file_type", "Only CSV, XLSX and Parquet files are supported.")
    key = uuid4().hex
    folder = storage.create(user.id, key)
    src, size, limit = folder / f"source{ext}", 0, settings.max_upload_size_mb * 1024 * 1024
    try:
        with src.open("wb") as out:
            while chunk := file.file.read(1024 * 1024):
                size += len(chunk)
                if size > limit:
                    raise AppError(413, "file_too_large",
                                   f"File exceeds {settings.max_upload_size_mb} MB.")
                out.write(chunk)
        _sniff(src, ext)
    except AppError:
        storage.delete(user.id, key)
        raise
    ds = Dataset(owner_id=user.id, name=Path(original).stem[:200] or "dataset",
                 original_filename=original[:255], storage_key=key, file_format=ext[1:],
                 file_size=size, status="processing")
    db.add(ds)
    db.commit()
    try:
        info = ingest(src, ext, folder / "data.duckdb", settings.max_columns)
    except IngestionError as e:
        ds.status, ds.error = "failed", str(e)[:500]
        db.commit()
        storage.delete(user.id, key)
        raise AppError(422, "ingestion_failed", str(e)[:300]) from e
    ds.status, ds.row_count, ds.column_count = "ready", info["row_count"], len(info["columns"])
    ds.schema_json = {"version": 1, "columns": info["columns"]}
    db.commit()
    return ds


@router.get("", response_model=list[DatasetOut])
def list_datasets(limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0),
                  db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = select(Dataset).where(Dataset.owner_id == user.id).order_by(Dataset.created_at.desc())
    return db.scalars(q.limit(limit).offset(offset)).all()


@router.get("/{dataset_id}", response_model=DatasetOut)
def get_dataset(dataset_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return get_owned(db, Dataset, dataset_id, user)


@router.get("/{dataset_id}/schema")
def schema(dataset_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ds = get_ready_dataset(db, dataset_id, user)
    return {"table": TABLE, **ds.schema_json}


def _db_path(ds: Dataset) -> Path:
    return storage.dataset_dir(ds.owner_id, ds.storage_key) / "data.duckdb"


@router.get("/{dataset_id}/preview")
def preview(dataset_id: str, rows: int = Query(20, ge=1, le=100), db: Session = Depends(get_db),
            user: User = Depends(get_current_user), settings: Settings = Depends(get_settings)):
    ds = get_ready_dataset(db, dataset_id, user)
    res = execute_query(_db_path(ds), f"SELECT * FROM {TABLE} LIMIT {int(rows)}", max_rows=rows,
                        timeout_s=settings.query_timeout_seconds,
                        memory_limit=settings.duckdb_memory_limit, threads=settings.duckdb_threads)
    return {"columns": res.columns, "rows": res.rows}


@router.get("/{dataset_id}/profile")
def profile(dataset_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user),
            settings: Settings = Depends(get_settings)):
    ds = get_ready_dataset(db, dataset_id, user)
    return {"row_count": ds.row_count, "column_count": ds.column_count,
            "columns": profile_dataset(_db_path(ds), ds.schema_json["columns"], settings)}


@router.patch("/{dataset_id}", response_model=DatasetOut)
def rename(dataset_id: str, body: DatasetPatch, db: Session = Depends(get_db),
           user: User = Depends(get_current_user)):
    ds = get_owned(db, Dataset, dataset_id, user)
    ds.name = body.name
    db.commit()
    return ds


@router.delete("/{dataset_id}", status_code=204)
def delete_dataset(dataset_id: str, db: Session = Depends(get_db),
                   user: User = Depends(get_current_user)):
    ds = get_owned(db, Dataset, dataset_id, user)
    conv_ids = select(Conversation.id).where(Conversation.dataset_id == ds.id)
    db.execute(delete(Message).where(Message.conversation_id.in_(conv_ids)))
    db.execute(delete(QueryHistory).where(QueryHistory.dataset_id == ds.id))
    db.execute(delete(SavedQuery).where(SavedQuery.dataset_id == ds.id))
    db.execute(delete(Conversation).where(Conversation.dataset_id == ds.id))
    db.delete(ds)
    db.commit()
    storage.delete(user.id, ds.storage_key)
    _ = shutil
