"""Tool for semantic search across project documents.

Uses pgvector to find semantically similar document chunks.
"""

import logging
from typing import List, Optional

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.database import engine
from app.models.document import Document
from app.models.embedding import DocumentEmbedding
from app.services.embedding_service import generate_embeddings
from app.tools.base import Tool, ToolResult

logger = logging.getLogger(__name__)


class SemanticSearchTool(Tool):
    """Search documents by semantic meaning using vector similarity."""

    name = "semantic_search"
    description = "Search project documents by semantic meaning. Returns the most relevant document chunks based on similarity."

    async def execute(
        self,
        query: str,
        limit: int = 5,
        threshold: float = 0.7,
        project_id: Optional[int] = None,
    ) -> ToolResult:
        """Search documents semantically.

        Args:
            query: Search query (natural language)
            limit: Maximum number of results to return
            threshold: Minimum similarity score (0.0-1.0)
            project_id: Optional filter by project

        Returns:
            ToolResult with list of matching document chunks
        """
        try:
            if not query or not query.strip():
                return ToolResult(success=False, error="Query cannot be empty")

            if limit < 1 or limit > 50:
                limit = min(max(limit, 1), 50)

            logger.debug(f"Semantic search: query={query}, limit={limit}, project_id={project_id}")

            # Generate embedding for query
            try:
                embedding_result = generate_embeddings([query])
                query_embedding = embedding_result["embeddings"][0]
            except Exception as e:
                logger.error(f"Failed to generate query embedding: {e}")
                return ToolResult(success=False, error=f"Failed to embed query: {e}")

            # Build and execute search query
            with Session(engine) as session:
                query_sql = f"""
                    SELECT
                        de.document_id,
                        d.title,
                        de.chunk_index,
                        de.chunk_text,
                        (1 - (de.embedding <=> '{query_embedding}')) as similarity_score,
                        d.customer,
                        d.document_type
                    FROM document_embeddings de
                    JOIN documents d ON de.document_id = d.id
                    WHERE d.deleted_at IS NULL
                        AND d.embedding_status = 'completed'
                        AND (1 - (de.embedding <=> '{query_embedding}')) >= {threshold}
                """

                if project_id is not None:
                    query_sql += f" AND d.project_id = {project_id}"

                query_sql += f"""
                    ORDER BY similarity_score DESC
                    LIMIT {limit}
                """

                raw_results = session.execute(text(query_sql)).fetchall()

                results = []
                for row in raw_results:
                    doc_id, title, chunk_idx, chunk_text, similarity, customer, doc_type = row
                    results.append({
                        "document_id": doc_id,
                        "title": title,
                        "chunk_index": chunk_idx,
                        "chunk_text": chunk_text,
                        "similarity_score": float(similarity),
                        "customer": customer,
                        "document_type": doc_type,
                    })

            logger.info(f"Semantic search found {len(results)} results")
            return ToolResult(
                success=True,
                data=results,
                metadata={
                    "query": query,
                    "results_count": len(results),
                    "threshold": threshold,
                },
            )

        except Exception as e:
            logger.error(f"Semantic search error: {e}", exc_info=True)
            return ToolResult(success=False, error=str(e))
