"""Execution Studio - Request tracing context.

Enables automatic event emission throughout the call stack by maintaining
request_id and event_id_stack in async context. Components can emit events
without explicitly passing these through every function call.
"""

import contextvars
from typing import Optional, List

# Async context variable to hold the current request_id
_request_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    'request_id',
    default=None
)

# Async context variable to hold the stack of event IDs (for parent-child relationships)
_event_id_stack_var: contextvars.ContextVar[Optional[List[str]]] = contextvars.ContextVar(
    'event_id_stack',
    default=None
)


def set_request_id(request_id: str) -> None:
    """Set the request ID in async context.

    Args:
        request_id: The request ID to associate with all subsequent events
    """
    _request_id_var.set(request_id)


def get_request_id() -> Optional[str]:
    """Get the current request ID from async context.

    Returns:
        The request ID if set, None otherwise
    """
    return _request_id_var.get()


def clear_request_id() -> None:
    """Clear the request ID from async context."""
    _request_id_var.set(None)


def push_event_id(event_id: str) -> None:
    """Push an event ID onto the stack (when starting a traced operation).

    Args:
        event_id: The event ID to push as parent for nested events
    """
    stack = _event_id_stack_var.get() or []
    stack = list(stack)  # Copy to avoid mutation
    stack.append(event_id)
    _event_id_stack_var.set(stack)


def pop_event_id() -> Optional[str]:
    """Pop an event ID from the stack (when completing a traced operation).

    Returns:
        The event ID that was popped, or None if stack was empty
    """
    stack = _event_id_stack_var.get() or []
    if stack:
        stack = list(stack)  # Copy to avoid mutation
        event_id = stack.pop()
        _event_id_stack_var.set(stack)
        return event_id
    return None


def get_parent_event_id() -> Optional[str]:
    """Get the current parent event ID (top of stack).

    Returns:
        The parent event ID if one is set, None otherwise
    """
    stack = _event_id_stack_var.get()
    if stack:
        return stack[-1]
    return None


def clear_event_stack() -> None:
    """Clear the event ID stack."""
    _event_id_stack_var.set(None)
