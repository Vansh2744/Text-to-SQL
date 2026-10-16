import shutil
from pathlib import Path

from app.core.config import get_settings


class LocalStorage:
    """Local-disk storage. Paths are built only from server-generated ids, never from filenames.
    Swap this class for an S3-compatible one in production (same three methods)."""

    def __init__(self, root: str):
        self.root = Path(root).resolve()

    def dataset_dir(self, owner_id: str, key: str) -> Path:
        return self.root / owner_id / key

    def create(self, owner_id: str, key: str) -> Path:
        d = self.dataset_dir(owner_id, key)
        d.mkdir(parents=True, exist_ok=False)
        return d

    def delete(self, owner_id: str, key: str) -> None:
        shutil.rmtree(self.dataset_dir(owner_id, key), ignore_errors=True)


storage = LocalStorage(get_settings().upload_dir)
