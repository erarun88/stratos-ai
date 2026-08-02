"""RAG Adapter - Knowledge Memory adapter that reuses existing RAG system."""

import logging
from typing import List, Optional

from .memory_model import MemoryEntry, MemoryScope, MemoryType

logger = logging.getLogger(__name__)


class RAGAdapter:
    """
    Adapter pattern: Knowledge Memory interface → Existing RAG backend

    Instead of duplicating vector infrastructure, this adapter allows
    Knowledge Memory to query the existing RAG system.

    Benefits:
    - No duplicate vectors, embeddings, or documents
    - Reuse existing infrastructure
    - One source of truth
    - Simpler maintenance
    """

    def __init__(self, rag_system):
        """
        Initialize with existing RAG system.

        Args:
            rag_system: Existing RAG system with semantic_search capability
        """
        self.rag = rag_system

    async def retrieve(
        self,
        query: str,
        limit: int = 5,
        min_score: float = 0.5,
    ) -> List[MemoryEntry]:
        """
        Retrieve knowledge memories using existing RAG semantic search.

        Args:
            query: Search query
            limit: Maximum results
            min_score: Minimum relevance score (0-1)

        Returns:
            List of MemoryEntry objects wrapping RAG documents
        """

        try:
            # Query existing vector store
            documents = await self.rag.semantic_search(
                query=query,
                top_k=limit,
                doc_type="knowledge",  # Filter to approved knowledge docs
                min_score=min_score,
            )

            if not documents:
                logger.info(f"RAG: No knowledge documents found for query: {query}")
                return []

            # Wrap RAG documents as MemoryEntry objects
            memories = []
            for doc in documents:
                memory = MemoryEntry(
                    memory_id=doc.id,
                    scope=MemoryScope.KNOWLEDGE,
                    scope_id="organization",  # Knowledge is org-wide
                    memory_type=MemoryType.PRACTICE,
                    title=doc.title or doc.id[:50],
                    content={
                        "text": doc.content,
                        "source_document": doc.id,
                    },
                    metadata={
                        "source": "rag",
                        "document_id": doc.id,
                        "doc_type": doc.doc_type,
                    },
                    confidence=doc.relevance_score,
                    utility_score=self._calculate_utility(doc),
                    tags=doc.tags or ["knowledge"],
                )
                memories.append(memory)

            logger.info(f"RAG: Retrieved {len(memories)} knowledge memories for: {query}")
            return memories

        except Exception as e:
            logger.error(f"RAG adapter error during retrieve: {e}")
            return []

    async def store(
        self,
        title: str,
        content: str,
        tags: List[str] = None,
        metadata: dict = None,
    ) -> Optional[str]:
        """
        Store knowledge memory as RAG document.

        Instead of storing in a separate knowledge memory table,
        this adds to the existing document corpus.

        Args:
            title: Document title
            content: Document content
            tags: Tags for categorization
            metadata: Additional metadata

        Returns:
            Document ID if successful
        """

        try:
            # Store as RAG document, not separate memory table
            doc_id = await self.rag.add_document(
                title=title,
                content=content,
                doc_type="knowledge",
                tags=tags or ["knowledge"],
                metadata=metadata or {},
            )

            logger.info(f"RAG: Stored knowledge document: {doc_id}")
            return doc_id

        except Exception as e:
            logger.error(f"RAG adapter error during store: {e}")
            return None

    async def update(
        self,
        doc_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> bool:
        """
        Update existing knowledge document in RAG system.

        Args:
            doc_id: Document ID
            title: New title (optional)
            content: New content (optional)
            tags: New tags (optional)

        Returns:
            Success status
        """

        try:
            # Update in existing RAG system
            await self.rag.update_document(
                doc_id=doc_id,
                title=title,
                content=content,
                tags=tags,
            )

            logger.info(f"RAG: Updated knowledge document: {doc_id}")
            return True

        except Exception as e:
            logger.error(f"RAG adapter error during update: {e}")
            return False

    async def delete(self, doc_id: str) -> bool:
        """
        Delete knowledge document from RAG system.

        Args:
            doc_id: Document ID

        Returns:
            Success status
        """

        try:
            await self.rag.delete_document(doc_id)
            logger.info(f"RAG: Deleted knowledge document: {doc_id}")
            return True

        except Exception as e:
            logger.error(f"RAG adapter error during delete: {e}")
            return False

    def _calculate_utility(self, doc) -> float:
        """
        Calculate utility score based on document usage.

        Args:
            doc: RAG document

        Returns:
            Utility score (0-1)
        """

        if not hasattr(doc, "access_count") or doc.access_count == 0:
            return 0.5  # Default

        if not hasattr(doc, "total_views"):
            return min(1.0, doc.access_count / 10.0)

        # Score based on access ratio
        ratio = doc.access_count / max(1, doc.total_views)
        return min(1.0, ratio)

    async def get_statistics(self) -> dict:
        """
        Get knowledge memory statistics from RAG system.

        Returns:
            Dict with statistics
        """

        try:
            stats = await self.rag.get_statistics(doc_type="knowledge")
            return {
                "knowledge_documents": stats.get("count", 0),
                "avg_relevance": stats.get("avg_score", 0),
                "most_accessed": stats.get("most_accessed", []),
            }

        except Exception as e:
            logger.error(f"Error getting RAG statistics: {e}")
            return {}
