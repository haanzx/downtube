"""Download pipeline: explicit stages for the download process.

5-stage pipeline:
1. Resolve: Spotify embed → metadata + YTMusic duration match / YouTube direct info
2. Download: yt-dlp audio download
3. Lyrics: Fetch synced/plain lyrics
4. Cover: MusicBrainz upgrade (keep search thumbnail as baseline)
5. Tag: mutagen metadata embedding

Cover art priority: Spotify embed > MusicBrainz CAA > Search thumbnail (1:1 square).
Do NOT use YouTube 16:9 thumbnails as fallback.
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field
from typing import Any, Callable

from downtube.config import settings
from downtube.db.models import QueueItem
from downtube.db.session import SessionLocal
from downtube.providers.base import TrackMetadata
from downtube.providers.ytdlp import YtdlpProvider

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
    loop: asyncio.AbstractEventLoop | None = None

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
    """Resolve URL to metadata and download URL.

    For Spotify: scrape embed page → duration match → YTMusic
    For YouTube: direct info fetch
    """

    name = "resolving"
    phase_label = "Mengambil info..."

    async def run(self, ctx: PipelineContext) -> None:
        from downtube.providers.spotify_embed import is_spotify, scrape_track
        from downtube.providers.ytmusic import YtmProvider

        url = ctx.item.url

        if is_spotify(url):
            # 1. Scrape Spotify embed page (cepat, ~0.5 detik)
            meta = await scrape_track(url)

            # 2. Search YTMusic by duration (cepat, ~1 detik)
            ytm = YtmProvider()
            yt_match = await ytm.search_by_duration(
                meta["name"],
                meta["artists"][0] if meta["artists"] else "",
                meta["duration"],
            )

            if not yt_match:
                raise ValueError(
                    f"Tidak bisa mencocokkan ke YouTube: {meta['artist']} - {meta['name']}"
                )

            # 3. Set download URL + metadata
            ctx.download_url = f"https://www.youtube.com/watch?v={yt_match['id']}"
            ctx.meta = TrackMetadata(
                title=meta["name"],
                artist=meta["artist"],
                album=meta.get("album_name"),
                cover_url=meta.get("cover_url"),
                cover_source="spotify",
                duration=meta.get("duration"),
                release_date=meta.get("release_date"),
                source_id=meta.get("song_id"),
                provider="spotify",
            )

            await ctx.update_metadata(
                title=meta["name"],
                artist=meta["artist"],
                album=meta.get("album_name"),
                source_id=meta.get("song_id"),
                cover_url=meta.get("cover_url"),
            )
        else:
            # YouTube URL - direct info fetch
            ytdlp = YtdlpProvider()
            ctx.info = await ytdlp.get_info(url)
            ctx.download_url = url

            artist = ctx.info.get("artist") or ctx.info.get("uploader")
            title = ctx.info.get("title") or "untitled"
            display = f"{artist} - {title}" if artist else title
            vid = ctx.info.get("id", "")

            # Use cover_url from QueueItem (search thumbnail, 1:1 square)
            # Do NOT fallback to YouTube 16:9 thumbnail
            cover_url = ctx.item.cover_url or None
            cover_source = "ytmusic" if cover_url else None

            ctx.meta = TrackMetadata(
                title=title,
                artist=artist,
                album=ctx.info.get("album"),
                album_artist=artist,
                track_number=_to_int(ctx.info.get("track_number")),
                disc_number=_to_int(ctx.info.get("disc_number")),
                genre=ctx.info.get("genre"),
                release_date=ctx.info.get("upload_date"),
                cover_url=cover_url,
                cover_source=cover_source,
                duration=ctx.info.get("duration"),
                source_id=vid,
                provider="ytdlp",
            )

            await ctx.update_metadata(
                title=display,
                artist=artist,
                album=ctx.info.get("album"),
                source_id=ctx.info.get("id"),
                cover_url=cover_url,
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
            if ctx.emit and ctx.loop:
                asyncio.run_coroutine_threadsafe(
                    ctx.emit(ctx.item.id, percent, None, phase),
                    ctx.loop,
                )

        ctx.output_path = await asyncio.to_thread(
            ytdlp.download,
            ctx.download_url,
            out_path,
            ctx.item.format,
            on_progress,
        )


class LyricsStage(PipelineStage):
    """Fetch lyrics for the downloaded track."""

    name = "fetching_lyrics"
    phase_label = "Mengambil lirik..."

    async def run(self, ctx: PipelineContext) -> None:
        from downtube.providers.lyrics import fetch_lyrics, fetch_synced_lyrics

        # Skip if lyrics option is none
        if ctx.item.lyrics_option == "none":
            return

        # Get video_id from context
        video_id = None
        if ctx.meta and ctx.meta.source_id:
            video_id = ctx.meta.source_id
        elif ctx.info.get("id"):
            video_id = ctx.info.get("id")

        # Get title and artist for fallback
        title = ctx.meta.title if ctx.meta else ctx.info.get("title")
        artist = ctx.meta.artist if ctx.meta else (ctx.info.get("artist") or ctx.info.get("uploader"))
        duration = int(ctx.meta.duration) if ctx.meta and ctx.meta.duration else None

        # Fetch plain lyrics (for USLT embed)
        lyrics = await fetch_lyrics(
            video_id=video_id,
            title=title,
            artist=artist,
            duration=duration,
        )

        if lyrics and ctx.meta:
            ctx.meta.lyrics = lyrics

        # Fetch synced lyrics (for LRC file)
        if ctx.item.lyrics_option in ("lrc", "both"):
            synced = await fetch_synced_lyrics(
                video_id=video_id,
                title=title,
                artist=artist,
                duration=duration,
            )
            if synced and ctx.meta:
                ctx.meta.synced_lyrics = synced


class CoverStage(PipelineStage):
    """Fetch cover art with priority chain:
    1. Spotify embed (1:1 square, high quality) — skip if already set
    2. MusicBrainz CAA (full resolution, 1:1 square) — upgrade if found
    3. Keep search thumbnail (1:1 square, ~720x720) — do NOT fallback to YouTube 16:9
    """

    name = "fetching_cover"
    phase_label = "Mengambil cover..."

    async def run(self, ctx: PipelineContext) -> None:
        # 1. Skip if cover is already from Spotify (highest quality, 1:1 square)
        if ctx.meta and ctx.meta.cover_source == "spotify":
            return

        # Skip if no metadata
        if not ctx.meta:
            return

        artist = ctx.meta.artist or ""
        title = ctx.meta.title or ""
        if not title:
            return

        # 2. Try MusicBrainz CAA (full resolution, 1:1 square) — only upgrade
        try:
            from downtube.providers.musicbrainz import musicbrainz_cover
            cover_url = await musicbrainz_cover.search_cover(artist, title)
            if cover_url:
                ctx.meta.cover_url = cover_url
                ctx.meta.cover_source = "musicbrainz"
                async with SessionLocal() as db:
                    item = await db.get(QueueItem, ctx.item.id)
                    if item is not None:
                        item.cover_url = cover_url
                        await db.commit()
                return
        except Exception:
            pass

        # 3. Keep existing cover_url (search thumbnail, 1:1 square)
        # Do NOT fallback to YouTube maxresdefault (16:9)


class MetadataStage(PipelineStage):
    """Write metadata tags to the downloaded audio file."""

    name = "tagging"
    phase_label = "Menulis metadata..."

    async def run(self, ctx: PipelineContext) -> None:
        from downtube.providers.tagger import CoverOption, LyricsOption, write_tags

        # Use metadata from pipeline context if available
        if ctx.meta is None:
            vid = ctx.info.get("id", "")
            # Use cover_url from QueueItem only (search thumbnail, 1:1 square)
            # Do NOT fallback to YouTube 16:9 thumbnail
            cover_url = ctx.item.cover_url or None
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
            # Ensure cover URL exists from QueueItem (search thumbnail)
            # Do NOT fallback to YouTube 16:9 thumbnail
            if not ctx.meta.cover_url:
                ctx.meta.cover_url = ctx.item.cover_url or None

        cover_opt = CoverOption(ctx.item.cover_option)
        lyrics_opt = LyricsOption(ctx.item.lyrics_option)

        def on_tag_phase(phase: str, prog: float) -> None:
            if ctx.emit and ctx.loop:
                asyncio.run_coroutine_threadsafe(
                    ctx.emit(ctx.item.id, prog, None, phase),
                    ctx.loop,
                )

        await asyncio.to_thread(
            write_tags, ctx.output_path, ctx.meta, cover_opt, lyrics_opt, on_tag_phase
        )


class DownloadPipeline:
    """5-stage pipeline: Resolve → Download → Lyrics → Cover → Tag."""

    stages: list[PipelineStage] = [
        ResolveStage(),
        DownloadStage(),
        LyricsStage(),
        CoverStage(),
        MetadataStage(),
    ]

    async def run(
        self,
        item: QueueItem,
        emit: Callable | None = None,
    ) -> None:
        """Run the full pipeline for a queue item."""
        loop = asyncio.get_event_loop()
        ctx = PipelineContext(item=item, emit=emit, loop=loop)

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
            "fetching_lyrics": 88.0,
            "fetching_cover": 90.0,
            "tagging": 92.0,
        }
        return progress_map.get(stage_name, 0.0)
