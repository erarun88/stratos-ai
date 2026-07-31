"""HTTP API for the Document Management module.

This layer is deliberately thin: parse and validate the request, delegate to
`app.services.document_service`, translate domain errors into status codes.
"""

import logging
from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.database import get_session
from app.models.project import Project
from app.schemas import (
    DocumentCreate,
    DocumentListResponse,
    DocumentResponse,
    DocumentSortField,
    DocumentType,
    DocumentUpdate,
    SortOrder,
)
from app.services import document_service
from app.services.exceptions import (
    DocumentNotFoundError,
    DocumentTooLargeError,
    DocumentValidationError,
    RelatedResourceNotFoundError,
    UnsupportedFileTypeError,
)
from app.storage import StorageError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])
project_documents_router = APIRouter(prefix="/projects", tags=["Documents"])


def _optional_int(value: Optional[str], field: str) -> Optional[int]:
    """Parse an optional integer form field, treating "" as not provided.

    HTML forms submit empty strings for cleared inputs; accepting that as
    "no value" avoids a confusing 422 for a perfectly ordinary request.
    """
    if value is None or not value.strip():
        return None
    try:
        return int(value)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=[{"loc": ["body", field], "msg": f"{field} must be an integer"}],
        )


def _validation_error(exc: ValidationError) -> HTTPException:
    """Convert a Pydantic error into FastAPI's 422 response shape."""
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=[
            {"loc": list(error["loc"]), "msg": error["msg"]} for error in exc.errors()
        ],
    )


def _content_disposition(filename: str) -> str:
    """Build an RFC 6266 Content-Disposition value.

    Sends both the ASCII fallback and the UTF-8 form so non-ASCII filenames
    survive, and quotes the value so a crafted filename cannot inject headers.
    """
    ascii_name = filename.encode("ascii", "ignore").decode("ascii") or "document.pdf"
    return f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(filename)}"


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def upload_document(
    file: UploadFile = File(..., description="PDF file to upload"),
    title: str = Form(..., description="Human-readable document title"),
    description: Optional[str] = Form(None),
    document_type: DocumentType = Form(DocumentType.other),
    project_id: Optional[str] = Form(None, description="Associated project id"),
    customer: Optional[str] = Form(
        None, description="Customer name; defaults to the project's customer"
    ),
    uploaded_by: Optional[str] = Form(None, description="Uploader name (until auth exists)"),
    session: Session = Depends(get_session),
):
    """Upload a PDF and register its metadata."""
    try:
        metadata = DocumentCreate(
            title=title,
            description=description,
            document_type=document_type,
            project_id=_optional_int(project_id, "project_id"),
            customer=customer,
            uploaded_by=uploaded_by,
        )
    except ValidationError as exc:
        raise _validation_error(exc)

    try:
        document = document_service.create_document(
            session,
            metadata=metadata,
            upload_stream=file.file,
            filename=file.filename,
            content_type=file.content_type,
        )
    except UnsupportedFileTypeError as exc:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(exc))
    except DocumentTooLargeError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(exc)
        )
    except (DocumentValidationError, RelatedResourceNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except StorageError as exc:
        logger.exception("Storage failure while uploading document")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Document storage is unavailable. Please try again.",
        ) from exc
    finally:
        file.file.close()

    return document_service.to_response(document)


@router.patch("/{document_id}", response_model=DocumentResponse)
def update_document(
    document_id: int,
    payload: DocumentUpdate,
    session: Session = Depends(get_session),
):
    """Update document metadata. The stored file itself is immutable."""
    try:
        document = document_service.update_document(session, document_id, payload)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except RelatedResourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return document_service.to_response(document)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: int, session: Session = Depends(get_session)):
    """Delete a document (soft delete — the record is retained for audit)."""
    try:
        document_service.delete_document(session, document_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------


@router.get("", response_model=DocumentListResponse)
def list_documents(
    search: Optional[str] = Query(
        None, description="Free-text match on title, filename, description or customer"
    ),
    document_type: Optional[DocumentType] = Query(None),
    project_id: Optional[int] = Query(None, ge=1),
    customer: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(
        document_service.DEFAULT_PAGE_SIZE, ge=1, le=document_service.MAX_PAGE_SIZE
    ),
    sort_by: DocumentSortField = Query(DocumentSortField.created_at),
    sort_order: SortOrder = Query(SortOrder.desc),
    session: Session = Depends(get_session),
):
    """Search, filter and page through the document repository."""
    documents, total = document_service.list_documents(
        session,
        search=search,
        document_type=document_type.value if document_type else None,
        project_id=project_id,
        customer=customer,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return DocumentListResponse(
        items=[document_service.to_response(doc) for doc in documents],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: int, session: Session = Depends(get_session)):
    """Fetch a single document's metadata."""
    try:
        document = document_service.get_document(session, document_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return document_service.to_response(document)


@router.get("/{document_id}/download")
def download_document(document_id: int, session: Session = Depends(get_session)):
    """Stream the stored file back to the client."""
    try:
        document = document_service.get_document(session, document_id)
        # Opened before the response starts so a storage failure is still a
        # clean HTTP error rather than a truncated download.
        handle = document_service.open_document_stream(document)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except StorageError:
        # Metadata exists but the blob does not — a real inconsistency worth
        # surfacing in the logs rather than a bare 500.
        logger.error("Missing blob for document id=%s", document_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The stored file for this document could not be found",
        )

    return StreamingResponse(
        document_service.iter_stream(handle),
        media_type=document.content_type,
        headers={
            "Content-Disposition": _content_disposition(document.filename),
            "Content-Length": str(document.file_size),
            # Stop browsers from re-interpreting the payload as another type.
            "X-Content-Type-Options": "nosniff",
        },
    )


@project_documents_router.get(
    "/{project_id}/documents", response_model=DocumentListResponse
)
def list_project_documents(
    project_id: int,
    search: Optional[str] = Query(None),
    document_type: Optional[DocumentType] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(
        document_service.DEFAULT_PAGE_SIZE, ge=1, le=document_service.MAX_PAGE_SIZE
    ),
    session: Session = Depends(get_session),
):
    """List the documents filed against a project."""
    if not session.get(Project, project_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found",
        )

    documents, total = document_service.list_documents(
        session,
        search=search,
        document_type=document_type.value if document_type else None,
        project_id=project_id,
        page=page,
        page_size=page_size,
    )

    return DocumentListResponse(
        items=[document_service.to_response(doc) for doc in documents],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )

# --- Embedding Status Endpoints (AI Features) ---

from pydantic import BaseModel
from app.models.document import Document
from app.models.embedding import DocumentEmbedding
from sqlalchemy import select, func


class EmbeddingStatus(BaseModel):
    """Status of document embedding."""
    document_id: int
    embedding_status: str
    embedding_model: Optional[str]
    chunks_count: Optional[int]
    token_count: Optional[int]
    embedding_cost_usd: Optional[float]
    embedded_at: Optional[str]
    error: Optional[str]


@router.get("/{document_id}/embedding-status", response_model=EmbeddingStatus)
def get_embedding_status(
    document_id: int,
    session: Session = Depends(get_session),
):
    """Get embedding status of a document.
    
    Returns how many chunks were created, token count, processing cost, 
    and any errors that occurred.
    """
    doc = session.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    chunk_count = session.execute(
        select(func.count())
        .select_from(DocumentEmbedding)
        .where(DocumentEmbedding.document_id == document_id)
    ).scalar() or 0

    return EmbeddingStatus(
        document_id=doc.id,
        embedding_status=doc.embedding_status,
        embedding_model=doc.embedding_model,
        chunks_count=chunk_count if chunk_count > 0 else None,
        token_count=doc.token_count,
        embedding_cost_usd=doc.embedding_cost,
        embedded_at=doc.embedded_at.isoformat() if doc.embedded_at else None,
        error=doc.embedding_error,
    )
