"""Search service: smart search with URL detection + provider search + cover art enrichment."""

import asyncio
from typing import Any

from downtube.providers.registry import all_providers, find_provider_for_url
from downtube.providers.ytmusic import YtmProvider

_ytm = YtmProvider()


def _is_url(text: str) -> bool:
    """Check if text looks like a URL."""
    return text.startswith("http://") or text.startswith("https://")


def _is_youtube_url(url: str) -> bool:
    return any(d in url for d in ("youtube.com", "youtu.be", "music.youtube.com"))


def _is_spotify_url(url: str) -> bool:
    return any(d in url for d in ("open.spotify.com", "spotify.link"))


async def _fetch_url_metadata(url: str) -> dict[str, Any] | None:
    """Fetch metadata for a URL (YouTube or Spotify)."""
    try:
        provider = find_provider_for_url(url)
        if hasattr(provider, 'get_info'):
            info = await provider.get_info(url)
            return {
                "id": info.get("id") or "",
                "title": info.get("title") or "untitled",
                "artist": info.get("artist") or info.get("uploader"),
                "album": info.get("album"),
                "duration": info.get("duration_string") or str(info.get("duration", "")),
                "type": "song",
                "url": url,
                "thumbnail": info.get("thumbnail"),
                "year": str(info.get("upload_date", ""))[:4] if info.get("upload_date") else None,
                "track_count": None,
            }
        elif hasattr(provider, 'resolve'):
            res = await provider.resolve(url)
            meta = await provider.get_metadata(res.source_id)
            return {
                "id": meta.source_id or "",
                "title": meta.title or "untitled",
                "artist": None,
                "album": None,
                "duration": None,
                "type": "spotify",
                "url": url,
                "thumbnail": meta.cover_url,
                "year": None,
                "track_count": None,
            }
    except Exception:
        return None
    return None


def _format_duration(seconds: float | None) -> str | None:
    if not seconds:
        return None
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


async def _enrich_with_cover_art(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Enrich search results with cover art from MusicBrainz + CAA.

    Priority:
    1. MusicBrainz (1:1 square, 500x500)
    2. YouTube Thumbnail (16:9, fallback)
    """
    from downtube.providers.musicbrainz import musicbrainz_cover

    async def _enrich_one(item: dict[str, Any]) -> dict[str, Any]:
        artist = item.get("artist") or ""
        title = item.get("title") or ""
        if not title:
            return item

        # Try MusicBrainz first (1:1 square cover)
        cover_url = await musicbrainz_cover.search_cover(artist, title)
        if cover_url:
            item["thumbnail"] = cover_url
            item["cover_source"] = "musicbrainz"
        else:
            # Fallback to YouTube thumbnail (already in item)
            item["cover_source"] = "youtube"

        return item

    # Enrich all results concurrently
    enriched = await asyncio.gather(*[_enrich_one(item) for item in results])
    return list(enriched)


async def search(
    query: str, kind: str = "song", limit: int = 20
) -> list[dict[str, Any]]:
    """Smart search: URL detection + provider search + cover art enrichment."""
    if _is_url(query):
        meta = await _fetch_url_metadata(query)
        return [meta] if meta else []

    # Search all providers
    all_results = []
    for provider in all_providers():
        try:
            results = await provider.search(query, limit)
            all_results.extend(results)
        except Exception:
            pass

    # Enrich with cover art from MusicBrainz (1:1 square)
    enriched = await _enrich_with_cover_art(all_results)
    return enriched[:limit]
