"""Queue processor: consumes pending QueueItems and runs the download pipeline.

Started once at app startup (lifespan). Polls the database for pending items
and processes up to `concurrency` of them in parallel. Progress is written to
the database and fanned out to SSE clients via the in-memory broker.
"""

import asyncio
import re
from typing import Any

from downtube.config import settings
from downtube.db.models import QueueItem, QueueStatus
from downtube.db.repositories import queue as queue_repo
from downtube.db.session import SessionLocal
from downtube.providers.ytdlp import YtdlpProvider
from downtube.worker.sse import broker

_UNSAFE = re.compile(r'[\\/:*?"<>|]')


def _safe_name(value: str) -> str:
    cleaned = _UNSAFE.sub("_", value).strip().strip(".")
    return cleaned[:120] or "untitled"


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
        self._provider = YtdlpProvider()

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

    async def _update_metadata(
        self, item_id: int, title: str | None, artist: str | None, album: str | None, source_id: str | None, cover_url: str | None = None
    ) -> None:
        async with SessionLocal() as db:
            item = await db.get(QueueItem, item_id)
            if item is None:
                return
            if title:
                item.title = title
            if artist:
                item.artist = artist
            if album:
                item.album = album
            if source_id:
                item.source_id = source_id
            if cover_url:
                item.cover_url = cover_url
            await db.commit()

    async def _process(self, item: QueueItem) -> None:
        loop = asyncio.get_event_loop()

        def on_progress(percent: float | None, phase: str | None) -> None:
            asyncio.run_coroutine_threadsafe(
                self._emit(item.id, percent, None, phase), loop
            )

        try:
            await self._emit(item.id, 5.0, QueueStatus.DOWNLOADING, "resolving")

            from downtube.providers.base import TrackMetadata
            from downtube.providers.router import provider_for_url
            from downtube.providers.spotify import SpotifyProvider
            from downtube.providers.tagger import (
                CoverOption,
                LyricsOption,
                write_tags,
            )

            provider_name = provider_for_url(item.url)
            info: dict = {}
            meta: TrackMetadata | None = None

            if provider_name == "spotify":
                sp = SpotifyProvider()
                meta, yt_url = await sp.resolve_and_match(item.url)
                if not yt_url:
                    raise ValueError(
                        f"Tidak bisa mencocokkan ke YouTube: {meta.artist} - {meta.title}"
                    )
                info = await self._provider.get_info(yt_url)
                download_url = yt_url
                await self._update_metadata(
                    item.id,
                    title=meta.title or None,
                    artist=meta.artist or None,
                    album=meta.album or None,
                    source_id=info.get("id"),
                    cover_url=meta.cover_url,
                )
            else:
                info = await self._provider.get_info(item.url)
                download_url = item.url
                artist = info.get("artist") or info.get("uploader")
                title = info.get("title") or "untitled"
                display = f"{artist} - {title}" if artist else title
                vid = info.get("id", "")
                yt_cover = f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg" if vid else None
                await self._update_metadata(
                    item.id,
                    title=display,
                    artist=artist,
                    album=info.get("album"),
                    source_id=info.get("id"),
                    cover_url=yt_cover,
                )

            await self._emit(item.id, 10.0, None, "downloading")

            base = _safe_name(item.title or info.get("title", "untitled"))
            out_path = settings.music_root / base
            final = await asyncio.to_thread(
                self._provider.download,
                download_url,
                out_path,
                item.format,
                on_progress,
            )

            await self._emit(item.id, 87.0, None, "transcoding")

            vid = info.get("id", "")

            if meta is None:
                cover_url = f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg" if vid else None
                meta = TrackMetadata(
                    title=info.get("title"),
                    artist=info.get("artist") or info.get("uploader"),
                    album=info.get("album"),
                    album_artist=info.get("artist") or info.get("uploader"),
                    track_number=_to_int(info.get("track_number")),
                    disc_number=_to_int(info.get("disc_number")),
                    genre=info.get("genre"),
                    release_date=info.get("upload_date"),
                    cover_url=cover_url,
                    duration=info.get("duration"),
                    source_id=vid,
                    provider="ytdlp",
                )
            else:
                if not meta.cover_url and vid:
                    meta.cover_url = f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"

            cover_opt = CoverOption(item.cover_option)
            lyrics_opt = LyricsOption(item.lyrics_option)

            def on_tag_phase(phase: str, prog: float) -> None:
                asyncio.run_coroutine_threadsafe(
                    self._emit(item.id, prog, None, phase), loop
                )

            await asyncio.to_thread(
                write_tags, final, meta, cover_opt, lyrics_opt, on_tag_phase
            )

            await self._emit(item.id, 100.0, QueueStatus.DONE, "done")
            async with SessionLocal() as db:
                row = await db.get(QueueItem, item.id)
                if row is not None:
                    row.output_path = final
                    await db.commit()
            await broker.publish(
                {
                    "id": item.id,
                    "progress": 100.0,
                    "status": QueueStatus.DONE.value,
                    "phase": "done",
                    "phase_label": "Selesai",
                    "output_path": final,
                }
            )
        except Exception as exc:  # noqa: BLE001
            await self._emit(item.id, None, QueueStatus.ERROR, "error")
            async with SessionLocal() as db:
                row = await db.get(QueueItem, item.id)
                if row is not None:
                    row.error = str(exc)[:500]
                    await db.commit()
            await broker.publish(
                {"id": item.id, "status": QueueStatus.ERROR.value, "phase": "error"}
            )


def _to_int(val: Any) -> int | None:
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


processor = QueueProcessor()
