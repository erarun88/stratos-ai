"""Semantic search endpoints.

Enables users to search documents by semantic meaning rather than keyword matching.
Uses vector embeddings and pgvector similarity search.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text, select
from sqlalchemy.orm import Session

from app.database import engine
from app.models.document import Document
from app.models.embedding import DocumentEmbedding
from app.services.embedding_service import generate_embeddings, embedding_from_json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


class SearchResult(BaseModel):
    """A single search result."""
    document_id: int
    document_title: str
    chunk_index: int
    chunk_text: str
    similarity_score: float = Field(description="Cosine similarity 0.0-1.0")
    metadata: dict = None


class SemanticSearchRequest(BaseModel):
    """Semantic search request."""
    query: str = Field(description="Search query")
    limit: int = Field(default=10, ge=1, le=50, description="Number of results")
    threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score (0.0-1.0)"
    )
    project_id: Optional[int] = Field(default=None, description="Filter by project")
    customer: Optional[str] = Field(default=None, description="Filter by customer")
    document_type: Optional[str] = Field(default=None, description="Filter by document type")


class SemanticSearchResponse(BaseModel):
    """Semantic search response."""
    query: str
    results: List[SearchResult]
    execution_time_ms: float = Field(description="Query execution time")
    total_results: int = Field(description="Total results (may be limited)")


@router.post("/semantic", response_model=SemanticSearchResponse)
def semantic_search(
    request: SemanticSearchRequest,
    session: Session = Depends(lambda: Session(engine)),
) -> SemanticSearchResponse:
    """Search documents using semantic similarity.

    Generates an embedding for the query and finds the most similar document chunks
    using vector similarity search (cosine distance).

    Args:
        request: Search parameters
        session: Database session

    Returns:
        Matching document chunks ranked by similarity
    """
    import time
    start_time = time.time()

    try:
        # Generate embedding for the query
        try:
            embedding_result = generate_embeddings([request.query])
            query_embedding = embedding_result["embeddings"][0]
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to generate search embedding"
            )

        # Build vector search query with similarity threshold and optional filters
        # Note: This uses pgvector's cosine distance operator (<=>)
        # Lower distance = higher similarity
        query_sql = f"""
            SELECT
                de.document_id,
                d.title,
                de.chunk_index,
                de.chunk_text,
                (1 - (de.embedding <=> '{embedding_result["embeddings"][0]}')) as similarity_score,
                de.metadata
            FROM document_embeddings de
            JOIN documents d ON de.document_id = d.id
            WHERE d.deleted_at IS NULL
                AND d.embedding_status = 'completed'
                AND (1 - (de.embedding <=> '{embedding_result["embeddings"][0]}')) >= {request.threshold}
        """

        # Add optional filters
        if request.project_id is not None:
            query_sql += f" AND d.project_id = {request.project_id}"
        if request.customer:
            query_sql += f" AND d.customer = '{request.customer}'"
        if request.document_type:
            query_sql += f" AND d.document_type = '{request.document_type}'"

        query_sql += f"""
            ORDER BY similarity_score DESC
            LIMIT {request.limit}
        """

        # Execute the search
        raw_results = session.execute(text(query_sql)).fetchall()

        # Convert results to response objects
        results = []
        for row in raw_results:
            doc_id, title, chunk_idx, chunk_text, similarity, metadata = row
            results.append(
                SearchResult(
                    document_id=doc_id,
                    document_title=title,
                    chunk_index=chunk_idx,
                    chunk_text=chunk_text,
                    similarity_score=float(similarity),
                    metadata=metadata or {},
                )
            )

        execution_time = (time.time() - start_time) * 1000

        return SemanticSearchResponse(
            query=request.query,
            results=results,
            execution_time_ms=execution_time,
            total_results=len(results),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Semantic search error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Search failed"
        )


@router.get("/health")
def search_health():
    """Check if semantic search is available (embeddings working)."""
    try:
        with Session(engine) as session:
            # Check if we have any embeddings in the database
            count = session.execute(
                select(func.count(DocumentEmbedding.id))
            ).scalar() or 0

            return {
                "status": "healthy" if count > 0 else "no_embeddings",
                "embeddings_count": count,
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


# Import func for the health endpoint
from sqlalchemy import func
