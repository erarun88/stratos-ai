"""Business logic for the Document Management module.

Responsibilities kept here (and out of the routers):
  * validating uploads (type, magic number, size) before anything is stored
  * generating opaque, collision-free storage keys
  * streaming file contents to the storage backend while hashing them
  * keeping the metadata row and the stored blob consistent
  * querying, filtering and paginating the repository

Nothing in this module imports FastAPI, so the same logic can be reused by a
background worker or the future AI ingestion pipeline.
"""

import hashlib
import logging
import re
import unicodedata
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO, Iterator, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.document import Document
from app.models.project import Project
from app.schemas import (
    DocumentCreate,
    DocumentResponse,
    DocumentSortField,
    DocumentUpdate,
    SortOrder,
)
from app.services.exceptions import (
    DocumentNotFoundError,
    DocumentTooLargeError,
    DocumentValidationError,
    RelatedResourceNotFoundError,
    UnsupportedFileTypeError,
)
from app.storage import get_document_storage

logger = logging.getLogger(__name__)

# First bytes of every valid PDF. Checked so a renamed .exe cannot be stored
# just because the client claimed "application/pdf".
PDF_MAGIC = b"%PDF-"

MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 20

_UNSAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9._ -]+")
_LIKE_SPECIAL_CHARS = re.compile(r"([\\%_])")

_SORT_COLUMNS = {
    DocumentSortField.created_at: Document.created_at,
    DocumentSortField.title: Document.title,
    DocumentSortField.file_size: Document.file_size,
    DocumentSortField.document_type: Document.document_type,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def sanitize_filename(filename: str) -> str:
    """Reduce a client-supplied filename to something safe to store and echo.

    The result is only ever used as *display* metadata and in the
    Content-Disposition header — never to build a filesystem path.
    """
    # Take the basename only: strips "../" and Windows "C:\dir\" prefixes.
    base = Path(filename.replace("\\", "/")).name
    normalized = unicodedata.normalize("NFKD", base)
    cleaned = _UNSAFE_FILENAME_CHARS.sub("_", normalized).strip(" .")
    if not cleaned:
        cleaned = "document.pdf"
    return cleaned[:255]


def _escape_like(value: str) -> str:
    """Escape LIKE wildcards so user input is matched literally."""
    return _LIKE_SPECIAL_CHARS.sub(r"\\\1", value)


def _build_storage_key(project_id: Optional[int], extension: str) -> str:
    """Generate an opaque, unguessable, collision-free storage key.

    Layout: <scope>/<yyyy>/<mm>/<uuid4><ext> — date-partitioned so a single
    directory never accumulates millions of entries, and prefixed by project
    so a per-project lifecycle policy is possible later.
    """
    now = datetime.now(timezone.utc)
    scope = f"project-{project_id}" if project_id else "unassigned"
    return f"{scope}/{now:%Y}/{now:%m}/{uuid.uuid4().hex}{extension}"


def _validate_project(session: Session, project_id: Optional[int]) -> Optional[Project]:
    if project_id is None:
        return None
    project = session.get(Project, project_id)
    if not project:
        raise RelatedResourceNotFoundError(f"Project with id {project_id} does not exist")
    return project


def _validate_upload(filename: Optional[str], content_type: Optional[str]) -> str:
    """Validate the declared file type. Returns the normalised extension."""
    if not filename or not filename.strip():
        raise DocumentValidationError("A file with a filename is required")

    extension = Path(filename).suffix.lower()
    if extension not in settings.allowed_document_extensions:
        allowed = ", ".join(sorted(settings.allowed_document_extensions))
        raise UnsupportedFileTypeError(f"Unsupported file extension. Allowed: {allowed}")

    # Content-Type may carry parameters, e.g. "application/pdf; charset=binary".
    declared = (content_type or "").split(";")[0].strip().lower()
    if declared not in settings.allowed_document_content_types:
        allowed = ", ".join(sorted(settings.allowed_document_content_types))
        raise UnsupportedFileTypeError(f"Unsupported content type. Allowed: {allowed}")

    return extension


class _HashingChunker:
    """Yields the upload in chunks while hashing and size-checking it.

    Enforcing the limit here — rather than trusting Content-Length — means an
    oversized or lying client is stopped mid-stream, before it can fill the
    disk.
    """

    def __init__(self, stream: BinaryIO, first_chunk: bytes, max_bytes: int, chunk_size: int):
        self._stream = stream
        self._first_chunk = first_chunk
        self._max_bytes = max_bytes
        self._chunk_size = chunk_size
        self._hasher = hashlib.sha256()
        self.size = 0

    def __iter__(self) -> Iterator[bytes]:
        chunk = self._first_chunk
        while chunk:
            self.size += len(chunk)
            if self.size > self._max_bytes:
                raise DocumentTooLargeError(
                    f"File exceeds the maximum allowed size of "
                    f"{settings.max_document_size_mb} MB"
                )
            self._hasher.update(chunk)
            yield chunk
            chunk = self._stream.read(self._chunk_size)

    @property
    def content_hash(self) -> str:
        return self._hasher.hexdigest()


def to_response(document: Document) -> DocumentResponse:
    """Map an ORM row to the API representation."""
    return DocumentResponse(
        id=document.id,
        title=document.title,
        description=document.description,
        document_type=document.document_type,
        project_id=document.project_id,
        project_name=document.project.name if document.project else None,
        customer=document.customer,
        uploaded_by=document.uploaded_by,
        filename=document.filename,
        content_type=document.content_type,
        file_size=document.file_size,
        content_hash=document.content_hash,
        storage_backend=document.storage_backend,
        created_at=document.created_at,
        updated_at=document.updated_at,
        embedding_status=document.embedding_status,
        embedding_model=document.embedding_model,
        token_count=document.token_count,
        embedding_cost=document.embedding_cost,
        embedded_at=document.embedded_at,
        embedding_error=document.embedding_error,
    )


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def create_document(
    session: Session,
    *,
    metadata: DocumentCreate,
    upload_stream: BinaryIO,
    filename: Optional[str],
    content_type: Optional[str],
) -> Document:
    """Validate, store and register a new document.

    Order of operations: validate cheaply, then stream the blob to storage,
    then commit the metadata row. If the commit fails the blob is removed, so
    storage never accumulates objects with no owning row.
    """
    extension = _validate_upload(filename, content_type)
    project = _validate_project(session, metadata.project_id)

    storage = get_document_storage()

    # Read the first chunk up front so the magic number can be checked before
    # a single byte is written to storage.
    first_chunk = upload_stream.read(settings.file_chunk_size)
    if not first_chunk:
        raise DocumentValidationError("The uploaded file is empty")
    if not first_chunk.startswith(PDF_MAGIC):
        raise UnsupportedFileTypeError("The uploaded file is not a valid PDF")

    storage_key = _build_storage_key(metadata.project_id, extension)
    chunker = _HashingChunker(
        upload_stream,
        first_chunk,
        settings.max_document_size_bytes,
        settings.file_chunk_size,
    )
    storage.save(storage_key, chunker)

    # A document filed against a project inherits the project's customer
    # unless the caller supplied one explicitly.
    customer = metadata.customer or (project.customer if project else None)

    document = Document(
        title=metadata.title,
        description=metadata.description,
        document_type=metadata.document_type.value,
        project_id=metadata.project_id,
        customer=customer,
        uploaded_by=metadata.uploaded_by,
        filename=sanitize_filename(filename or "document.pdf"),
        content_type="application/pdf",
        file_size=chunker.size,
        content_hash=chunker.content_hash,
        storage_backend=storage.name,
        storage_key=storage_key,
    )

    try:
        session.add(document)
        session.commit()
    except Exception:
        session.rollback()
        # Compensating action: the row never existed, so neither should the blob.
        try:
            storage.delete(storage_key)
        except Exception:  # pragma: no cover - best-effort cleanup
            logger.exception("Orphaned blob left in storage: key=%s", storage_key)
        raise

    session.refresh(document)
    logger.info(
        "Document uploaded: id=%s title=%r project_id=%s size=%s hash=%s",
        document.id,
        document.title,
        document.project_id,
        document.file_size,
        document.content_hash[:12],
    )
    return document


def update_document(session: Session, document_id: int, payload: DocumentUpdate) -> Document:
    """Apply a partial metadata update. The stored file is never modified."""
    document = get_document(session, document_id)
    fields = payload.model_dump(exclude_unset=True)

    if "project_id" in fields:
        _validate_project(session, fields["project_id"])

    for field, value in fields.items():
        if field == "document_type" and value is not None:
            value = value.value if hasattr(value, "value") else value
        setattr(document, field, value)

    session.commit()
    session.refresh(document)
    logger.info("Document metadata updated: id=%s fields=%s", document.id, sorted(fields))
    return document


def delete_document(session: Session, document_id: int) -> None:
    """Soft-delete a document.

    Documents are contractual and audit-relevant, so the record is hidden
    rather than destroyed; the blob is reclaimed later by
    `python -m app.purge_documents`. This also keeps a future "restore" or
    versioning feature cheap to add.
    """
    document = get_document(session, document_id)
    document.deleted_at = datetime.now(timezone.utc)
    session.commit()
    logger.info("Document soft-deleted: id=%s storage_key=%s", document_id, document.storage_key)


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------


def get_document(session: Session, document_id: int) -> Document:
    document = session.get(Document, document_id)
    if not document or document.deleted_at is not None:
        raise DocumentNotFoundError(f"Document with id {document_id} not found")
    return document


def list_documents(
    session: Session,
    *,
    search: Optional[str] = None,
    document_type: Optional[str] = None,
    project_id: Optional[int] = None,
    customer: Optional[str] = None,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    sort_by: DocumentSortField = DocumentSortField.created_at,
    sort_order: SortOrder = SortOrder.desc,
) -> tuple[list[Document], int]:
    """Return one page of documents plus the total number of matches."""
    page = max(page, 1)
    page_size = min(max(page_size, 1), MAX_PAGE_SIZE)

    conditions = [Document.deleted_at.is_(None)]

    if search and search.strip():
        pattern = f"%{_escape_like(search.strip())}%"
        conditions.append(
            or_(
                Document.title.ilike(pattern, escape="\\"),
                Document.filename.ilike(pattern, escape="\\"),
                Document.description.ilike(pattern, escape="\\"),
                Document.customer.ilike(pattern, escape="\\"),
            )
        )
    if document_type:
        conditions.append(Document.document_type == document_type)
    if project_id is not None:
        conditions.append(Document.project_id == project_id)
    if customer and customer.strip():
        conditions.append(
            Document.customer.ilike(f"%{_escape_like(customer.strip())}%", escape="\\")
        )

    total = session.execute(
        select(func.count(Document.id)).where(*conditions)
    ).scalar_one()

    column = _SORT_COLUMNS[sort_by]
    ordering = column.asc() if sort_order is SortOrder.asc else column.desc()

    statement = (
        select(Document)
        .where(*conditions)
        # id is a deterministic tie-breaker, so paging never repeats or skips
        # rows that share a sort value.
        .order_by(ordering, Document.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    documents = session.execute(statement).unique().scalars().all()
    return list(documents), total


def open_document_stream(document: Document) -> BinaryIO:
    """Open the stored blob for download.

    Opened eagerly (rather than inside the streaming generator) so a missing
    blob fails before response headers are sent and can be reported properly.
    """
    storage = get_document_storage()
    return storage.open(document.storage_key)


def iter_stream(handle: BinaryIO) -> Iterator[bytes]:
    """Yield an open blob's contents in chunks, closing it at the end."""
    try:
        while True:
            chunk = handle.read(settings.file_chunk_size)
            if not chunk:
                break
            yield chunk
    finally:
        handle.close()
