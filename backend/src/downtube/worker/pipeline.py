"""Download pipeline: explicit stages for the download process.

Each stage is a separate class with a clear responsibility, making
the pipeline easier to debug, test, and extend.
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field
from typing import Any, Callable

from downtube.config import settings
from downtube.db.models import QueueItem, QueueStatus
from downtube.db.session import SessionLocal
from downtube.providers.base import TrackMetadata
from downtube.providers.ytdlp import YtdlpProvider
from downtube.worker.sse import broker

_UNSAFE = re.compile(r'[\\/:*?"<>|]')


def _safe_name(value: str) -> str:
    cleaned = _UNSAFE.sub("_", value).strip().strip(".")
    return cleaned[:120] or "untitled"


def _to_int(val: Any) -> int | None:
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


@dataclass
class PipelineContext:
    """Shared context passed between pipeline stages."""

    item: QueueItem
    info: dict = field(default_factory=dict)
    meta: TrackMetadata | None = None
    download_url: str = ""
    output_path: str = ""
    emit: Callable | None = None

    async def update_metadata(
        self,
        title: str | None = None,
        artist: str | None = None,
        album: str | None = None,
        source_id: str | None = None,
        cover_url: str | None = None,
    ) -> None:
        """Update metadata in database."""
        async with SessionLocal() as db:
            item = await db.get(QueueItem, self.item.id)
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


class PipelineStage:
    """Base class for pipeline stages."""

    name: str = "unknown"
    phase_label: str = ""

    async def run(self, ctx: PipelineContext) -> None:
        raise NotImplementedError


class ResolveStage(PipelineStage):
    """Resolve URL to metadata and download URL."""

    name = "resolving"
    phase_label = "Mengambil info..."

    async def run(self, ctx: PipelineContext) -> None:
        from downtube.providers.router import provider_for_url
        from downtube.providers.spotify import SpotifyProvider

        provider_name = provider_for_url(ctx.item.url)

        if provider_name == "spotify":
            sp = SpotifyProvider()
            meta, yt_url = await sp.resolve_and_match(ctx.item.url)
            if not yt_url:
                raise ValueError(
                    f"Tidak bisa mencocokkan ke YouTube: {meta.artist} - {meta.title}"
                )
            ytdlp = YtdlpProvider()
            ctx.info = await ytdlp.get_info(yt_url)
            ctx.download_url = yt_url
            ctx.meta = meta
            await ctx.update_metadata(
                title=meta.title,
                artist=meta.artist,
                album=meta.album,
                source_id=ctx.info.get("id"),
                cover_url=meta.cover_url,
            )
        else:
            ytdlp = YtdlpProvider()
            ctx.info = await ytdlp.get_info(ctx.item.url)
            ctx.download_url = ctx.item.url

            artist = ctx.info.get("artist") or ctx.info.get("uploader")
            title = ctx.info.get("title") or "untitled"
            display = f"{artist} - {title}" if artist else title
            vid = ctx.info.get("id", "")
            yt_cover = f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg" if vid else None

            await ctx.update_metadata(
                title=display,
                artist=artist,
                album=ctx.info.get("album"),
                source_id=ctx.info.get("id"),
                cover_url=yt_cover,
            )


class DownloadStage(PipelineStage):
    """Download audio via yt-dlp."""

    name = "downloading"
    phase_label = "Mengunduh..."

    async def run(self, ctx: PipelineContext) -> None:
        ytdlp = YtdlpProvider()
        base = _safe_name(ctx.item.title or ctx.info.get("title", "untitled"))
        out_path = settings.music_root / base

        def on_progress(percent: float | None, phase: str | None) -> None:
            if ctx.emit:
                asyncio.run_coroutine_threadsafe(
                    ctx.emit(ctx.item.id, percent, None, phase),
                    asyncio.get_event_loop(),
                )

        ctx.output_path = await asyncio.to_thread(
            ytdlp.download,
            ctx.download_url,
            out_path,
            ctx.item.format,
            on_progress,
        )


class TranscodeStage(PipelineStage):
    """Transcode is handled by yt-dlp internally. This stage is a placeholder."""

    name = "transcoding"
    phase_label = "Transcode audio..."

    async def run(self, ctx: PipelineContext) -> None:
        # yt-dlp handles transcoding during download
        # This stage exists for pipeline completeness
        pass


class MetadataStage(PipelineStage):
    """Write metadata tags to the downloaded audio file."""

    name = "tagging"
    phase_label = "Menulis metadata..."

    async def run(self, ctx: PipelineContext) -> None:
        from downtube.providers.tagger import CoverOption, LyricsOption, write_tags

        vid = ctx.info.get("id", "")

        if ctx.meta is None:
            cover_url = f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg" if vid else None
            ctx.meta = TrackMetadata(
                title=ctx.info.get("title"),
                artist=ctx.info.get("artist") or ctx.info.get("uploader"),
                album=ctx.info.get("album"),
                album_artist=ctx.info.get("artist") or ctx.info.get("uploader"),
                track_number=_to_int(ctx.info.get("track_number")),
                disc_number=_to_int(ctx.info.get("disc_number")),
                genre=ctx.info.get("genre"),
                release_date=ctx.info.get("upload_date"),
                cover_url=cover_url,
                duration=ctx.info.get("duration"),
                source_id=vid,
                provider="ytdlp",
            )
        else:
            if not ctx.meta.cover_url and vid:
                ctx.meta.cover_url = f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"

        cover_opt = CoverOption(ctx.item.cover_option)
        lyrics_opt = LyricsOption(ctx.item.lyrics_option)

        def on_tag_phase(phase: str, prog: float) -> None:
            if ctx.emit:
                asyncio.run_coroutine_threadsafe(
                    ctx.emit(ctx.item.id, prog, None, phase),
                    asyncio.get_event_loop(),
                )

        await asyncio.to_thread(
            write_tags, ctx.output_path, ctx.meta, cover_opt, lyrics_opt, on_tag_phase
        )


class DownloadPipeline:
    """Orchestrates the download pipeline stages."""

    stages: list[PipelineStage] = [
        ResolveStage(),
        DownloadStage(),
        TranscodeStage(),
        MetadataStage(),
    ]

    async def run(
        self,
        item: QueueItem,
        emit: Callable | None = None,
    ) -> None:
        """Run the full pipeline for a queue item."""
        ctx = PipelineContext(item=item, emit=emit)

        for stage in self.stages:
            await self._emit_stage(item.id, stage, emit)
            await stage.run(ctx)

        # Save output path
        async with SessionLocal() as db:
            row = await db.get(QueueItem, item.id)
            if row is not None:
                row.output_path = ctx.output_path
                await db.commit()

    async def _emit_stage(
        self,
        item_id: int,
        stage: PipelineStage,
        emit: Callable | None,
    ) -> None:
        """Emit stage progress."""
        if emit:
            progress = self._stage_progress(stage.name)
            await emit(item_id, progress, None, stage.name)

    def _stage_progress(self, stage_name: str) -> float:
        """Get progress percentage for a stage."""
        progress_map = {
            "resolving": 5.0,
            "downloading": 10.0,
            "transcoding": 87.0,
            "tagging": 92.0,
        }
        return progress_map.get(stage_name, 0.0)
