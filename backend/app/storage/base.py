"""Storage backend contract for document binaries.

The service layer only ever talks to this interface, never to the filesystem
directly. Adding S3 / Azure Blob / GCS later means implementing these four
methods and registering the class in app/storage/__init__.py — no changes to
the API, service or database layers.
"""

from abc import ABC, abstractmethod
from typing import BinaryIO, Iterable


class StorageError(RuntimeError):
    """Raised when the storage backend cannot complete an operation."""


class DocumentStorage(ABC):
    """Content-addressed blob store keyed by an opaque string."""

    #: Value written to documents.storage_backend for objects this backend owns.
    name: str

    @abstractmethod
    def save(self, key: str, chunks: Iterable[bytes]) -> int:
        """Persist `chunks` under `key`. Returns the number of bytes written.

        Implementations must be atomic from a reader's point of view: a key
        either does not exist, or resolves to the complete object.
        """

    @abstractmethod
    def open(self, key: str) -> BinaryIO:
        """Return a readable binary stream for `key`.

        The caller is responsible for closing the stream.
        """

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Remove `key`. Returns True if an object was removed."""

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Return True if `key` resolves to a stored object."""
