"""Semantic Event Store - Persistence for semantic execution events.

Converts between SemanticExecutionEvent and database storage.
Maintains backward compatibility with old ExecutionEvent model.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import Column, String, Float, Integer, DateTime, Text, JSON, Index
from sqlalchemy.orm import Session

from app.database import engine
from app.models import Base
from app.execution_studio.semantic_event import (
    SemanticExecutionEvent,
    EventStatus,
    ComponentType,
    RelationshipType,
    InputSummary,
    OutputSummary,
    RelatedEvent,
    ComponentDependency,
    Decision,
)

logger = logging.getLogger(__name__)


class SemanticEventModel(Base):
    """SQLAlchemy model for semantic execution events (persisted to PostgreSQL)."""

    __tablename__ = "semantic_execution_events"

    # IDs
    event_id = Column(String(36), primary_key=True)
    request_id = Column(String(36), nullable=False, index=True)
    parent_event_id = Column(String(36), nullable=True, index=True)
    sequence_in_parent = Column(Integer, default=0)

    # The Story
    purpose = Column(Text, nullable=False)
    reason = Column(Text, default="")
    description = Column(Text, default="")

    # What & Who
    component = Column(String(255), nullable=False, index=True)
    component_type = Column(String(50), nullable=False)
    component_role = Column(String(100), default="")
    action = Column(String(255), nullable=False)

    # I/O (stored as JSON)
    input_json = Column(JSON, default={})
    output_json = Column(JSON, default={})

    # Relationships (stored as JSON)
    related_events_json = Column(JSON, default=[])
    dependencies_json = Column(JSON, default=[])
    decision_json = Column(JSON, nullable=True)

    # Timing
    timestamp = Column(DateTime, nullable=False, index=True)
    duration_ms = Column(Float, default=0.0)
    started_relative_ms = Column(Float, default=0.0)

    # Status & Quality
    status = Column(String(50), nullable=False, index=True)
    error = Column(Text, nullable=True)
    warnings_json = Column(JSON, default=[])

    # Resources
    tokens_used = Column(Integer, default=0)
    tokens_input = Column(Integer, default=0)
    tokens_output = Column(Integer, default=0)
    cost = Column(Float, default=0.0)

    # Metadata
    metadata_json = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Indexes
    __table_args__ = (
        Index("idx_semantic_request_component", "request_id", "component"),
        Index("idx_semantic_request_timestamp", "request_id", "timestamp"),
        Index("idx_semantic_parent_sequence", "parent_event_id", "sequence_in_parent"),
    )

    def to_semantic_event(self) -> SemanticExecutionEvent:
        """Convert DB model to SemanticExecutionEvent."""
        # Reconstruct input
        input_data = self.input_json or {}
        input_summary = InputSummary(
            type=input_data.get("type", "unknown"),
            description=input_data.get("description", ""),
            key_fields=input_data.get("key_fields", {}),
            source_event_ids=input_data.get("source_event_ids", []),
        )

        # Reconstruct output
        output_data = self.output_json or {}
        output_summary = OutputSummary(
            type=output_data.get("type", "unknown"),
            description=output_data.get("description", ""),
            key_fields=output_data.get("key_fields", {}),
            confidence=output_data.get("confidence", 0.5),
            quality_score=output_data.get("quality_score", 0.5),
        )

        # Reconstruct related events
        related_events = []
        for rel_data in (self.related_events_json or []):
            related_events.append(
                RelatedEvent(
                    event_id=rel_data["event_id"],
                    relationship=RelationshipType(rel_data["relationship"]),
                    description=rel_data["description"],
                )
            )

        # Reconstruct dependencies
        dependencies = []
        for dep_data in (self.dependencies_json or []):
            dependencies.append(
                ComponentDependency(
                    component=dep_data["component"],
                    reason=dep_data["reason"],
                    criticality=dep_data.get("criticality", "required"),
                )
            )

        # Reconstruct decision
        decision = None
        if self.decision_json:
            dec_data = self.decision_json
            decision = Decision(
                type=dec_data["type"],
                description=dec_data["description"],
                options_considered=dec_data.get("options_considered", 0),
                rationale=dec_data.get("rationale", ""),
                confidence=dec_data.get("confidence", 0.5),
            )

        return SemanticExecutionEvent(
            event_id=self.event_id,
            request_id=self.request_id,
            parent_event_id=self.parent_event_id,
            sequence_in_parent=self.sequence_in_parent,
            purpose=self.purpose,
            reason=self.reason,
            description=self.description,
            component=self.component,
            component_type=ComponentType(self.component_type),
            component_role=self.component_role,
            action=self.action,
            input=input_summary,
            output=output_summary,
            related_events=related_events,
            dependencies=dependencies,
            decision=decision,
            timestamp=self.timestamp,
            duration_ms=self.duration_ms,
            started_relative_ms=self.started_relative_ms,
            status=EventStatus(self.status),
            error=self.error,
            warnings=self.warnings_json or [],
            tokens_used=self.tokens_used,
            tokens_input=self.tokens_input,
            tokens_output=self.tokens_output,
            cost=self.cost,
            metadata=self.metadata_json or {},
            created_at=self.created_at,
            indexed=True,
        )

    @staticmethod
    def from_semantic_event(event: SemanticExecutionEvent) -> "SemanticEventModel":
        """Create DB model from SemanticExecutionEvent."""
        return SemanticEventModel(
            event_id=str(event.event_id),
            request_id=str(event.request_id),
            parent_event_id=str(event.parent_event_id) if event.parent_event_id else None,
            sequence_in_parent=event.sequence_in_parent,
            purpose=event.purpose,
            reason=event.reason,
            description=event.description,
            component=event.component,
            component_type=event.component_type.value,
            component_role=event.component_role,
            action=event.action,
            input_json={
                "type": event.input.type,
                "description": event.input.description,
                "key_fields": event.input.key_fields,
                "source_event_ids": event.input.source_event_ids,
            },
            output_json={
                "type": event.output.type,
                "description": event.output.description,
                "key_fields": event.output.key_fields,
                "confidence": event.output.confidence,
                "quality_score": event.output.quality_score,
            },
            related_events_json=[
                {
                    "event_id": rel.event_id,
                    "relationship": rel.relationship.value,
                    "description": rel.description,
                }
                for rel in event.related_events
            ],
            dependencies_json=[
                {
                    "component": dep.component,
                    "reason": dep.reason,
                    "criticality": dep.criticality,
                }
                for dep in event.dependencies
            ],
            decision_json={
                "type": event.decision.type,
                "description": event.decision.description,
                "options_considered": event.decision.options_considered,
                "rationale": event.decision.rationale,
                "confidence": event.decision.confidence,
            } if event.decision else None,
            timestamp=event.timestamp,
            duration_ms=event.duration_ms,
            started_relative_ms=event.started_relative_ms,
            status=event.status.value,
            error=event.error,
            warnings_json=event.warnings,
            tokens_used=event.tokens_used,
            tokens_input=event.tokens_input,
            tokens_output=event.tokens_output,
            cost=event.cost,
            metadata_json=event.metadata,
            created_at=event.created_at,
        )


class SemanticEventStore:
    """Service for storing and querying semantic execution events."""

    def __init__(self):
        """Initialize event store (creates tables if needed)."""
        Base.metadata.create_all(engine)
        logger.info("SemanticEventStore initialized")

    def store_event(self, event: SemanticExecutionEvent) -> bool:
        """Store a semantic event."""
        try:
            with Session(engine) as session:
                model = SemanticEventModel.from_semantic_event(event)
                session.add(model)
                session.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to store semantic event: {e}", exc_info=True)
            return False

    def store_events(self, events: List[SemanticExecutionEvent]) -> int:
        """Store multiple semantic events."""
        stored_count = 0
        try:
            with Session(engine) as session:
                for event in events:
                    try:
                        model = SemanticEventModel.from_semantic_event(event)
                        session.add(model)
                        stored_count += 1
                    except Exception as e:
                        logger.error(f"Failed to add semantic event to batch: {e}")
                session.commit()
                return stored_count
        except Exception as e:
            logger.error(f"Failed to store semantic event batch: {e}", exc_info=True)
            return 0

    def get_request_trace(self, request_id: str) -> List[SemanticExecutionEvent]:
        """Get all semantic events for a request (in order)."""
        try:
            with Session(engine) as session:
                models = (
                    session.query(SemanticEventModel)
                    .filter(SemanticEventModel.request_id == request_id)
                    .order_by(SemanticEventModel.timestamp)
                    .all()
                )
                return [m.to_semantic_event() for m in models]
        except Exception as e:
            logger.error(f"Failed to get semantic request trace: {e}", exc_info=True)
            return []

    def get_component_events(
        self,
        request_id: str,
        component: str,
    ) -> List[SemanticExecutionEvent]:
        """Get semantic events for a specific component."""
        try:
            with Session(engine) as session:
                models = (
                    session.query(SemanticEventModel)
                    .filter(
                        SemanticEventModel.request_id == request_id,
                        SemanticEventModel.component == component,
                    )
                    .order_by(SemanticEventModel.timestamp)
                    .all()
                )
                return [m.to_semantic_event() for m in models]
        except Exception as e:
            logger.error(f"Failed to get semantic component events: {e}", exc_info=True)
            return []

    def get_children_events(
        self,
        parent_event_id: str,
    ) -> List[SemanticExecutionEvent]:
        """Get direct children of an event."""
        try:
            with Session(engine) as session:
                models = (
                    session.query(SemanticEventModel)
                    .filter(SemanticEventModel.parent_event_id == parent_event_id)
                    .order_by(SemanticEventModel.sequence_in_parent)
                    .all()
                )
                return [m.to_semantic_event() for m in models]
        except Exception as e:
            logger.error(f"Failed to get semantic child events: {e}", exc_info=True)
            return []

    def delete_old_events(self, days: int = 7) -> int:
        """Delete semantic events older than N days."""
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            with Session(engine) as session:
                result = session.query(SemanticEventModel).filter(
                    SemanticEventModel.created_at < cutoff
                ).delete()
                session.commit()
                logger.info(f"Deleted {result} old semantic events")
                return result
        except Exception as e:
            logger.error(f"Failed to delete old semantic events: {e}", exc_info=True)
            return 0


# Global singleton
_semantic_event_store: Optional[SemanticEventStore] = None


def get_semantic_event_store() -> SemanticEventStore:
    """Get or create global semantic event store."""
    global _semantic_event_store
    if _semantic_event_store is None:
        _semantic_event_store = SemanticEventStore()
    return _semantic_event_store
