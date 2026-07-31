from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func, Numeric, JSON
from app.models import Base


class DocumentEmbedding(Base):
    """A vector embedding for a chunk of a document.

    One document may have many chunks; each chunk is independently embedded
    and stored here with its vector (pgvector type). This allows semantic
    search to find relevant document sections.
    """

    __tablename__ = "document_embeddings"

    id = Column(Integer, primary_key=True)

    # Document this chunk belongs to
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)

    # Position in document (0, 1, 2, ...)
    chunk_index = Column(Integer, nullable=False)

    # Raw text of this chunk
    chunk_text = Column(Text, nullable=False)

    # Embedding vector (1536 dimensions for text-embedding-3-small)
    # PostgreSQL pgvector extension stores this as a vector type
    embedding = Column(Text, nullable=False)  # JSON string of float array; can query via pgvector

    # Approximate token count in this chunk (for cost tracking)
    token_count = Column(Integer)

    # Additional info about this chunk (page number, section, etc.)
    chunk_metadata = Column(JSON)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        # Ensure unique chunk index per document
        # uniqueconstraint(document_id, chunk_index),
    )


class EmbeddingOperation(Base):
    """Audit trail of embedding operations.

    Tracks every step of the embedding pipeline (extraction, chunking, API calls)
    for debugging, cost tracking, and monitoring.
    """

    __tablename__ = "embedding_operations"

    id = Column(Integer, primary_key=True)

    # Document being processed
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)

    # What operation: extraction, chunking, embedding, indexing
    operation_type = Column(String(50), nullable=False, index=True)

    # Status: started, completed, failed
    status = Column(String(20), nullable=False, index=True)

    # How long did this step take (milliseconds)
    duration_ms = Column(Integer)

    # Tokens used in this operation (if applicable, e.g., for embeddings)
    tokens_used = Column(Integer)

    # Cost in USD (for OpenAI API calls)
    cost_usd = Column(Numeric(10, 6))

    # Error message if status is 'failed'
    error_message = Column(Text)

    # Additional details (JSON)
    operation_metadata = Column(JSON)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
