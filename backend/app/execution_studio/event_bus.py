"""Execution Studio - Event Bus

Central pub/sub system for execution events.
Components publish events; subscribers receive them.
Non-blocking, failure-safe.
"""

import asyncio
import logging
from typing import Callable, Set, Dict, List
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.execution_studio.event_model import ExecutionEvent

logger = logging.getLogger(__name__)


@dataclass
class EventSubscription:
    """A subscription to events."""
    subscriber_id: str
    callback: Callable
    request_id_filter: str = None  # Filter to specific request
    component_filter: str = None   # Filter to specific component


class EventBus:
    """Central event bus for execution tracing.

    Components publish events; subscribers receive them.
    Thread-safe, non-blocking, failure-safe.

    Usage:
        bus = EventBus()

        # Subscribe to all events
        bus.subscribe("my_listener", on_event)

        # Publish event
        event = ExecutionEvent(
            request_id="req-123",
            component="SupervisorAgent",
            action="route_query"
        )
        bus.publish(event)
    """

    def __init__(self):
        """Initialize event bus."""
        self.subscriptions: Dict[str, List[EventSubscription]] = {}
        self.recent_events: List[ExecutionEvent] = []
        self.max_recent = 1000
        logger.info("EventBus initialized")

    def subscribe(
        self,
        subscriber_id: str,
        callback: Callable,
        request_id_filter: str = None,
        component_filter: str = None,
    ) -> None:
        """Subscribe to events.

        Args:
            subscriber_id: Unique subscriber ID (e.g., "websocket_conn_123")
            callback: Async function called when event published
            request_id_filter: Only get events for this request (optional)
            component_filter: Only get events from this component (optional)
        """
        subscription = EventSubscription(
            subscriber_id=subscriber_id,
            callback=callback,
            request_id_filter=request_id_filter,
            component_filter=component_filter,
        )

        if subscriber_id not in self.subscriptions:
            self.subscriptions[subscriber_id] = []

        self.subscriptions[subscriber_id].append(subscription)
        logger.debug(
            f"Subscribed: {subscriber_id} "
            f"(request={request_id_filter}, component={component_filter})"
        )

    def unsubscribe(self, subscriber_id: str) -> bool:
        """Unsubscribe from events.

        Args:
            subscriber_id: Subscriber to remove

        Returns:
            True if subscriber was subscribed
        """
        if subscriber_id in self.subscriptions:
            del self.subscriptions[subscriber_id]
            logger.debug(f"Unsubscribed: {subscriber_id}")
            return True
        return False

    def publish(self, event: ExecutionEvent) -> None:
        """Publish an event.

        Non-blocking. Notifies subscribers asynchronously.

        Args:
            event: ExecutionEvent to publish
        """
        # Store in recent events
        self._add_to_recent(event)

        # Notify subscribers asynchronously
        asyncio.create_task(self._notify_subscribers(event))

        logger.debug(
            f"Published: {event.component}.{event.action} "
            f"(request={event.request_id[:8]}...)"
        )

    async def _notify_subscribers(self, event: ExecutionEvent) -> None:
        """Notify all matching subscribers (async, non-blocking).

        Args:
            event: Event to notify about
        """
        tasks = []

        for subscriber_id, subscriptions in self.subscriptions.items():
            for sub in subscriptions:
                # Check filters
                if sub.request_id_filter and event.request_id != sub.request_id_filter:
                    continue
                if sub.component_filter and event.component != sub.component_filter:
                    continue

                # Call subscriber
                try:
                    tasks.append(sub.callback(event))
                except Exception as e:
                    logger.error(
                        f"Error notifying subscriber {subscriber_id}: {e}",
                        exc_info=True,
                    )

        # Wait for all notifications (with timeout)
        if tasks:
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
            except Exception as e:
                logger.error(f"Error in event notification: {e}", exc_info=True)

    def get_recent_events(
        self,
        request_id: str = None,
        component: str = None,
        limit: int = 100,
    ) -> List[ExecutionEvent]:
        """Get recent events (from memory cache).

        Args:
            request_id: Filter by request ID (optional)
            component: Filter by component (optional)
            limit: Max events to return

        Returns:
            List of ExecutionEvent objects
        """
        events = self.recent_events

        if request_id:
            events = [e for e in events if e.request_id == request_id]

        if component:
            events = [e for e in events if e.component == component]

        return events[-limit:]

    def get_subscription_count(self) -> int:
        """Get total subscription count.

        Returns:
            Number of active subscriptions
        """
        return sum(len(subs) for subs in self.subscriptions.values())

    def clear_subscriptions(self) -> None:
        """Clear all subscriptions (mainly for testing)."""
        self.subscriptions.clear()
        logger.info("Cleared all subscriptions")

    def _add_to_recent(self, event: ExecutionEvent) -> None:
        """Add event to recent events cache.

        Args:
            event: Event to cache
        """
        self.recent_events.append(event)

        # Keep only recent events
        if len(self.recent_events) > self.max_recent:
            self.recent_events = self.recent_events[-self.max_recent :]


# Global singleton event bus
_event_bus: EventBus = None


def get_event_bus() -> EventBus:
    """Get or create global event bus.

    Returns:
        Global EventBus instance
    """
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


async def publish_event(event: ExecutionEvent) -> None:
    """Publish event to global bus.

    Helper function for components.

    Args:
        event: ExecutionEvent to publish
    """
    bus = get_event_bus()
    bus.publish(event)
