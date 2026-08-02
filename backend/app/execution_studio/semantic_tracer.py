"""Semantic Execution Tracer - High-level API for semantic event emission.

Makes it easy for components to emit rich, self-describing events.
Handles parent-child relationships, I/O tracking, and narrative building.
"""

import logging
import time
from typing import Any, Dict, Optional, List
from contextlib import asynccontextmanager

from app.execution_studio.semantic_event import (
    SemanticExecutionEvent,
    EventStatus,
    ComponentType,
    RelationshipType,
)
from app.execution_studio.semantic_event_store import get_semantic_event_store
from app.execution_studio.event_bus import get_event_bus
from app.execution_studio.trace_context import (
    get_request_id,
    push_event_id,
    pop_event_id,
    get_parent_event_id,
)

logger = logging.getLogger(__name__)


class SemanticTracer:
    """High-level tracer for emitting semantic execution events.

    Usage:
        tracer = SemanticTracer(
            request_id=request_id,
            component="SupervisorAgent",
            component_type=ComponentType.ORCHESTRATOR,
        )

        event = tracer.start_event(
            action="route_query",
            purpose="Determine which agents should handle this query",
            reason="User asked a question",
        )

        event.with_input(
            input_type="query",
            description="User question about project risks",
            key_fields={"query": query[:100]},
        )

        # ... do work ...

        event.with_output(
            output_type="agent_selection",
            description="Selected RiskAgent and ProjectAgent",
            key_fields={"agents_selected": ["RiskAgent", "ProjectAgent"]},
            confidence=0.95,
        )

        tracer.end_event(event)
    """

    def __init__(
        self,
        request_id: Optional[str] = None,
        component: str = "Unknown",
        component_type: ComponentType = ComponentType.TOOL,
        component_role: str = "",
    ):
        """Initialize tracer.

        Args:
            request_id: Request/trace ID. If None, uses context.
            component: Component name
            component_type: Type of component
            component_role: Role of component
        """
        self.request_id = request_id or get_request_id()
        self.component = component
        self.component_type = component_type
        self.component_role = component_role
        self.store = get_semantic_event_store()
        self.bus = get_event_bus()
        self.events: Dict[str, SemanticExecutionEvent] = {}
        self.start_time = time.time()
        self._sequence_counter = 0

    def start_event(
        self,
        action: str,
        purpose: str,
        reason: str = "",
        description: str = "",
    ) -> SemanticExecutionEvent:
        """Start a new traced event.

        Args:
            action: What action is being performed
            purpose: Why this action exists
            reason: What triggered it
            description: Human-readable narrative

        Returns:
            SemanticExecutionEvent to be enhanced and ended
        """
        request_start = self.start_time
        elapsed_ms = (time.time() - request_start) * 1000

        parent_event_id = get_parent_event_id()

        event = SemanticExecutionEvent.build(
            request_id=str(self.request_id),
            component=self.component,
            component_type=self.component_type,
            action=action,
            purpose=purpose,
            reason=reason,
            description=description,
            parent_event_id=parent_event_id,
        )

        event.component_role = self.component_role
        event.started_relative_ms = elapsed_ms
        event.status = EventStatus.IN_PROGRESS
        event.sequence_in_parent = self._sequence_counter
        self._sequence_counter += 1

        # Track in memory
        self.events[str(event.event_id)] = event

        # Publish start event
        if self.request_id:
            push_event_id(str(event.event_id))

        logger.debug(
            f"Started event: {event.component}::{event.action} "
            f"(purpose={event.purpose[:50]}...)"
        )

        return event

    def end_event(
        self,
        event: SemanticExecutionEvent,
        completed: bool = True,
        error: Optional[str] = None,
    ) -> SemanticExecutionEvent:
        """End a traced event.

        Args:
            event: Event to end
            completed: Whether it completed successfully
            error: Error message if failed

        Returns:
            The completed event
        """
        elapsed_ms = (time.time() - self.start_time) * 1000

        if completed and not error:
            event.mark_completed(duration_ms=elapsed_ms)
        else:
            event.mark_failed(error or "Unknown error")

        # Store event
        self.store.store_event(event)

        # Publish to bus
        try:
            self.bus.publish(event)  # Backwards compat, might need adaptation
        except Exception as e:
            logger.debug(f"Could not publish to event bus: {e}")

        # Pop from event stack
        if self.request_id:
            pop_event_id()

        logger.debug(
            f"Ended event: {event.component}::{event.action} "
            f"({event.status.value}, {event.duration_ms:.1f}ms)"
        )

        return event

    def emit_simple_event(
        self,
        action: str,
        purpose: str,
        description: str = "",
        output_type: str = "result",
        output_description: str = "",
    ) -> SemanticExecutionEvent:
        """Emit a simple completed event in one call.

        Args:
            action: Action performed
            purpose: Why it was done
            description: What happened
            output_type: Type of output
            output_description: Description of output

        Returns:
            The completed event
        """
        event = self.start_event(
            action=action,
            purpose=purpose,
            description=description,
        )

        if output_description:
            event.with_output(
                output_type=output_type,
                description=output_description,
            )

        return self.end_event(event)

    def create_relationship(
        self,
        from_event_id: str,
        to_event_id: str,
        relationship: RelationshipType,
        description: str,
    ) -> bool:
        """Create a relationship between two events (after they're created).

        Args:
            from_event_id: Source event
            to_event_id: Target event
            relationship: Type of relationship
            description: Why this relationship exists

        Returns:
            True if relationship was added
        """
        if from_event_id in self.events:
            event = self.events[from_event_id]
            event.with_related_event(to_event_id, relationship, description)
            self.store.store_event(event)
            return True
        return False


@asynccontextmanager
async def trace_semantic_operation(
    request_id: Optional[str] = None,
    component: str = "Unknown",
    component_type: ComponentType = ComponentType.TOOL,
    action: str = "execute",
    purpose: str = "Execute operation",
    reason: str = "",
):
    """Context manager for tracing a semantic operation.

    Usage:
        async with trace_semantic_operation(
            component="ProjectAgent",
            component_type=ComponentType.SPECIALIST_AGENT,
            action="lookup_project",
            purpose="Retrieve project information",
        ) as event:
            event.with_input("project_id", "Looking up project 123", {"project_id": 123})
            # ... do work ...
            event.with_output("project", "Found project", {"name": "Example"})
    """
    tracer = SemanticTracer(
        request_id=request_id,
        component=component,
        component_type=component_type,
    )

    event = tracer.start_event(
        action=action,
        purpose=purpose,
        reason=reason,
    )

    try:
        yield event
        tracer.end_event(event, completed=True)
    except Exception as e:
        tracer.end_event(event, completed=False, error=str(e))
        raise
