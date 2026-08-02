"""Memory lifecycle management - expiration and cleanup policies."""

import logging
from datetime import datetime, timedelta
from typing import Dict

from .memory_model import MemoryScope
from .memory_store import MemoryStore

logger = logging.getLogger(__name__)


class MemoryLifecycleManager:
    """Manages memory lifecycle including expiration and cleanup."""

    # Default expiration times per scope
    DEFAULT_EXPIRATION_TIMES: Dict[str, timedelta] = {
        MemoryScope.WORKING: timedelta(minutes=5),      # 5 minutes
        MemoryScope.SESSION: timedelta(hours=24),       # 24 hours
        MemoryScope.USER: None,                         # Never expires
        MemoryScope.KNOWLEDGE: None,                    # Never expires
    }

    def __init__(self, memory_store: MemoryStore):
        self.store = memory_store

    def get_expiration_time(self, scope: str) -> timedelta:
        """
        Get expiration time for a scope.

        Args:
            scope: Memory scope

        Returns:
            Timedelta for expiration, or None if never expires
        """
        return self.DEFAULT_EXPIRATION_TIMES.get(
            scope,
            self.DEFAULT_EXPIRATION_TIMES[MemoryScope.SESSION],  # Default to session
        )

    async def calculate_expiry_time(
        self,
        scope: str,
        importance: float = 0.5,
    ) -> datetime:
        """
        Calculate expiry time for a memory.

        High importance memories might be kept longer.

        Args:
            scope: Memory scope
            importance: Importance score (0-1)

        Returns:
            Datetime when memory expires
        """

        base_expiration = self.get_expiration_time(scope)

        if base_expiration is None:
            return None  # Never expires

        # High importance memories get extended lifetime
        multiplier = 1 + (importance * 0.5)  # 1x to 1.5x
        actual_expiration = base_expiration * multiplier

        return datetime.utcnow() + actual_expiration

    async def cleanup_scope(self, scope: str) -> int:
        """
        Clean up expired memories in a scope.

        Args:
            scope: Memory scope

        Returns:
            Count of deleted memories
        """

        cleaned = await self.store.cleanup_expired(scope)
        logger.info(f"Memory lifecycle: Cleaned {cleaned} expired memories from {scope}")

        return cleaned

    async def cleanup_all(self) -> int:
        """
        Clean up all expired memories.

        Returns:
            Total count of deleted memories
        """

        total = 0

        for scope in MemoryScope:
            count = await self.cleanup_scope(scope.value)
            total += count

        return total

    async def get_lifecycle_stats(self) -> dict:
        """
        Get statistics about memory lifecycle.

        Returns:
            Dict with lifecycle statistics
        """

        if not hasattr(MemoryStore, "_memories"):
            return {
                "total_memories": 0,
                "expired_memories": 0,
                "by_scope": {},
            }

        total = len(MemoryStore._memories)
        expired = 0
        by_scope = {}
        now = datetime.utcnow()

        for memory in MemoryStore._memories.values():
            if memory.expires_at and memory.expires_at <= now:
                expired += 1

            scope = memory.scope
            if scope not in by_scope:
                by_scope[scope] = {"total": 0, "expired": 0}

            by_scope[scope]["total"] += 1

            if memory.expires_at and memory.expires_at <= now:
                by_scope[scope]["expired"] += 1

        return {
            "total_memories": total,
            "expired_memories": expired,
            "by_scope": by_scope,
        }
