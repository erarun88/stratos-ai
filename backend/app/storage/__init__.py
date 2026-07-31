"""Document storage backends.

`get_document_storage()` is the single place that decides which backend the
application uses, based on DOCUMENT_STORAGE_BACKEND. Callers depend on the
DocumentStorage interface only.
"""

from functools import lru_cache

from app.config import settings
from app.storage.base import DocumentStorage, StorageError
from app.storage.local import LocalDocumentStorage

__all__ = ["DocumentStorage", "StorageError", "LocalDocumentStorage", "get_document_storage"]


@lru_cache(maxsize=1)
def get_document_storage() -> DocumentStorage:
    """Return the configured storage backend (created once per process)."""
    backend = settings.document_storage_backend.lower()

    if backend == "local":
        return LocalDocumentStorage(settings.document_storage_root)

    # Future backends (s3, azure_blob, gcs) register here.
    raise StorageError(f"Unsupported document storage backend: {backend!r}")
