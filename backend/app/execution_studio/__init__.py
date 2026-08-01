"""Execution Studio - Event-driven AI system visualization platform.

Makes the Enterprise AI system transparent and educational.
Every component publishes events; frontend renders events generically.

Key Components:
- EventBus: Central pub/sub for events
- EventStore: Persistent storage
- Tracer: Decorator for tracing execution
- Learning Explanations: Educational content

Usage:
    # In any component, import tracer
    from app.execution_studio import Tracer, publish_event
    from app.execution_studio.event_model import ExecutionEvent

    # Create tracer with request_id
    tracer = Tracer(request_id="req-123", component="MyComponent")

    # Publish event
    tracer.start_event("my_action", metadata={"key": "value"})
    # ... do work ...
    tracer.end_event(duration_ms=100)

    # Or use context manager
    async with Tracer(...).span("action"):
        # ... work is auto-traced ...
"""

from app.execution_studio.event_model import (
    ExecutionEvent,
    EventStatus,
    TraceMetrics,
    EVENT_ACTIONS,
    KNOWN_COMPONENTS,
)
from app.execution_studio.event_bus import (
    EventBus,
    EventSubscription,
    get_event_bus,
    publish_event,
)
from app.execution_studio.event_store import (
    EventStore,
    ExecutionEventModel,
    get_event_store,
)
from app.execution_studio.tracer import (
    Tracer,
    trace_execution,
    TracingContextManager,
)
from app.execution_studio.learning_explanations import (
    ComponentExplanation,
    COMPONENT_EXPLANATIONS,
    ACTION_EXPLANATIONS,
    get_component_explanation,
    get_action_explanation,
)

__all__ = [
    # Event Model
    "ExecutionEvent",
    "EventStatus",
    "TraceMetrics",
    "EVENT_ACTIONS",
    "KNOWN_COMPONENTS",

    # Event Bus
    "EventBus",
    "EventSubscription",
    "get_event_bus",
    "publish_event",

    # Event Store
    "EventStore",
    "ExecutionEventModel",
    "get_event_store",

    # Tracer
    "Tracer",
    "trace_execution",
    "TracingContextManager",

    # Learning
    "ComponentExplanation",
    "COMPONENT_EXPLANATIONS",
    "ACTION_EXPLANATIONS",
    "get_component_explanation",
    "get_action_explanation",
]
