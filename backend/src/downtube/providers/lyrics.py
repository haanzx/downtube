"""Lyrics provider: fetches lyrics from multiple sources.

Primary: ytmusicapi (YouTube Music lyrics)
Fallback: LRCLIB (lrclib.net - free synced lyrics API)

No credentials required for either source.
"""

from __future__ import annotations

import asyncio
from typing import Optional


async def fetch_lyrics(
    video_id: str | None = None,
    title: str | None = None,
    artist: str | None = None,
    duration: int | None = None,
) -> str | None:
    """Fetch lyrics from available sources.

    Tries ytmusicapi first (if video_id provided), then falls back to LRCLIB.

    Args:
        video_id: YouTube video ID (for ytmusicapi)
        title: Track title (for LRCLIB fallback)
        artist: Artist name (for LRCLIB fallback)
        duration: Duration in seconds (for LRCLIB fallback)

    Returns:
        Plain lyrics text or None
    """
    # Try ytmusicapi first (best coverage)
    if video_id:
        lyrics = await _fetch_ytmusic_lyrics(video_id)
        if lyrics:
            return lyrics

    # Fallback to LRCLIB
    if title and artist:
        lyrics = await _fetch_lrclib_lyrics(title, artist, duration)
        if lyrics:
            return lyrics

    return None


async def fetch_synced_lyrics(
    video_id: str | None = None,
    title: str | None = None,
    artist: str | None = None,
    duration: int | None = None,
) -> str | None:
    """Fetch synced (timed) lyrics for LRC files.

    Tries ytmusicapi first (timestamps=True), then LRCLIB.

    Returns:
        LRC-formatted synced lyrics or None
    """
    # Try ytmusicapi first
    if video_id:
        lyrics = await _fetch_ytmusic_timed_lyrics(video_id)
        if lyrics:
            return _normalize_lrc(lyrics)

    # Fallback to LRCLIB (returns synced LRC directly)
    if title and artist:
        lyrics = await _fetch_lrclib_synced_lyrics(title, artist, duration)
        if lyrics:
            return _normalize_lrc(lyrics)

    return None


def _normalize_lrc(text: str) -> str:
    """Normalize LRC content: fix line endings and strip."""
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


async def _fetch_ytmusic_lyrics(video_id: str) -> str | None:
    """Fetch plain lyrics from YouTube Music."""
    try:
        from downtube.providers.ytmusic import YtmProvider

        ytm = YtmProvider()
        lyrics = await ytm.get_lyrics(video_id)
        return lyrics
    except Exception:
        return None


async def _fetch_ytmusic_timed_lyrics(video_id: str) -> str | None:
    """Fetch timed lyrics from YouTube Music and convert to LRC format."""
    try:
        from downtube.providers.ytmusic import YtmProvider

        ytm = YtmProvider()

        def _fetch() -> str | None:
            try:
                client = ytm._client()
                watch = client.get_watch_playlist(video_id)
                lyrics_browse_id = watch.get("lyrics")
                if not lyrics_browse_id:
                    return None

                # Get timed lyrics
                lyrics = client.get_lyrics(lyrics_browse_id, timestamps=True)
                if not lyrics or not lyrics.hasTimestamps:
                    return None

                # Convert to LRC format
                lines = []
                for line in lyrics.lyrics:
                    start_ms = line.start_time
                    minutes = start_ms // 60000
                    seconds = (start_ms % 60000) // 1000
                    hundredths = (start_ms % 1000) // 10
                    lines.append(f"[{minutes:02d}:{seconds:02d}.{hundredths:02d}]{line.text}")

                return "\n".join(lines) if lines else None
            except Exception:
                return None

        return await asyncio.to_thread(_fetch)
    except Exception:
        return None


async def _fetch_lrclib_lyrics(
    title: str, artist: str, duration: int | None = None
) -> str | None:
    """Fetch plain lyrics from LRCLIB."""
    try:
        import httpx

        params = {"track_name": title, "artist_name": artist}
        if duration:
            params["duration"] = str(duration)

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://lrclib.net/api/get",
                params=params,
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("plainLyrics")
        return None
    except Exception:
        return None


async def _fetch_lrclib_synced_lyrics(
    title: str, artist: str, duration: int | None = None
) -> str | None:
    """Fetch synced LRC lyrics from LRCLIB."""
    try:
        import httpx

        params = {"track_name": title, "artist_name": artist}
        if duration:
            params["duration"] = str(duration)

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://lrclib.net/api/get",
                params=params,
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("syncedLyrics")
        return None
    except Exception:
        return None
