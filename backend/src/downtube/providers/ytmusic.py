"""YouTube Music search + metadata via ytmusicapi.

`search()` maps the filter to ytmusicapi's `filter` param and normalises
results for the frontend. ytmusicapi is imported lazily so the module
can be imported without the dependency installed at import-time.
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


class YtmProvider:
    name = "ytmusic"

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
            }
            for t in raw
            if t.get("videoId")
        ]

    async def resolve(self, url: str) -> Any:
        raise NotImplementedError

    async def download(self, url: str, out_path: str, on_progress: Any) -> str:
        raise NotImplementedError
