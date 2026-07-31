from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from app.models import Base

# Imported for its side effect: the `project` relationship below resolves the
# "Project" mapper by name, so that class must be registered on the shared
# declarative Base whenever Document is used (see ADR-006).
from app.models.project import Project  # noqa: F401


class Document(Base):
    """A file stored in the document repository.

    The row holds *metadata only*: the binary lives in a storage backend
    (see app/storage/) and is addressed by `storage_key`. Keeping the two
    apart is what allows the local filesystem backend to be swapped for S3
    or Azure Blob Storage without a schema change.
    """

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)

    # --- Business metadata ---------------------------------------------
    title = Column(String(255), nullable=False)
    description = Column(Text)
    document_type = Column(String(50), nullable=False, index=True)

    # Association. Both are optional: a document may be filed against a
    # project, against a customer only, or be organisation-wide.
    project_id = Column(Integer, ForeignKey("projects.id"), index=True)
    customer = Column(String(255), index=True)

    # No authentication yet, so this is a caller-supplied label. It becomes
    # a real users.id foreign key when auth lands.
    uploaded_by = Column(String(255))

    # --- File metadata ---------------------------------------------------
    filename = Column(String(255), nullable=False)  # original client filename
    content_type = Column(String(100), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    # SHA-256 of the file contents: integrity checking today, and the natural
    # cache key for "has this content already been embedded?" later.
    content_hash = Column(String(64), nullable=False, index=True)

    # --- Storage location -------------------------------------------------
    storage_backend = Column(String(30), nullable=False, default="local")
    storage_key = Column(String(500), nullable=False, unique=True)

    # --- Lifecycle --------------------------------------------------------
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    # Soft delete: documents are audit-relevant, so a delete hides the record
    # rather than destroying it. Blobs are reclaimed by app/purge_documents.py.
    deleted_at = Column(DateTime(timezone=True), index=True)

    # --- AI & Embedding Metadata ---------------------------------------------------
    # Status of embedding pipeline: queued, processing, completed, failed
    embedding_status = Column(String(20), nullable=False, default="queued", index=True)
    # Which embedding model was used (text-embedding-3-small, etc.)
    embedding_model = Column(String(50), default="text-embedding-3-small")
    # Total tokens in all chunks (for cost tracking)
    token_count = Column(Integer)
    # Cost in USD for generating embeddings
    embedding_cost = Column(Float)
    # Error message if embedding failed
    embedding_error = Column(Text)
    # When embeddings were completed
    embedded_at = Column(DateTime(timezone=True), index=True)

    project = relationship("Project", lazy="joined")
