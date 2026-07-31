"""Local filesystem implementation of the DocumentStorage contract.

Suitable for development and single-node deployments. Every path is resolved
and checked against the configured root, so a malicious or malformed key can
never escape the storage directory.
"""

import logging
import os
from pathlib import Path
from typing import BinaryIO, Iterable

from app.storage.base import DocumentStorage, StorageError

logger = logging.getLogger(__name__)


class LocalDocumentStorage(DocumentStorage):
    name = "local"

    def __init__(self, root: Path):
        self._root = Path(root).resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    @property
    def root(self) -> Path:
        return self._root

    def _resolve(self, key: str) -> Path:
        """Map a storage key to an absolute path inside the storage root.

        Rejects absolute paths and any key that would traverse outside the
        root (e.g. "../../etc/passwd").
        """
        if not key or key.startswith("/") or "\x00" in key:
            raise StorageError(f"Invalid storage key: {key!r}")

        path = (self._root / key).resolve()
        if path != self._root and self._root not in path.parents:
            raise StorageError(f"Storage key escapes the storage root: {key!r}")
        return path

    def save(self, key: str, chunks: Iterable[bytes]) -> int:
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write to a temporary sibling first, then rename. os.replace() is
        # atomic on POSIX and Windows, so readers never observe a half-written
        # object and a crash mid-upload leaves only a .part file behind.
        temp_path = path.with_suffix(path.suffix + ".part")
        written = 0
        try:
            with open(temp_path, "wb") as handle:
                for chunk in chunks:
                    handle.write(chunk)
                    written += len(chunk)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, path)
        except OSError as exc:
            temp_path.unlink(missing_ok=True)
            logger.exception("Failed to write document to local storage: key=%s", key)
            raise StorageError(f"Could not store object {key!r}") from exc
        except BaseException:
            # The producer failed (e.g. the upload exceeded the size limit).
            # Clean up the partial write and let the original error surface
            # unchanged so the caller can map it to the right response.
            temp_path.unlink(missing_ok=True)
            raise

        return written

    def open(self, key: str) -> BinaryIO:
        path = self._resolve(key)
        if not path.is_file():
            raise StorageError(f"Object not found in storage: {key!r}")
        return open(path, "rb")

    def delete(self, key: str) -> bool:
        path = self._resolve(key)
        try:
            path.unlink()
        except FileNotFoundError:
            return False
        except OSError as exc:
            logger.exception("Failed to delete document from local storage: key=%s", key)
            raise StorageError(f"Could not delete object {key!r}") from exc
        return True

    def exists(self, key: str) -> bool:
        try:
            return self._resolve(key).is_file()
        except StorageError:
            return False
