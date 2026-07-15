"""Metadata resolver: unified layer for resolving metadata from multiple sources.

Combines metadata from YouTube and Spotify (via embed scraping) into a single
TrackMetadata object. Makes it easy to add new sources (MusicBrainz, Discogs)
in the future.
"""

from __future__ import annotations

from typing import Any

from downtube.providers.base import TrackMetadata


def is_youtube(url: str) -> bool:
    """Check if URL is a YouTube link."""
    return any(d in url for d in ("youtube.com", "youtu.be", "music.youtube.com"))


def is_spotify(url: str) -> bool:
    """Check if URL is a Spotify link."""
    return any(d in url for d in ("open.spotify.com", "spotify.link"))


class MetadataResolver:
    """Unified metadata resolver for multiple sources."""

    async def resolve(self, url: str) -> tuple[TrackMetadata, str | None]:
        """Resolve URL to metadata + optional download URL.

        Returns (metadata, download_url_or_none).
        """
        if is_spotify(url):
            return await self._resolve_spotify(url)
        if is_youtube(url):
            return await self._resolve_youtube(url)
        raise ValueError(f"URL tidak didukung: {url}")

    async def _resolve_spotify(self, url: str) -> tuple[TrackMetadata, str | None]:
        """Resolve Spotify URL: embed scrape → YTMusic match."""
        from downtube.providers.spotify_embed import scrape_track
        from downtube.providers.ytmusic import YtmProvider

        # Scrape Spotify embed page
        meta = await scrape_track(url)

        # Search YTMusic by duration
        ytm = YtmProvider()
        yt_match = await ytm.search_by_duration(
            meta["name"],
            meta["artists"][0] if meta["artists"] else "",
            meta["duration"],
        )

        if not yt_match:
            raise ValueError(f"Tidak bisa mencocokkan ke YouTube: {meta['artist']} - {meta['name']}")

        # Build TrackMetadata
        track_meta = TrackMetadata(
            title=meta["name"],
            artist=meta["artist"],
            album=meta.get("album_name"),
            cover_url=meta.get("cover_url"),
            duration=meta.get("duration"),
            release_date=meta.get("release_date"),
            source_id=meta.get("song_id"),
            provider="spotify",
        )

        return track_meta, f"https://www.youtube.com/watch?v={yt_match['id']}"

    async def _resolve_youtube(self, url: str) -> tuple[TrackMetadata, str | None]:
        """Resolve YouTube URL: yt-dlp info → metadata."""
        from downtube.providers.ytdlp import YtdlpProvider

        ytdlp = YtdlpProvider()
        info = await ytdlp.get_info(url)

        artist = info.get("artist") or info.get("uploader")
        title = info.get("title") or "untitled"
        vid = info.get("id", "")
        cover_url = f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg" if vid else None

        meta = TrackMetadata(
            title=title,
            artist=artist,
            album=info.get("album"),
            album_artist=artist,
            track_number=_to_int(info.get("track_number")),
            disc_number=_to_int(info.get("disc_number")),
            genre=info.get("genre"),
            release_date=info.get("upload_date"),
            cover_url=cover_url,
            duration=info.get("duration"),
            source_id=vid,
            provider="ytdlp",
        )

        return meta, url

    async def get_search_metadata(
        self, results: list[dict[str, Any]], source: str = "ytmusic"
    ) -> list[dict[str, Any]]:
        """Enrich search results with metadata from additional sources."""
        return results


def _to_int(val: Any) -> int | None:
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


# Singleton instance
metadata_resolver = MetadataResolver()
