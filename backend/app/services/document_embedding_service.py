"""Document embedding orchestration service.

End-to-end pipeline: extract text → chunk → embed → index.
"""

import logging
import time
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models.document import Document
from app.models.embedding import DocumentEmbedding, EmbeddingOperation
from app.storage import get_document_storage
from app.services.pdf_service import extract_text_from_pdf, PdfExtractionError
from app.services.chunking_service import create_semantic_chunks
from app.services.embedding_service import (
    generate_embeddings,
    embedding_to_json,
    EmbeddingError,
)

logger = logging.getLogger(__name__)


class DocumentEmbeddingError(Exception):
    """Raised when document embedding pipeline fails."""
    pass


def _log_operation(
    session: Session,
    document_id: int,
    operation_type: str,
    status: str,
    duration_ms: int = None,
    tokens_used: int = None,
    cost_usd: float = None,
    error_message: str = None,
    metadata: dict = None,
) -> None:
    """Log an embedding operation to the audit trail."""
    try:
        op = EmbeddingOperation(
            document_id=document_id,
            operation_type=operation_type,
            status=status,
            duration_ms=duration_ms,
            tokens_used=tokens_used,
            cost_usd=cost_usd,
            error_message=error_message,
            operation_metadata=metadata,
        )
        session.add(op)
        session.commit()
    except Exception as e:
        logger.error(f"Failed to log operation: {e}")


def embed_document(session: Session, document_id: int) -> bool:
    """Embed a document: extract → chunk → embed → store.

    Args:
        session: Database session
        document_id: ID of document to embed

    Returns:
        True if embedding succeeded, False otherwise
    """
    doc = session.get(Document, document_id)
    if not doc:
        logger.error(f"Document {document_id} not found")
        return False

    if doc.deleted_at:
        logger.warning(f"Skipping deleted document {document_id}")
        return False

    logger.info(f"Starting embedding for document {document_id}")

    try:
        # Mark as processing
        doc.embedding_status = "processing"
        session.commit()

        # Step 1: Extract text from PDF
        logger.info(f"[{document_id}] Extracting text...")
        extract_start = time.time()

        storage = get_document_storage()
        pdf_file = storage.open(doc.storage_key)
        try:
            pdf_bytes = pdf_file.read()
        finally:
            pdf_file.close()
        text = extract_text_from_pdf(pdf_bytes)

        extract_duration = int((time.time() - extract_start) * 1000)
        _log_operation(
            session, document_id, "extraction", "completed",
            duration_ms=extract_duration, metadata={"char_count": len(text)}
        )

        # Step 2: Chunk text
        logger.info(f"[{document_id}] Creating semantic chunks...")
        chunk_start = time.time()

        chunks = create_semantic_chunks(
            text,
            max_chunk_tokens=settings.embedding_max_chunk_tokens,
            min_chunk_tokens=settings.embedding_min_chunk_tokens,
        )

        if not chunks:
            raise DocumentEmbeddingError("No chunks created from document text")

        chunk_duration = int((time.time() - chunk_start) * 1000)
        _log_operation(
            session, document_id, "chunking", "completed",
            duration_ms=chunk_duration,
            metadata={"chunk_count": len(chunks)}
        )

        # Step 3: Generate embeddings
        logger.info(f"[{document_id}] Generating embeddings for {len(chunks)} chunks...")
        embed_start = time.time()

        chunk_texts = [c["text"] for c in chunks]
        result = generate_embeddings(chunk_texts)

        embeddings = result["embeddings"]
        total_tokens = result["total_tokens"]
        total_cost = result["total_cost"]

        embed_duration = int((time.time() - embed_start) * 1000)
        _log_operation(
            session, document_id, "embedding", "completed",
            duration_ms=embed_duration,
            tokens_used=total_tokens,
            cost_usd=total_cost,
        )

        # Step 4: Store embeddings
        logger.info(f"[{document_id}] Storing {len(embeddings)} embeddings...")
        store_start = time.time()

        for chunk_idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_embedding = DocumentEmbedding(
                document_id=document_id,
                chunk_index=chunk_idx,
                chunk_text=chunk["text"],
                embedding=embedding_to_json(embedding),
                token_count=chunk["token_count"],
                chunk_metadata={
                    "chunk_size": len(chunk["text"]),
                }
            )
            session.add(chunk_embedding)

        # Update document status
        doc.embedding_status = "completed"
        doc.embedding_model = settings.embedding_model
        doc.token_count = total_tokens
        doc.embedding_cost = total_cost
        doc.embedded_at = datetime.utcnow()
        doc.embedding_error = None

        session.commit()

        store_duration = int((time.time() - store_start) * 1000)
        _log_operation(
            session, document_id, "indexing", "completed",
            duration_ms=store_duration,
        )

        total_duration = time.time() - extract_start
        logger.info(
            f"✓ Document {document_id} successfully embedded: "
            f"{len(chunks)} chunks, {total_tokens} tokens, ${total_cost:.4f}, {total_duration:.1f}s"
        )
        return True

    except Exception as e:
        logger.error(f"✗ Failed to embed document {document_id}: {e}", exc_info=True)

        # Mark as failed
        doc.embedding_status = "failed"
        doc.embedding_error = str(e)
        session.commit()

        _log_operation(
            session, document_id, "embedding", "failed",
            error_message=str(e),
        )

        return False


def reset_document_embedding(session: Session, document_id: int) -> None:
    """Reset embedding status for a document to retry.

    Useful for manually retrying failed embeddings.
    """
    doc = session.get(Document, document_id)
    if not doc:
        raise DocumentEmbeddingError(f"Document {document_id} not found")

    doc.embedding_status = "queued"
    doc.embedding_error = None
    session.commit()
    logger.info(f"Reset embedding status for document {document_id}")


def get_embedding_stats(session: Session) -> dict:
    """Get statistics about document embeddings."""
    from sqlalchemy import func, select

    # Count by status
    status_counts = {}
    for status in ["queued", "processing", "completed", "failed"]:
        count = session.execute(
            select(func.count(Document.id)).where(Document.embedding_status == status)
        ).scalar() or 0
        status_counts[status] = count

    # Total stats
    total_tokens = (
        session.execute(select(func.sum(Document.token_count))).scalar() or 0
    )
    total_cost = (
        session.execute(select(func.sum(Document.embedding_cost))).scalar() or 0.0
    )

    return {
        "status_counts": status_counts,
        "total_tokens": total_tokens,
        "total_cost": float(total_cost),
    }
