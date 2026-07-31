"""Abstract base class for memory stores.

Defines interface for saving and loading conversation history.
Implementations can be in-memory, database, or external.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Message:
    """A single message in a conversation."""

    role: str  # "user" or "assistant"
    content: str
    tokens: int = 0
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class MemoryStore(ABC):
    """Abstract base class for conversation memory storage.

    Implementations handle persistence of conversation history.
    """

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def clear(self, conversation_id: str) -> None:
        """Clear all messages for a conversation.

        Args:
            conversation_id: Conversation ID to clear
        """
        pass

    @abstractmethod
    async def summarize(self, conversation_id: str) -> Optional[str]:
        """Summarize conversation history for context window management.

        Used when conversation becomes too long to fit in token budget.

        Args:
            conversation_id: Conversation ID

        Returns:
            Summary string or None if conversation empty
        """
        pass

    async def get_context_tokens(self, conversation_id: str) -> int:
        """Get total token count for conversation history.

        Args:
            conversation_id: Conversation ID

        Returns:
            Total token count
        """
        messages = await self.load(conversation_id, limit=999)
        return sum(m.tokens for m in messages)
