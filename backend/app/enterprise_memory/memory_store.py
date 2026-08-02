"""Memory store - database operations for memory system."""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, func, or_, text
from sqlalchemy.orm import Session

from app.database import get_session
from .memory_model import MemoryEntry, MemoryScope, MemoryType

logger = logging.getLogger(__name__)


class MemoryStore:
    """Database operations for memory system."""

    def __init__(self, db_session: Optional[Session] = None):
        self.db = db_session

    async def store(
        self,
        scope: str,
        scope_id: str,
        memory_type: str,
        title: str,
        content: Dict[str, Any],
        tags: List[str] = None,
        importance: float = 0.5,
        expires_at: Optional[datetime] = None,
        source: str = "user_input",
        source_id: str = "",
        component_id: Optional[str] = None,
    ) -> MemoryEntry:
        """Store a new memory."""

        memory = MemoryEntry(
            scope=scope,
            scope_id=scope_id,
            memory_type=memory_type,
            title=title,
            content=content,
            tags=tags or [],
            importance=importance,
            expires_at=expires_at,
            source=source,
            source_id=source_id,
            component_id=component_id,
            keywords=self._extract_keywords(title, content),
        )

        # Store in memory (in-process for now, will be replaced with DB)
        # For MVP, using in-memory storage
        if not hasattr(MemoryStore, "_memories"):
            MemoryStore._memories = {}

        MemoryStore._memories[memory.memory_id] = memory
        logger.info(f"Stored memory: {memory.memory_id} ({scope}/{memory_type})")

        return memory

    async def retrieve_all(
        self,
        scope: str,
        scope_id: str,
        memory_type: Optional[str] = None,
    ) -> List[MemoryEntry]:
        """Retrieve all memories for a scope."""

        if not hasattr(MemoryStore, "_memories"):
            return []

        memories = [
            m
            for m in MemoryStore._memories.values()
            if m.scope == scope and m.scope_id == scope_id
            and (memory_type is None or m.memory_type == memory_type)
            and (m.expires_at is None or m.expires_at > datetime.utcnow())
        ]

        # Increment access count
        for m in memories:
            m.access_count += 1
            m.updated_at = datetime.utcnow()

        return sorted(memories, key=lambda m: m.updated_at, reverse=True)

    async def search(
        self,
        query: str,
        scope: str,
        scope_id: Optional[str] = None,
        memory_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[MemoryEntry]:
        """Search memories by keyword."""

        if not hasattr(MemoryStore, "_memories"):
            return []

        query_lower = query.lower()
        results = []

        for memory in MemoryStore._memories.values():
            # Check if expired
            if memory.expires_at and memory.expires_at <= datetime.utcnow():
                continue

            # Check scope
            if memory.scope != scope:
                continue

            if scope_id and memory.scope_id != scope_id:
                continue

            if memory_type and memory.memory_type != memory_type:
                continue

            # Check if matches query
            match_score = 0
            if query_lower in memory.title.lower():
                match_score += 10

            for keyword in memory.keywords:
                if query_lower in keyword.lower():
                    match_score += 5

            for tag in memory.tags:
                if query_lower in tag.lower():
                    match_score += 3

            if match_score > 0:
                results.append((memory, match_score))

        # Sort by score and return top results
        results.sort(key=lambda x: x[1], reverse=True)

        # Increment access count
        for memory, _ in results[:limit]:
            memory.access_count += 1
            memory.updated_at = datetime.utcnow()

        return [m for m, _ in results[:limit]]

    async def get(self, memory_id: str) -> Optional[MemoryEntry]:
        """Get a specific memory by ID."""

        if not hasattr(MemoryStore, "_memories"):
            return None

        memory = MemoryStore._memories.get(memory_id)

        if memory and (memory.expires_at is None or memory.expires_at > datetime.utcnow()):
            memory.access_count += 1
            memory.updated_at = datetime.utcnow()
            return memory

        return None

    async def update(
        self,
        memory_id: str,
        updates: Dict[str, Any],
    ) -> Optional[MemoryEntry]:
        """Update an existing memory."""

        if not hasattr(MemoryStore, "_memories"):
            return None

        memory = MemoryStore._memories.get(memory_id)
        if not memory:
            return None

        # Apply updates
        for key, value in updates.items():
            if hasattr(memory, key) and key not in ["memory_id", "created_at"]:
                if key == "content":
                    memory.content.update(value)
                    memory.keywords = self._extract_keywords(memory.title, memory.content)
                else:
                    setattr(memory, key, value)

        memory.updated_at = datetime.utcnow()
        memory.version += 1

        logger.info(f"Updated memory: {memory_id}")
        return memory

    async def mark_useful(self, memory_id: str, delta: float = 0.1) -> Optional[MemoryEntry]:
        """Increment utility score."""

        memory = await self.get(memory_id)
        if memory:
            memory.utility_score = min(1.0, memory.utility_score + delta)
            memory.updated_at = datetime.utcnow()
            logger.info(f"Marked memory as useful: {memory_id} (score: {memory.utility_score})")

        return memory

    async def forget(self, memory_id: str, reason: str = "user_request") -> bool:
        """Delete a memory."""

        if not hasattr(MemoryStore, "_memories"):
            return False

        if memory_id in MemoryStore._memories:
            del MemoryStore._memories[memory_id]
            logger.info(f"Forgot memory: {memory_id} (reason: {reason})")
            return True

        return False

    async def cleanup_expired(self, scope: Optional[str] = None) -> int:
        """Remove expired memories."""

        if not hasattr(MemoryStore, "_memories"):
            return 0

        now = datetime.utcnow()
        expired = []

        for memory_id, memory in MemoryStore._memories.items():
            if memory.expires_at and memory.expires_at <= now:
                if scope is None or memory.scope == scope:
                    expired.append(memory_id)

        # Delete expired
        for memory_id in expired:
            del MemoryStore._memories[memory_id]

        logger.info(f"Cleaned up {len(expired)} expired memories")
        return len(expired)

    @staticmethod
    def _extract_keywords(title: str, content: Dict[str, Any]) -> List[str]:
        """Extract keywords from title and content for search."""

        keywords = []

        # Extract from title
        keywords.extend(title.lower().split())

        # Extract from content values
        for value in content.values():
            if isinstance(value, str):
                keywords.extend(value.lower().split())
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        keywords.extend(item.lower().split())

        # Remove duplicates and short words
        keywords = list(set(k for k in keywords if len(k) > 2))

        return keywords[:20]  # Limit to 20 keywords
