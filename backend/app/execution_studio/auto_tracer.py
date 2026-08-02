"""Execution Studio - Auto-tracing decorator using async context.

Allows components to emit events without explicitly passing request_id
through every function. Uses async context to thread request_id.
"""

import asyncio
import logging
import time
from functools import wraps
from typing import Any, Callable, Optional

from app.execution_studio.event_model import ExecutionEvent, EventStatus
from app.execution_studio.event_bus import get_event_bus
from app.execution_studio.event_store import get_event_store
from app.execution_studio.trace_context import (
    get_request_id,
    get_parent_event_id,
    push_event_id,
    pop_event_id,
)

logger = logging.getLogger(__name__)


def auto_trace(
    component: str,
    action: str,
):
    """Decorator to automatically emit execution events with request_id from context.

    Usage:
        @auto_trace(component="ProjectAgent", action="query_project")
        async def query_project(self, project_id: int):
            ...

    The decorator automatically:
    - Gets request_id from async context
    - Publishes start event
    - Measures execution time
    - Publishes completion or error event
    - Handles both sync and async functions

    Args:
        component: Component name (e.g., "ProjectAgent", "LLMClient")
        action: Action name (e.g., "query_project", "generate")
    """
    def decorator(func: Callable) -> Callable:
        is_async = asyncio.iscoroutinefunction(func)

        if is_async:
            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                request_id = get_request_id()
                bus = get_event_bus()
                store = get_event_store()
                start_time = time.time()
                event_id = None

                # Publish start event
                if request_id:
                    start_event = ExecutionEvent(
                        request_id=request_id,
                        parent_event_id=get_parent_event_id(),
                        component=component,
                        action=action,
                        metadata={"function": func.__name__}
                    )
                    event_id = start_event.event_id
                    bus.publish(start_event)
                    push_event_id(str(event_id))  # Push as parent for nested events

                try:
                    # Execute function
                    result = await func(*args, **kwargs)

                    # Publish completion event
                    if request_id:
                        elapsed_ms = (time.time() - start_time) * 1000
                        end_event = ExecutionEvent(
                            event_id=event_id,
                            request_id=request_id,
                            parent_event_id=get_parent_event_id(),
                            component=component,
                            action=action,
                            status=EventStatus.COMPLETED,
                            duration_ms=elapsed_ms,
                            metadata={
                                "function": func.__name__,
                                "result_type": type(result).__name__
                            }
                        )
                        bus.publish(end_event)
                        store.store_event(end_event)

                    return result

                except Exception as e:
                    # Publish error event
                    if request_id:
                        elapsed_ms = (time.time() - start_time) * 1000
                        error_event = ExecutionEvent(
                            event_id=event_id,
                            request_id=request_id,
                            parent_event_id=get_parent_event_id(),
                            component=component,
                            action=action,
                            status=EventStatus.FAILED,
                            duration_ms=elapsed_ms,
                            error=str(e),
                            metadata={
                                "function": func.__name__,
                                "error_type": type(e).__name__
                            }
                        )
                        bus.publish(error_event)
                        store.store_event(error_event)

                    raise

                finally:
                    # Pop the event ID from the stack when done
                    if event_id:
                        pop_event_id()

            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                request_id = get_request_id()
                bus = get_event_bus()
                store = get_event_store()
                start_time = time.time()
                event_id = None

                # Publish start event
                if request_id:
                    start_event = ExecutionEvent(
                        request_id=request_id,
                        parent_event_id=get_parent_event_id(),
                        component=component,
                        action=action,
                        metadata={"function": func.__name__}
                    )
                    event_id = start_event.event_id
                    bus.publish(start_event)
                    push_event_id(str(event_id))  # Push as parent for nested events

                try:
                    # Execute function
                    result = func(*args, **kwargs)

                    # Publish completion event
                    if request_id:
                        elapsed_ms = (time.time() - start_time) * 1000
                        end_event = ExecutionEvent(
                            event_id=event_id,
                            request_id=request_id,
                            parent_event_id=get_parent_event_id(),
                            component=component,
                            action=action,
                            status=EventStatus.COMPLETED,
                            duration_ms=elapsed_ms,
                            metadata={
                                "function": func.__name__,
                                "result_type": type(result).__name__
                            }
                        )
                        bus.publish(end_event)
                        store.store_event(end_event)

                    return result

                except Exception as e:
                    # Publish error event
                    if request_id:
                        elapsed_ms = (time.time() - start_time) * 1000
                        error_event = ExecutionEvent(
                            event_id=event_id,
                            request_id=request_id,
                            parent_event_id=get_parent_event_id(),
                            component=component,
                            action=action,
                            status=EventStatus.FAILED,
                            duration_ms=elapsed_ms,
                            error=str(e),
                            metadata={
                                "function": func.__name__,
                                "error_type": type(e).__name__
                            }
                        )
                        bus.publish(error_event)
                        store.store_event(error_event)

                    raise

                finally:
                    # Pop the event ID from the stack when done
                    if event_id:
                        pop_event_id()

            return sync_wrapper

    return decorator


def emit_event(
    component: str,
    action: str,
    status: EventStatus = EventStatus.COMPLETED,
    duration_ms: float = 0.0,
    metadata: Optional[dict] = None,
    error: Optional[str] = None,
) -> bool:
    """Manually emit an execution event using request_id from context.

    Sets parent_event_id automatically if there's a parent in the event stack.

    Args:
        component: Component name
        action: Action name
        status: Event status (default: COMPLETED)
        duration_ms: Duration in milliseconds
        metadata: Optional metadata dict
        error: Optional error message

    Returns:
        True if event was emitted, False if no request_id in context
    """
    request_id = get_request_id()
    if not request_id:
        return False

    bus = get_event_bus()
    store = get_event_store()

    event = ExecutionEvent(
        request_id=request_id,
        parent_event_id=get_parent_event_id(),
        component=component,
        action=action,
        status=status,
        duration_ms=duration_ms,
        metadata=metadata or {},
        error=error,
    )

    bus.publish(event)
    store.store_event(event)
    return True
