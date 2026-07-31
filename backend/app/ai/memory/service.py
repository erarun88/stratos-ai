"""Memory service implementation.

Provides in-memory storage with optional database persistence.
Can be extended to use Redis, DynamoDB, or other stores.
"""

import logging
from collections import defaultdict
from typing import List, Optional

from app.ai.memory.base import MemoryStore, Message

logger = logging.getLogger(__name__)


class MemoryService(MemoryStore):
    """Simple in-memory conversation memory.

    Stores conversation history in-process.
    Suitable for MVP; upgrade to persistent storage for production.
    """

    def __init__(self, max_memory_per_conversation: int = 20):
        """Initialize memory service.

        Args:
            max_memory_per_conversation: Max messages to keep per conversation
        """
        self.max_memory = max_memory_per_conversation
        # conversation_id -> List[Message]
        self.conversations: dict[str, List[Message]] = defaultdict(list)
        logger.info(f"MemoryService initialized (max {max_memory_per_conversation} per conversation)")

    async def save(
        self,
        conversation_id: str,
        message: Message,
    ) -> None:
        """Save a message to conversation history.

        Args:
            conversation_id: Unique conversation identifier
            message: Message to save
        """
        self.conversations[conversation_id].append(message)

        # Trim if exceeds max
        if len(self.conversations[conversation_id]) > self.max_memory:
            self.conversations[conversation_id] = self.conversations[conversation_id][-self.max_memory:]

        logger.debug(f"Saved message to conversation {conversation_id}")

    async def load(
        self,
        conversation_id: str,
        limit: int = 10,
    ) -> List[Message]:
        """Load conversation history.

        Args:
            conversation_id: Conversation ID
            limit: Maximum number of recent messages to load

        Returns:
            List of messages in chronological order
        """
        messages = self.conversations.get(conversation_id, [])
        return messages[-limit:] if limit > 0 else messages

    async def clear(self, conversation_id: str) -> None:
        """Clear all messages for a conversation.

        Args:
            conversation_id: Conversation ID to clear
        """
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            logger.info(f"Cleared conversation {conversation_id}")

    async def summarize(self, conversation_id: str) -> Optional[str]:
        """Summarize conversation history.

        Simple implementation: just joins message snippets.
        Production version would use LLM to create actual summary.

        Args:
            conversation_id: Conversation ID

        Returns:
            Summary string or None if empty
        """
        messages = await self.load(conversation_id, limit=999)

        if not messages:
            return None

        # Simple concatenation for MVP
        # Production: call LLM to create real summary
        summary_parts = []
        for msg in messages[-10:]:  # Last 10 messages
            role_label = "User" if msg.role == "user" else "Assistant"
            snippet = msg.content[:100]
            summary_parts.append(f"{role_label}: {snippet}")

        return "\n".join(summary_parts)

    def get_stats(self, conversation_id: str) -> dict:
        """Get statistics about a conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            Dict with message count, token count, etc.
        """
        messages = self.conversations.get(conversation_id, [])
        return {
            "message_count": len(messages),
            "token_count": sum(m.tokens for m in messages),
            "user_messages": sum(1 for m in messages if m.role == "user"),
            "assistant_messages": sum(1 for m in messages if m.role == "assistant"),
        }
