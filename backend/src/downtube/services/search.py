from typing import Any

from downtube.config import settings
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
                "artist": meta.artist,
                "album": meta.album,
                "duration": _format_duration(meta.duration),
                "type": meta.provider or "spotify",
                "url": url,
                "thumbnail": meta.cover_url,
                "year": meta.release_date[:4] if meta.release_date else None,
                "track_count": meta.track_count,
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


def _has_spotify_config() -> bool:
    return bool(settings.spotify_client_id and settings.spotify_client_secret)


async def _enrich_with_spotify(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Enrich YTMusic results with Spotify metadata (best-effort)."""
    if not _has_spotify_config():
        return results

    from downtube.providers.spotify import SpotifyProvider

    sp = SpotifyProvider()

    async def _enrich_one(item: dict[str, Any]) -> dict[str, Any]:
        artist = item.get("artist") or ""
        title = item.get("title") or ""
        if not artist or not title:
            return item
        try:
            sp_meta = await sp.search_track(artist, title)
            if not sp_meta:
                return item
            merged = dict(item)
            if not merged.get("album") and sp_meta.album:
                merged["album"] = sp_meta.album
            if not merged.get("thumbnail") and sp_meta.cover_url:
                merged["thumbnail"] = sp_meta.cover_url
            if sp_meta.track_number:
                merged["track_number"] = sp_meta.track_number
            if sp_meta.disc_number:
                merged["disc_number"] = sp_meta.disc_number
            if sp_meta.release_date:
                merged["year"] = sp_meta.release_date[:4]
            if sp_meta.duration and not merged.get("duration"):
                merged["duration"] = _format_duration(sp_meta.duration)
            merged["spotify_metadata"] = True
            return merged
        except Exception:
            return item

    import asyncio

    enriched = await asyncio.gather(*[_enrich_one(r) for r in results[:10]])
    return list(enriched) + list(results[10:])


async def search(
    query: str, kind: str = "song", limit: int = 20
) -> list[dict[str, Any]]:
    """Smart search: URL detection + YTMusic + Spotify enrichment."""
    if _is_url(query):
        meta = await _fetch_url_metadata(query)
        return [meta] if meta else []

    results = await _ytm.search(query, kind, limit)
    return await _enrich_with_spotify(results)
