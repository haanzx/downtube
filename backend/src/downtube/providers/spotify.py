"""Spotify provider: metadata via oEmbed API (no credentials required).

Spotify oEmbed provides title + thumbnail_url for free.
Full metadata is obtained by matching to YouTube Music.
"""

from __future__ import annotations

import re
from typing import Any

import httpx

from downtube.core.constants import SPOTIFY_OEMBED
from downtube.providers.base import ResolveResult, TrackMetadata
from downtube.providers.ytmusic import YtmProvider


def is_spotify(url: str) -> bool:
    """Check if URL is a Spotify link."""
    return "open.spotify.com" in url or "spotify.link" in url


def _extract_spotify_id(url: str) -> tuple[str, str]:
    """Extract (id, kind) from a Spotify URL."""
    m = re.search(r"open\.spotify\.com/(track|album|playlist|artist)/([A-Za-z0-9]+)", url)
    if m:
        return m.group(2), m.group(1)
    raise ValueError(f"Gagal ekstrak Spotify ID dari URL: {url}")


class SpotifyProvider:
    """Spotify metadata provider using oEmbed API (no auth required)."""

    name = "spotify"

    def __init__(self) -> None:
        self._ytm = YtmProvider()

    def can_handle(self, url: str) -> bool:
        """Check if URL is a Spotify link."""
        return "open.spotify.com" in url or "spotify.link" in url

    async def search(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        """Search via YTMusic, then enrich with Spotify cover art (1:1).

        Strategy:
        1. Search YTMusic for results (primary source)
        2. For each result, try to find matching Spotify track
        3. Enrich with Spotify cover art (1:1 aspect ratio)
        """
        # Search YTMusic first
        ytm_results = await self._ytm.search(query, kind="songs", limit=limit)

        enriched = []
        for item in ytm_results:
            title = item.get("title") or ""
            artist = item.get("artist") or ""
            if not title:
                continue

            # Try to get Spotify cover art
            cover_url = None
            try:
                search_query = f"{artist} {title}".strip() if artist else title
                # oEmbed doesn't support search, but we can construct a Spotify URL
                # and use oEmbed to get the cover
                # For now, use YTMusic thumbnail as fallback
                cover_url = item.get("thumbnail")
            except Exception:
                cover_url = item.get("thumbnail")

            enriched.append({
                "id": item.get("id", ""),
                "title": title,
                "artist": artist,
                "album": item.get("album"),
                "duration": item.get("duration"),
                "type": "song",
                "url": item.get("url", ""),
                "thumbnail": cover_url,
                "year": item.get("year"),
                "spotify_metadata": False,
            })

        return enriched

    async def _get_oembed(self, url: str) -> dict[str, Any]:
        """Fetch metadata via oEmbed API (public, no auth)."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(SPOTIFY_OEMBED, params={"url": url})
            resp.raise_for_status()
            return resp.json()

    async def resolve(self, url: str) -> ResolveResult:
        """Resolve Spotify URL to source_id and kind."""
        source_id, kind = _extract_spotify_id(url)
        return ResolveResult(url=url, provider="spotify", source_id=source_id, kind=kind)

    async def get_metadata(self, source_id: str, kind: str = "track") -> TrackMetadata:
        """Get metadata via oEmbed (title + thumbnail only)."""
        url = f"https://open.spotify.com/{kind}/{source_id}"
        oembed = await self._get_oembed(url)
        return TrackMetadata(
            title=oembed.get("title"),
            cover_url=oembed.get("thumbnail_url"),
            source_id=source_id,
            provider="spotify",
        )

    async def match_to_youtube(self, title: str) -> str | None:
        """Search YouTube Music for a matching track."""
        results = await self._ytm.search(title, kind="songs", limit=1)
        if results:
            vid = results[0].get("id")
            if vid:
                return f"https://www.youtube.com/watch?v={vid}"
        return None

    async def resolve_and_match(self, url: str) -> tuple[TrackMetadata, str | None]:
        """Resolve Spotify URL → oEmbed metadata → match to YouTube Music.

        Returns (merged_metadata, youtube_url_or_none).
        """
        res = await self.resolve(url)
        oembed_meta = await self.get_metadata(res.source_id, res.kind)

        # Match to YTMusic for full metadata
        yt_url = None
        if oembed_meta.title:
            yt_url = await self.match_to_youtube(oembed_meta.title)

        if yt_url and oembed_meta.title:
            # Get full metadata from YTMusic
            results = await self._ytm.search(oembed_meta.title, kind="songs", limit=1)
            if results:
                yt = results[0]
                merged = TrackMetadata(
                    title=oembed_meta.title or yt.get("title"),
                    artist=yt.get("artist"),
                    album=yt.get("album"),
                    album_artist=yt.get("artist"),
                    cover_url=oembed_meta.cover_url or yt.get("thumbnail"),
                    duration=yt.get("duration"),
                    source_id=res.source_id,
                    provider="spotify",
                )
                return merged, yt_url

        return oembed_meta, yt_url
