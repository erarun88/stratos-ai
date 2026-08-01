"""Execution Studio - Event Store

Persistent storage for execution events in PostgreSQL.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import Column, String, Float, Integer, DateTime, Text, JSON, Index, Boolean
from sqlalchemy.orm import Session

from app.database import engine
from app.models import Base
from app.execution_studio.event_model import ExecutionEvent, EventStatus, TraceMetrics

logger = logging.getLogger(__name__)


class ExecutionEventModel(Base):
    """SQLAlchemy model for execution events (persisted to PostgreSQL)."""

    __tablename__ = "execution_events"

    # IDs
    event_id = Column(String(36), primary_key=True)
    request_id = Column(String(36), nullable=False, index=True)
    parent_event_id = Column(String(36), nullable=True)

    # Timing
    timestamp = Column(DateTime, nullable=False, index=True)
    duration_ms = Column(Float, default=0.0)

    # What happened
    component = Column(String(255), nullable=False, index=True)
    action = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, index=True)

    # Metrics
    tokens_used = Column(Integer, default=0)
    cost = Column(Float, default=0.0)
    latency_ms = Column(Float, default=0.0)

    # Data
    metadata_json = Column(JSON, default={})
    error = Column(Text, nullable=True)

    # System
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Indexes for common queries
    __table_args__ = (
        Index("idx_request_component", "request_id", "component"),
        Index("idx_timestamp_desc", "timestamp"),
        Index("idx_status", "status"),
    )

    def to_event(self) -> ExecutionEvent:
        """Convert DB model to ExecutionEvent."""
        return ExecutionEvent(
            event_id=self.event_id,
            request_id=self.request_id,
            parent_event_id=self.parent_event_id,
            timestamp=self.timestamp,
            duration_ms=self.duration_ms,
            component=self.component,
            action=self.action,
            status=EventStatus(self.status),
            tokens_used=self.tokens_used,
            cost=self.cost,
            latency_ms=self.latency_ms,
            metadata=self.metadata_json or {},
            error=self.error,
            created_at=self.created_at,
            indexed=True,
        )

    @staticmethod
    def from_event(event: ExecutionEvent) -> "ExecutionEventModel":
        """Create DB model from ExecutionEvent."""
        return ExecutionEventModel(
            event_id=str(event.event_id),
            request_id=str(event.request_id),
            parent_event_id=str(event.parent_event_id) if event.parent_event_id else None,
            timestamp=event.timestamp,
            duration_ms=event.duration_ms,
            component=event.component,
            action=event.action,
            status=event.status.value,
            tokens_used=event.tokens_used,
            cost=event.cost,
            latency_ms=event.latency_ms,
            metadata_json=event.metadata,
            error=event.error,
            created_at=event.created_at,
        )


class EventStore:
    """Service for storing and querying execution events."""

    def __init__(self):
        """Initialize event store (creates tables if needed)."""
        Base.metadata.create_all(engine)
        logger.info("EventStore initialized")

    def store_event(self, event: ExecutionEvent) -> bool:
        """Store an event in the database.

        Args:
            event: ExecutionEvent to store

        Returns:
            True if stored successfully
        """
        try:
            with Session(engine) as session:
                model = ExecutionEventModel.from_event(event)
                session.add(model)
                session.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to store event: {e}", exc_info=True)
            return False

    def store_events(self, events: List[ExecutionEvent]) -> int:
        """Store multiple events.

        Args:
            events: List of ExecutionEvent objects

        Returns:
            Number of events stored
        """
        stored_count = 0
        try:
            with Session(engine) as session:
                for event in events:
                    try:
                        model = ExecutionEventModel.from_event(event)
                        session.add(model)
                        stored_count += 1
                    except Exception as e:
                        logger.error(f"Failed to add event to batch: {e}")
                session.commit()
                return stored_count
        except Exception as e:
            logger.error(f"Failed to store event batch: {e}", exc_info=True)
            return 0

    def get_request_trace(self, request_id: str) -> List[ExecutionEvent]:
        """Get all events for a request (in order).

        Args:
            request_id: Request ID to retrieve

        Returns:
            List of ExecutionEvent objects ordered by timestamp
        """
        try:
            with Session(engine) as session:
                models = (
                    session.query(ExecutionEventModel)
                    .filter(ExecutionEventModel.request_id == request_id)
                    .order_by(ExecutionEventModel.timestamp)
                    .all()
                )
                return [m.to_event() for m in models]
        except Exception as e:
            logger.error(f"Failed to get request trace: {e}", exc_info=True)
            return []

    def get_component_events(
        self,
        request_id: str,
        component: str,
    ) -> List[ExecutionEvent]:
        """Get events for a specific component in a request.

        Args:
            request_id: Request ID
            component: Component name

        Returns:
            List of ExecutionEvent objects
        """
        try:
            with Session(engine) as session:
                models = (
                    session.query(ExecutionEventModel)
                    .filter(
                        ExecutionEventModel.request_id == request_id,
                        ExecutionEventModel.component == component,
                    )
                    .order_by(ExecutionEventModel.timestamp)
                    .all()
                )
                return [m.to_event() for m in models]
        except Exception as e:
            logger.error(f"Failed to get component events: {e}", exc_info=True)
            return []

    def get_trace_metrics(self, request_id: str) -> TraceMetrics:
        """Calculate metrics for a request trace.

        Args:
            request_id: Request ID

        Returns:
            TraceMetrics with aggregated data
        """
        try:
            with Session(engine) as session:
                events = (
                    session.query(ExecutionEventModel)
                    .filter(ExecutionEventModel.request_id == request_id)
                    .all()
                )

                if not events:
                    return TraceMetrics(request_id=request_id)

                # Calculate metrics
                total_tokens = sum(e.tokens_used for e in events)
                total_cost = sum(e.cost for e in events)
                components = set(e.component for e in events)
                agents = set(
                    e.component for e in events if "Agent" in e.component
                )
                tools = set(
                    e.component for e in events if "Tool" in e.component
                )
                errors = len([e for e in events if e.status == "failed"])

                # Calculate total duration
                if events:
                    start = min(e.timestamp for e in events)
                    end = max(e.timestamp for e in events)
                    total_duration_ms = (end - start).total_seconds() * 1000
                else:
                    total_duration_ms = 0.0

                return TraceMetrics(
                    request_id=request_id,
                    total_duration_ms=total_duration_ms,
                    total_tokens=total_tokens,
                    total_cost=total_cost,
                    component_count=len(components),
                    event_count=len(events),
                    agent_count=len(agents),
                    tool_count=len(tools),
                    errors=errors,
                )
        except Exception as e:
            logger.error(f"Failed to get trace metrics: {e}", exc_info=True)
            return TraceMetrics(request_id=request_id)

    def get_recent_requests(
        self,
        limit: int = 50,
        hours: int = 24,
    ) -> List[str]:
        """Get recent request IDs.

        Args:
            limit: Max requests to return
            hours: Only include requests from last N hours

        Returns:
            List of request IDs
        """
        try:
            cutoff = datetime.utcnow() - timedelta(hours=hours)

            with Session(engine) as session:
                results = (
                    session.query(ExecutionEventModel.request_id)
                    .filter(ExecutionEventModel.created_at >= cutoff)
                    .distinct()
                    .order_by(ExecutionEventModel.created_at.desc())
                    .limit(limit)
                    .all()
                )
                return [r[0] for r in results]
        except Exception as e:
            logger.error(f"Failed to get recent requests: {e}", exc_info=True)
            return []

    def delete_old_events(self, days: int = 7) -> int:
        """Delete events older than N days.

        Args:
            days: Delete events older than this many days

        Returns:
            Number of events deleted
        """
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)

            with Session(engine) as session:
                result = session.query(ExecutionEventModel).filter(
                    ExecutionEventModel.created_at < cutoff
                ).delete()
                session.commit()
                logger.info(f"Deleted {result} old events")
                return result
        except Exception as e:
            logger.error(f"Failed to delete old events: {e}", exc_info=True)
            return 0


# Global singleton event store
_event_store: Optional[EventStore] = None


def get_event_store() -> EventStore:
    """Get or create global event store.

    Returns:
        Global EventStore instance
    """
    global _event_store
    if _event_store is None:
        _event_store = EventStore()
    return _event_store
