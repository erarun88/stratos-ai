"""Execution Studio - Request tracing context.

Enables automatic event emission throughout the call stack by maintaining
request_id in async context. Components can emit events without explicitly
passing request_id through every function call.
"""

import contextvars
from typing import Optional

# Async context variable to hold the current request_id
_request_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    'request_id',
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
