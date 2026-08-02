"""Memory data models - extensible schema for all memory types."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4


class MemoryScope(str, Enum):
    """Memory scope - where this memory belongs. Extensible for future org/team/project."""
    WORKING = "working"          # Current execution context (ephemeral)
    SESSION = "session"          # Request collection summary (24 hours)
    USER = "user"                # User learnings & preferences (long-term)
    KNOWLEDGE = "knowledge"      # Shared organizational knowledge (persistent)
    # Future scopes (added later without refactoring):
    # PROJECT = "project"
    # TEAM = "team"
    # ORGANIZATION = "organization"


class MemoryType(str, Enum):
    """Memory type - what kind of memory. Extensible for future Decision/Pattern/Learning."""
    CONTEXT = "context"          # Execution context
    PREFERENCE = "preference"    # User preferences & learnings
    PRACTICE = "practice"        # Best practices & procedures
    SUMMARY = "summary"          # Session or execution summary
    # Future types (added later without refactoring):
    # DECISION = "decision"
    # PATTERN = "pattern"
    # LEARNING = "learning"
    # CONSTRAINT = "constraint"


class MemoryDecisionAction(str, Enum):
    """Decision actions - what to do with a statement."""
    IGNORE = "ignore"            # Don't store (trivial, duplicate)
    STORE = "store"              # Create new memory
    UPDATE = "update"            # Update existing memory
    MERGE = "merge"              # Merge with related memories
    DELETE = "delete"            # Mark obsolete memories as deleted


@dataclass
class MemoryDecision:
    """Decision engine output - what to do with a statement."""
    action: MemoryDecisionAction      # IGNORE, STORE, UPDATE, MERGE, DELETE
    confidence: float                 # 0-1, how sure about this decision
    rationale: str                    # Why this decision was made
    related_memory_ids: List[str] = field(default_factory=list)  # Related memories
    suggested_scope: str = MemoryScope.USER                       # Where to store
    suggested_memory_type: str = MemoryType.CONTEXT               # What type
    suggested_title: Optional[str] = None                         # Suggested title


@dataclass
class MemoryEntry:
    """Generic memory entry - flexible schema for all memory types and scopes."""

    # === SCOPE & TYPE (Extensible) ===
    scope: str                      # "working" | "session" | "user" | "knowledge"
    scope_id: str                   # user-123, session-456, etc
    memory_type: str                # "context" | "preference" | "practice" | "summary"
    title: str                      # Human-readable title

    # === IDENTITY ===
    memory_id: str = field(default_factory=lambda: str(uuid4()))

    # === CONTENT ===
    content: Dict[str, Any] = field(default_factory=dict)  # Flexible structure

    # === METADATA ===
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)  # For full-text search

    # === SOURCE ===
    source: str = ""                # "semantic_event" | "decision" | "user_input" | "auto_learn"
    source_id: str = ""             # ID of the source
    component_id: Optional[str] = None

    # === RELATIONSHIPS ===
    related_memories: List[str] = field(default_factory=list)

    # === LIFECYCLE ===
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    importance: float = 0.5         # 0-1, affects retention

    # === QUALITY ===
    confidence: float = 0.5         # 0-1, how sure are we
    utility_score: float = 0.5      # 0-1, how useful has it been
    access_count: int = 0           # Times retrieved

    # === SEARCH ===
    embedding: Optional[List[float]] = None  # Vector embedding (added later)

    # === VERSION ===
    version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization."""
        return {
            "memory_id": self.memory_id,
            "scope": self.scope,
            "scope_id": self.scope_id,
            "memory_type": self.memory_type,
            "title": self.title,
            "content": self.content,
            "metadata": self.metadata,
            "tags": self.tags,
            "keywords": self.keywords,
            "source": self.source,
            "source_id": self.source_id,
            "component_id": self.component_id,
            "related_memories": self.related_memories,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "importance": self.importance,
            "confidence": self.confidence,
            "utility_score": self.utility_score,
            "access_count": self.access_count,
            "version": self.version,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "MemoryEntry":
        """Create from dict."""
        return MemoryEntry(
            memory_id=data.get("memory_id", str(uuid4())),
            scope=data.get("scope", MemoryScope.USER),
            scope_id=data.get("scope_id", ""),
            memory_type=data.get("memory_type", MemoryType.CONTEXT),
            title=data.get("title", ""),
            content=data.get("content", {}),
            metadata=data.get("metadata", {}),
            tags=data.get("tags", []),
            keywords=data.get("keywords", []),
            source=data.get("source", ""),
            source_id=data.get("source_id", ""),
            component_id=data.get("component_id"),
            related_memories=data.get("related_memories", []),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.utcnow(),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            importance=data.get("importance", 0.5),
            confidence=data.get("confidence", 0.5),
            utility_score=data.get("utility_score", 0.5),
            access_count=data.get("access_count", 0),
            version=data.get("version", 1),
        )
