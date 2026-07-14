"""Queue processor: consumes pending QueueItems and runs the download pipeline.

Started once at app startup (lifespan). Polls the database for pending items
and processes up to `concurrency` of them in parallel. Progress is written to
the database and fanned out to SSE clients via the in-memory broker.

Concurrency is controlled via asyncio.Semaphore for low-power device optimization.
"""

import asyncio
from typing import Any

from downtube.config import settings
from downtube.db.models import QueueItem, QueueStatus
from downtube.db.repositories import queue as queue_repo
from downtube.db.session import SessionLocal
from downtube.worker.pipeline import DownloadPipeline
from downtube.worker.sse import broker

PHASE_LABELS = {
    "resolving": "Mengambil info...",
    "downloading": "Mengunduh...",
    "transcoding": "Transcode audio...",
    "embedding cover": "Menanam cover...",
    "embedding lyrics": "Menanam lirik...",
    "writing metadata": "Menulis metadata...",
    "done": "Selesai",
    "error": "Gagal",
}


class QueueProcessor:
    def __init__(self, concurrency: int | None = None) -> None:
        self.concurrency = concurrency or settings.download_concurrency
        self._running = False
        self._task: asyncio.Task | None = None
        self._pipeline = DownloadPipeline()
        self._semaphore = asyncio.Semaphore(self.concurrency)

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _loop(self) -> None:
        while self._running:
            try:
                async with SessionLocal() as db:
                    pending = await queue_repo.list_pending(db, limit=self.concurrency)
            except Exception:
                pending = []
            if not pending:
                await asyncio.sleep(2)
                continue
            await asyncio.gather(*(self._process(item) for item in pending))

    async def _emit(
        self,
        item_id: int,
        progress: float | None,
        status: QueueStatus | None,
        phase: str | None,
    ) -> None:
        async with SessionLocal() as db:
            item = await db.get(QueueItem, item_id)
            if item is None:
                return
            if progress is not None:
                item.progress = progress
            if status is not None:
                item.status = status
            if phase is not None:
                item.phase = phase
            await db.commit()
        await broker.publish(
            {
                "id": item_id,
                "progress": item.progress if progress is None else progress,
                "status": item.status.value if status is not None else "",
                "phase": phase or "",
                "phase_label": PHASE_LABELS.get(phase or "", ""),
            }
        )

    async def _process(self, item: QueueItem) -> None:
        async with self._semaphore:
            try:
                await self._emit(item.id, 5.0, QueueStatus.RESOLVING, "resolving")

                await self._pipeline.run(item, emit=self._emit)

                await self._emit(item.id, 100.0, QueueStatus.DONE, "done")
                async with SessionLocal() as db:
                    row = await db.get(QueueItem, item.id)
                    if row is not None:
                        await db.commit()
                await broker.publish(
                    {
                        "id": item.id,
                        "progress": 100.0,
                        "status": QueueStatus.DONE.value,
                        "phase": "done",
                        "phase_label": "Selesai",
                    }
                )
            except Exception as exc:  # noqa: BLE001
                await self._emit(item.id, None, QueueStatus.FAILED, "error")
                async with SessionLocal() as db:
                    row = await db.get(QueueItem, item.id)
                    if row is not None:
                        row.error = str(exc)[:500]
                        await db.commit()
                await broker.publish(
                    {"id": item.id, "status": QueueStatus.FAILED.value, "phase": "error"}
                )


processor = QueueProcessor()
