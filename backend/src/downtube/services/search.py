"""Search service: smart search with URL detection + provider search + cover art enrichment."""

import asyncio
from typing import Any

from downtube.providers.registry import find_provider_for_url
from downtube.providers.ytmusic import YtmProvider

_ytm = YtmProvider()

# Keywords that indicate non-song content
_EXCLUDE_KEYWORDS = {
    "podcast", "interview", "full episode", "behind the scenes",
    "documentary", "reaction", "review", "tutorial", "how to",
    "karaoke", "instrumental", "lyrics video", "visualizer",
    "live at", "acoustic cover", "cover by", "remix by",
    "fan made", "fan edit", "tribute", "parody",
}

# Max duration for a song (15 minutes)
_MAX_SONG_DURATION = 900


def _is_url(text: str) -> bool:
    """Check if text looks like a URL."""
    return text.startswith("http://") or text.startswith("https://")


def _is_youtube_url(url: str) -> bool:
    return any(d in url for d in ("youtube.com", "youtu.be", "music.youtube.com"))


def _is_spotify_url(url: str) -> bool:
    return any(d in url for d in ("open.spotify.com", "spotify.link"))


def _parse_duration_to_seconds(duration: Any) -> int | None:
    """Parse duration string (e.g., '3:45', '225', or '3 min 45 sec') to seconds."""
    if isinstance(duration, (int, float)):
        return int(duration)
    if not isinstance(duration, str):
        return None

    # Handle "X min Y sec" format from YTMusic
    if "min" in duration or "sec" in duration:
        total = 0
        if "min" in duration:
            parts = duration.split("min")
            try:
                total += int(parts[0].strip()) * 60
            except ValueError:
                pass
            if len(parts) > 1 and "sec" in parts[1]:
                try:
                    total += int(parts[1].split("sec")[0].strip())
                except ValueError:
                    pass
            return total if total > 0 else None

    # Handle "M:SS" or "H:MM:SS" format
    parts = duration.split(":")
    try:
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except (ValueError, TypeError):
        return None
    return None


def _is_valid_song(item: dict[str, Any]) -> bool:
    """Check if a search result is a valid song (not podcast, cover, etc.)."""
    title = (item.get("title") or "").lower()
    artist = (item.get("artist") or "").lower()
    full_text = f"{title} {artist}"

    # Check exclude keywords
    for kw in _EXCLUDE_KEYWORDS:
        if kw in full_text:
            return False

    # Check duration (podcasts are typically > 15 min)
    duration = _parse_duration_to_seconds(item.get("duration"))
    if duration and duration > _MAX_SONG_DURATION:
        return False

    # Must have a title
    if not item.get("title"):
        return False

    return True


async def _fetch_url_metadata(url: str) -> dict[str, Any] | None:
    """Fetch metadata for a URL (YouTube or Spotify)."""
    try:
        # YouTube URLs
        if _is_youtube_url(url):
            provider = find_provider_for_url(url)
            if provider and hasattr(provider, 'get_info'):
                info = await provider.get_info(url)
                vid = info.get("id", "")
                cover = f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg" if vid else None
                return {
                    "id": vid,
                    "title": info.get("title") or "untitled",
                    "artist": info.get("artist") or info.get("uploader"),
                    "album": info.get("album"),
                    "duration": info.get("duration_string") or str(info.get("duration", "")),
                    "type": "song",
                    "url": url,
                    "thumbnail": cover or info.get("thumbnail"),
                    "year": str(info.get("upload_date", ""))[:4] if info.get("upload_date") else None,
                    "track_count": None,
                }

        # Spotify URLs
        if _is_spotify_url(url):
            from downtube.providers.spotify_embed import is_spotify, scrape_track
            if is_spotify(url):
                meta = await scrape_track(url)
                duration_sec = meta.get("duration", 0)
                m, s = divmod(int(duration_sec), 60)
                duration_str = f"{m}:{s:02d}"
                return {
                    "id": meta.get("song_id", ""),
                    "title": meta.get("name", "untitled"),
                    "artist": meta.get("artist", ""),
                    "album": meta.get("album_name"),
                    "duration": duration_str,
                    "type": "song",
                    "url": url,
                    "thumbnail": meta.get("cover_url"),
                    "year": meta.get("release_date", "")[:4] if meta.get("release_date") else None,
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


async def search(
    query: str, kind: str = "song", limit: int = 20
) -> list[dict[str, Any]]:
    """Smart search: URL detection + YTMusic search + filtering.

    Search only uses YTMusic for song queries (not yt-dlp which returns everything).
    Results are filtered to exclude podcasts, covers, karaoke, etc.
    Cover art comes directly from YTMusic thumbnails (1:1 square, ~720x720).
    MusicBrainz enrichment happens in pipeline CoverStage, not here.
    """
    if _is_url(query):
        meta = await _fetch_url_metadata(query)
        return [meta] if meta else []

    # Search only YTMusic for songs (more reliable, official results)
    try:
        results = await _ytm.search(query, kind="songs", limit=limit * 2)
    except Exception:
        results = []

    # Filter out non-song content
    filtered = [r for r in results if _is_valid_song(r)]

    # Mark cover source
    for item in filtered:
        if item.get("thumbnail"):
            item["cover_source"] = "ytmusic"

    return filtered[:limit]
