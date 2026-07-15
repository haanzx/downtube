"""YouTube Music search + metadata via ytmusicapi.

`search()` maps the filter to ytmusicapi's `filter` param and normalises
results for the frontend. ytmusicapi is imported lazily so the module
can be imported without the dependency installed at import-time.

Includes duration-based audio matching for Spotify→YouTube matching.
"""

from typing import Any

FILTER_MAP = {
    "song": "songs",
    "songs": "songs",
    "album": "albums",
    "albums": "albums",
    "artist": "artists",
    "artists": "artists",
    "playlist": "playlists",
    "playlists": "playlists",
}

TYPE_MAP = {v: k for k, v in FILTER_MAP.items()}


def _thumb_url(thumbnails: list[dict]) -> str | None:
    if not thumbnails:
        return None
    best = sorted(thumbnails, key=lambda t: t.get("width", 0), reverse=True)
    return best[0].get("url")


def _artist_name(item: dict) -> str | None:
    artists = item.get("artists") or []
    if item.get("artist"):
        return item["artist"]
    names = [a.get("name", "") for a in artists if a.get("name")]
    return ", ".join(names) if names else None


def _build_url(item: dict, kind: str) -> str:
    if kind == "artist":
        bid = item.get("browseId", "")
        return f"https://music.youtube.com/channel/{bid}" if bid else ""
    if kind in ("album", "playlist"):
        bid = item.get("browseId", "")
        return f"https://music.youtube.com/playlist?list={bid}" if bid else ""
    vid = item.get("videoId") or item.get("id", "")
    return f"https://music.youtube.com/watch?v={vid}" if vid else ""


def _normalise(item: dict, kind: str) -> dict[str, Any]:
    return {
        "id": item.get("videoId") or item.get("browseId") or item.get("id") or "",
        "title": item.get("title") or item.get("name") or "untitled",
        "artist": _artist_name(item),
        "album": item.get("album", {}).get("title") if isinstance(item.get("album"), dict) else item.get("album"),
        "duration": item.get("duration"),
        "type": kind,
        "url": _build_url(item, kind),
        "thumbnail": _thumb_url(item.get("thumbnails", [])),
        "year": item.get("year"),
        "track_count": item.get("trackCount"),
    }


def _parse_duration_str(duration: Any) -> int | None:
    """Parse duration string (e.g., '3:45' or 225) to seconds."""
    if isinstance(duration, (int, float)):
        return int(duration)
    if not isinstance(duration, str):
        return None

    parts = duration.split(":")
    try:
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except (ValueError, TypeError):
        return None
    return None


class YtmProvider:
    name = "ytmusic"

    def can_handle(self, url: str) -> bool:
        """Check if URL is a YouTube Music link."""
        return "music.youtube.com" in url

    def _client(self) -> Any:
        from ytmusicapi import YTMusic

        return YTMusic()

    def search_sync(
        self, query: str, kind: str = "songs", limit: int = 20
    ) -> list[dict[str, Any]]:
        client = self._client()
        ytm_filter = FILTER_MAP.get(kind, "songs")
        results = client.search(query, filter=ytm_filter, limit=limit)
        return [_normalise(r, kind) for r in results if r]

    async def search(
        self, query: str, kind: str = "songs", limit: int = 20
    ) -> list[dict[str, Any]]:
        import asyncio

        return await asyncio.to_thread(self.search_sync, query, kind, limit)

    async def search_by_duration(
        self,
        title: str,
        artist: str,
        target_duration: int,
        tolerance: int = 10,
    ) -> dict[str, Any] | None:
        """Search YTMusic and match by duration.

        Picks the best result by comparing audio duration.
        Falls back to first result if no exact match.

        Args:
            title: Track title
            artist: Artist name
            target_duration: Target duration in seconds
            tolerance: Duration tolerance in seconds (default: 10)

        Returns:
            Best matching result or None
        """
        query = f"{artist} {title}" if artist else title
        results = await self.search(query, kind="songs", limit=10)

        if not results:
            return None

        # Try to find duration match
        for r in results:
            yt_duration = _parse_duration_str(r.get("duration"))
            if yt_duration is not None and abs(yt_duration - target_duration) <= tolerance:
                return r

        # Fallback to first result
        return results[0]

    async def get_metadata(self, source_id: str) -> Any:
        raise NotImplementedError("metadata via ytmusicapi is implemented in P3")

    async def get_playlist_items(self, playlist_id: str) -> list[dict[str, Any]]:
        def _fetch() -> list[dict]:
            client = self._client()
            result = client.get_playlist(playlist_id, limit=10000)
            return result.get("tracks", [])

        import asyncio

        raw = await asyncio.to_thread(_fetch)
        return [
            {
                "video_id": t.get("videoId", ""),
                "title": t.get("title", ""),
                "artist": _artist_name(t),
                "thumbnail": _thumb_url(t.get("thumbnails", [])),
            }
            for t in raw
            if t.get("videoId")
        ]

    async def get_lyrics(self, video_id: str) -> str | None:
        """Get lyrics for a song by video ID.

        Uses ytmusicapi to fetch lyrics from YouTube Music.
        Returns plain lyrics text or None if not available.
        """
        import asyncio

        def _fetch_lyrics() -> str | None:
            try:
                client = self._client()
                # Get watch playlist to find lyrics browseId
                watch = client.get_watch_playlist(video_id)
                lyrics_browse_id = watch.get("lyrics")
                if not lyrics_browse_id:
                    return None

                # Get lyrics content
                lyrics = client.get_lyrics(lyrics_browse_id)
                if lyrics and lyrics.lyrics:
                    return lyrics.lyrics
                return None
            except Exception:
                return None

        return await asyncio.to_thread(_fetch_lyrics)

    async def resolve(self, url: str) -> Any:
        raise NotImplementedError

    async def download(self, url: str, out_path: str, on_progress: Any) -> str:
        raise NotImplementedError
