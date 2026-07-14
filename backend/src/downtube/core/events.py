"""Simple in-memory event bus for decoupled communication."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any, Callable, Coroutine


EventHandler = Callable[..., Coroutine[Any, Any, None]]


class EventBus:
    """Pub/sub event bus for decoupled components."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)

    def on(self, event: str, handler: EventHandler) -> None:
        """Register a handler for an event."""
        self._handlers[event].append(handler)

    def off(self, event: str, handler: EventHandler) -> None:
        """Unregister a handler for an event."""
        if handler in self._handlers[event]:
            self._handlers[event].remove(handler)

    async def emit(self, event: str, **kwargs: Any) -> None:
        """Emit an event to all registered handlers."""
        for handler in self._handlers[event]:
            try:
                await handler(**kwargs)
            except Exception:
                pass  # Don't let handler errors propagate


# Global event bus instance
event_bus = EventBus()
