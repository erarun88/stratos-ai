"""Memory API - REST endpoints for enterprise memory system."""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.enterprise_memory import (
    MemoryDecisionEngine,
    MemoryEntry,
    MemoryLifecycleManager,
    MemoryStore,
)
from app.enterprise_memory.rag_adapter import RAGAdapter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/memory", tags=["memory"])

# Initialize components (in production, these would be singletons from DI)
memory_store = MemoryStore()

# Try to get LLM client, but don't fail if not available (Phase 2 feature)
llm_client = None
try:
    from app.config import settings
    if hasattr(settings, 'openai_api_key') and settings.openai_api_key:
        from openai import OpenAI
        llm_client = OpenAI(api_key=settings.openai_api_key)
except Exception as e:
    logger.warning(f"LLM client not available: {e}")

decision_engine = MemoryDecisionEngine(llm_client, memory_store)
lifecycle_manager = MemoryLifecycleManager(memory_store)
# RAG adapter initialized later when RAG system is available
rag_adapter = None


@router.post("/store")
async def store_memory(
    scope: str = Query(..., description="Memory scope: working, session, user, knowledge"),
    scope_id: str = Query(..., description="Scope ID: user-123, session-456, etc"),
    memory_type: str = Query(..., description="Memory type: context, preference, practice, summary"),
    title: str = Query(..., description="Human-readable title"),
    content: dict = Query(..., description="Memory content (flexible structure)"),
    tags: Optional[List[str]] = Query(None, description="Tags for categorization"),
    importance: float = Query(0.5, ge=0, le=1, description="Importance score 0-1"),
    source: str = Query("user_input", description="Source of memory"),
    source_id: str = Query("", description="Source ID"),
) -> dict:
    """
    Store a memory directly (bypassing decision engine).

    Useful for trusted sources or admin storage.
    """

    try:
        memory = await memory_store.store(
            scope=scope,
            scope_id=scope_id,
            memory_type=memory_type,
            title=title,
            content=content,
            tags=tags or [],
            importance=importance,
            source=source,
            source_id=source_id,
        )

        return {
            "status": "stored",
            "memory_id": memory.memory_id,
            "scope": memory.scope,
            "type": memory.memory_type,
        }

    except Exception as e:
        logger.error(f"Failed to store memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/decide")
async def decide_memory(
    statement: str = Query(..., description="Statement to evaluate"),
    scope: str = Query(..., description="Memory scope"),
    scope_id: str = Query(..., description="Scope ID"),
) -> dict:
    """
    Get decision engine decision for a statement (without storing).

    Useful for testing and understanding decisions.
    """

    try:
        decision = await decision_engine.decide(
            statement=statement,
            scope=scope,
            scope_id=scope_id,
        )

        return {
            "statement": statement,
            "decision": decision.action.value,
            "confidence": decision.confidence,
            "rationale": decision.rationale,
            "related_memory_ids": decision.related_memory_ids,
            "suggested_type": decision.suggested_memory_type,
            "suggested_title": decision.suggested_title,
        }

    except Exception as e:
        logger.error(f"Decision engine error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process")
async def process_statement(
    statement: str = Query(..., description="Statement to process"),
    scope: str = Query(..., description="Memory scope"),
    scope_id: str = Query(..., description="Scope ID"),
    source: str = Query("user_input", description="Source"),
    source_id: str = Query("", description="Source ID"),
) -> dict:
    """
    Process a statement through decision engine and execute decision.

    Full pipeline: Statement → Decision → Action
    """

    try:
        result = await decision_engine.process(
            statement=statement,
            scope=scope,
            scope_id=scope_id,
            source=source,
            source_id=source_id,
        )

        return result

    except Exception as e:
        logger.error(f"Failed to process statement: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_memories(
    query: str = Query(..., description="Search query"),
    scope: str = Query(..., description="Memory scope to search"),
    scope_id: Optional[str] = Query(None, description="Optional scope ID filter"),
    memory_type: Optional[str] = Query(None, description="Optional type filter"),
    limit: int = Query(10, ge=1, le=50, description="Max results"),
) -> dict:
    """
    Search memories by keyword.
    """

    try:
        results = await memory_store.search(
            query=query,
            scope=scope,
            scope_id=scope_id,
            memory_type=memory_type,
            limit=limit,
        )

        return {
            "query": query,
            "found": len(results),
            "memories": [m.to_dict() for m in results],
        }

    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{memory_id}")
async def get_memory(memory_id: str) -> dict:
    """
    Get a specific memory by ID.
    """

    try:
        memory = await memory_store.get(memory_id)

        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")

        return memory.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get memory error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{memory_id}")
async def update_memory(
    memory_id: str,
    updates: dict = Query(..., description="Updates to apply"),
) -> dict:
    """
    Update an existing memory.
    """

    try:
        memory = await memory_store.update(memory_id, updates)

        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")

        return {
            "status": "updated",
            "memory": memory.to_dict(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{memory_id}/mark-useful")
async def mark_memory_useful(
    memory_id: str,
    delta: float = Query(0.1, ge=0, le=1),
) -> dict:
    """
    Increment utility score for a memory.
    """

    try:
        memory = await memory_store.mark_useful(memory_id, delta)

        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")

        return {
            "status": "marked_useful",
            "memory_id": memory_id,
            "utility_score": memory.utility_score,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mark useful error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{memory_id}")
async def forget_memory(
    memory_id: str,
    reason: str = Query("user_request"),
) -> dict:
    """
    Delete a memory.
    """

    try:
        success = await memory_store.forget(memory_id, reason)

        if not success:
            raise HTTPException(status_code=404, detail="Memory not found")

        return {
            "status": "forgotten",
            "memory_id": memory_id,
            "reason": reason,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Forget error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup/{scope}")
async def cleanup_scope(scope: str) -> dict:
    """
    Clean up expired memories in a scope.
    """

    try:
        count = await lifecycle_manager.cleanup_scope(scope)

        return {
            "status": "cleaned",
            "scope": scope,
            "deleted_count": count,
        }

    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/lifecycle")
async def lifecycle_stats() -> dict:
    """
    Get memory lifecycle statistics.
    """

    try:
        stats = await lifecycle_manager.get_lifecycle_stats()
        return stats

    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge/search")
async def search_knowledge(
    query: str = Query(..., description="Search query"),
    limit: int = Query(5, ge=1, le=20),
) -> dict:
    """
    Search knowledge memories using RAG adapter.

    Uses existing RAG system - no knowledge memory duplication.
    """

    if not rag_adapter:
        raise HTTPException(status_code=503, detail="RAG system not initialized")

    try:
        memories = await rag_adapter.retrieve(query, limit=limit)

        return {
            "query": query,
            "found": len(memories),
            "memories": [m.to_dict() for m in memories],
        }

    except Exception as e:
        logger.error(f"Knowledge search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
