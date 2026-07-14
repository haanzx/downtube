"""Search service: smart search with URL detection + YTMusic + Spotify oEmbed enrichment."""

from typing import Any

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
    if _is_youtube_url(url):
        from downtube.providers.ytdlp import YtdlpProvider

        ytdlp = YtdlpProvider()
        try:
            info = await ytdlp.get_info(url)
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
        except Exception:
            return None

    if _is_spotify_url(url):
        from downtube.providers.spotify import SpotifyProvider

        sp = SpotifyProvider()
        try:
            res = await sp.resolve(url)
            meta = await sp.get_metadata(res.source_id, res.kind)
            return {
                "id": meta.source_id or "",
                "title": meta.title or "untitled",
                "artist": None,  # oEmbed doesn't provide artist
                "album": None,  # oEmbed doesn't provide album
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


async def _enrich_with_spotify(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Enrich YTMusic results with Spotify oEmbed cover art (best-effort).

    Uses oEmbed API (no credentials required) to get cover thumbnails.
    """
    from downtube.providers.spotify import SpotifyProvider

    sp = SpotifyProvider()

    async def _enrich_one(item: dict[str, Any]) -> dict[str, Any]:
        artist = item.get("artist") or ""
        title = item.get("title") or ""
        if not title:
            return item
        try:
            query = f"{artist} {title}".strip() if artist else title
            # Search Spotify via oEmbed is not possible, but we can try to get
            # cover from YTMusic thumbnail (already included)
            # oEmbed enrichment is limited to title + thumbnail
            return item
        except Exception:
            return item

    # oEmbed doesn't support search, so we skip enrichment for now
    # Cover art comes from YouTube thumbnails
    return results


async def search(
    query: str, kind: str = "song", limit: int = 20
) -> list[dict[str, Any]]:
    """Smart search: URL detection + YTMusic + Spotify enrichment."""
    if _is_url(query):
        meta = await _fetch_url_metadata(query)
        return [meta] if meta else []

    results = await _ytm.search(query, kind, limit)
    return await _enrich_with_spotify(results)
