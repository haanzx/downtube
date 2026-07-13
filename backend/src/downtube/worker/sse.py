"""In-memory Server-Sent Events broker for download progress.

A single broker fans progress updates out to all connected SSE clients.
Implemented/used in milestone P1; the skeleton here is import-safe.
"""

import asyncio
from typing import Any


class EventBroker:
    def __init__(self) -> None:
        self._queues: list[asyncio.Queue[dict[str, Any]]] = []

    def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        q: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._queues.append(q)
        return q

    async def publish(self, event: dict[str, Any]) -> None:
        for q in self._queues:
            await q.put(event)

    def unsubscribe(self, q: asyncio.Queue[dict[str, Any]]) -> None:
        if q in self._queues:
            self._queues.remove(q)


broker = EventBroker()
