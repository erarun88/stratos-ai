"""Execution Studio - Tracer

Decorator and utilities for tracing component execution.
Automatically publishes events to event bus.
"""

import logging
import time
import functools
from typing import Callable, Any, Optional, Dict
from contextlib import asynccontextmanager

from app.execution_studio.event_model import ExecutionEvent, EventStatus
from app.execution_studio.event_bus import get_event_bus, publish_event
from app.execution_studio.event_store import get_event_store

logger = logging.getLogger(__name__)


class Tracer:
    """Utility for tracing component execution.

    Usage:
        tracer = Tracer(request_id="req-123", component="SupervisorAgent")

        tracer.start_event("route_query", metadata={"query": "..."})
        # ... do work ...
        tracer.end_event(duration_ms=100)
    """

    def __init__(
        self,
        request_id: str,
        component: str,
        parent_event_id: Optional[str] = None,
    ):
        """Initialize tracer.

        Args:
            request_id: Unique request ID (trace ID)
            component: Component name
            parent_event_id: Parent event ID for nesting
        """
        self.request_id = request_id
        self.component = component
        self.parent_event_id = parent_event_id
        self.current_event: Optional[ExecutionEvent] = None
        self.bus = get_event_bus()
        self.store = get_event_store()

    def start_event(
        self,
        action: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExecutionEvent:
        """Start a new event.

        Args:
            action: Action name (e.g., "route_query")
            metadata: Optional metadata

        Returns:
            ExecutionEvent
        """
        self.current_event = ExecutionEvent(
            request_id=self.request_id,
            parent_event_id=self.parent_event_id,
            component=self.component,
            action=action,
            status=EventStatus.STARTED,
            metadata=metadata or {},
        )

        # Publish to bus (non-blocking)
        self.bus.publish(self.current_event)

        logger.debug(
            f"Trace started: {self.component}.{action} (request={self.request_id[:8]}...)"
        )

        return self.current_event

    def end_event(
        self,
        duration_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExecutionEvent:
        """End current event (mark as completed).

        Args:
            duration_ms: How long the event took
            metadata: Optional additional metadata

        Returns:
            ExecutionEvent
        """
        if not self.current_event:
            logger.warning("end_event called without start_event")
            return None

        # Update event
        self.current_event.status = EventStatus.COMPLETED
        self.current_event.duration_ms = duration_ms

        if metadata:
            self.current_event.metadata.update(metadata)

        # Publish updated event to bus
        self.bus.publish(self.current_event)

        # Store in database asynchronously
        self.store.store_event(self.current_event)

        logger.debug(
            f"Trace completed: {self.component}.{self.current_event.action} "
            f"({duration_ms:.1f}ms)"
        )

        return self.current_event

    def fail_event(self, error: str) -> ExecutionEvent:
        """Mark current event as failed.

        Args:
            error: Error message

        Returns:
            ExecutionEvent
        """
        if not self.current_event:
            logger.warning("fail_event called without start_event")
            return None

        self.current_event.status = EventStatus.FAILED
        self.current_event.error = error

        # Publish to bus
        self.bus.publish(self.current_event)

        # Store in database
        self.store.store_event(self.current_event)

        logger.error(
            f"Trace failed: {self.component}.{self.current_event.action} - {error}"
        )

        return self.current_event

    @asynccontextmanager
    async def span(
        self,
        action: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Context manager for tracing (async).

        Usage:
            tracer = Tracer(request_id, "MyComponent")
            async with tracer.span("my_action", {"key": "value"}):
                # ... do work ...
                # Event automatically started/completed
        """
        start_time = time.time()
        event = self.start_event(action, metadata)

        try:
            yield event
        except Exception as e:
            self.fail_event(str(e))
            raise
        else:
            duration_ms = (time.time() - start_time) * 1000
            self.end_event(duration_ms)


def trace_execution(
    component: str,
    action: str,
) -> Callable:
    """Decorator for tracing function execution.

    Automatically publishes start/end events.

    Usage:
        @trace_execution("MyComponent", "my_action")
        async def my_function(request_id: str, ...):
            # ... implementation ...
            return result

    The decorated function must have `request_id` parameter.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            # Extract request_id from kwargs or first arg
            request_id = kwargs.get("request_id")
            if not request_id:
                # Try to find in kwargs with different name
                if "trace_id" in kwargs:
                    request_id = kwargs["trace_id"]

            if not request_id:
                logger.warning(
                    f"trace_execution: no request_id found for {component}.{action}"
                )
                return await func(*args, **kwargs)

            # Create tracer and execute with tracing
            tracer = Tracer(request_id, component)
            start_time = time.time()

            try:
                tracer.start_event(action)
                result = await func(*args, **kwargs)

                duration_ms = (time.time() - start_time) * 1000
                tracer.end_event(duration_ms, metadata={"result_type": type(result).__name__})

                return result

            except Exception as e:
                tracer.fail_event(str(e))
                raise

        return async_wrapper

    return decorator


class TracingContextManager:
    """Context manager for tracing blocks of code.

    Usage:
        async with TracingContextManager(
            request_id="req-123",
            component="MyComponent",
            action="do_work"
        ) as tracer:
            # ... do work ...
            tracer.add_metadata("key", value)
    """

    def __init__(
        self,
        request_id: str,
        component: str,
        action: str,
        metadata: Optional[Dict[str, Any]] = None,
        parent_event_id: Optional[str] = None,
    ):
        self.request_id = request_id
        self.component = component
        self.action = action
        self.metadata = metadata or {}
        self.parent_event_id = parent_event_id
        self.tracer = None
        self.start_time = None

    async def __aenter__(self):
        self.start_time = time.time()
        self.tracer = Tracer(
            self.request_id,
            self.component,
            self.parent_event_id,
        )
        self.tracer.start_event(self.action, self.metadata)
        return self.tracer

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.tracer.fail_event(f"{exc_type.__name__}: {exc_val}")
            return False
        else:
            duration_ms = (time.time() - self.start_time) * 1000
            self.tracer.end_event(duration_ms)
            return True
