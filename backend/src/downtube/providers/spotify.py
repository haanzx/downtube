"""Spotify provider: metadata only (Client Credentials flow).

Spotify does not expose audio; we resolve metadata here and match the
"artist title" to YouTube Music for the actual download.
"""

from __future__ import annotations

import re
from typing import Any

from downtube.providers.base import ResolveResult, TrackMetadata
from downtube.providers.ytmusic import YtmProvider


def is_spotify(url: str) -> bool:
    return "open.spotify.com" in url or "spotify.link" in url


def _extract_spotify_id(url: str) -> tuple[str, str]:
    """Extract (id, kind) from a Spotify URL."""
    m = re.search(r"open\.spotify\.com/(track|album|playlist|artist)/([A-Za-z0-9]+)", url)
    if m:
        return m.group(2), m.group(1)
    raise ValueError(f"Gagal ekstrak Spotify ID dari URL: {url}")


class SpotifyProvider:
    name = "spotify"

    def __init__(self) -> None:
        self._sp: Any = None
        self._ytm = YtmProvider()

    def _client(self) -> Any:
        if self._sp is not None:
            return self._sp
        from spotipy import Spotify
        from spotipy.oauth2 import SpotifyClientCredentials

        from downtube.config import settings

        if not settings.spotify_client_id or not settings.spotify_client_secret:
            raise ValueError(
                "Spotify CLIENT_ID dan CLIENT_SECRET belum diatur. "
                "Set SPOTIFY_CLIENT_ID dan SPOTIFY_CLIENT_SECRET di .env"
            )
        self._sp = Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=settings.spotify_client_id,
                client_secret=settings.spotify_client_secret,
            )
        )
        return self._sp

    async def resolve(self, url: str) -> ResolveResult:
        source_id, kind = _extract_spotify_id(url)
        return ResolveResult(url=url, provider="spotify", source_id=source_id, kind=kind)

    async def get_metadata(self, source_id: str, kind: str = "track") -> TrackMetadata:
        sp = self._client()
        if kind == "track":
            return await self._get_track_metadata(sp, source_id)
        if kind == "album":
            return await self._get_album_metadata(sp, source_id)
        if kind == "playlist":
            return await self._get_playlist_metadata(sp, source_id)
        raise ValueError(f"Jenis Spotify tidak didukung: {kind}")

    async def _get_track_metadata(self, sp: Any, track_id: str) -> TrackMetadata:
        def _fetch() -> dict:
            return sp.track(track_id)

        track = await _await(_fetch)
        artists = ", ".join(a["name"] for a in track.get("artists", []))
        album = track.get("album", {})
        images = album.get("images", [])
        cover_url = images[0]["url"] if images else None
        release = album.get("release_date", "")
        track_num = track.get("track_number")
        track_total = album.get("total_tracks")
        disc_num = track.get("disc_number", 1)
        duration_ms = track.get("duration_ms")

        return TrackMetadata(
            title=track.get("name"),
            artist=artists,
            album=album.get("name"),
            album_artist=artists,
            track_number=track_num,
            track_count=track_total,
            disc_number=disc_num,
            release_date=release,
            cover_url=cover_url,
            duration=duration_ms / 1000.0 if duration_ms else None,
            source_id=track_id,
            provider="spotify",
        )

    async def _get_album_metadata(self, sp: Any, album_id: str) -> TrackMetadata:
        def _fetch() -> dict:
            return sp.album(album_id)

        album = await _await(_fetch)
        artists = ", ".join(a["name"] for a in album.get("artists", []))
        images = album.get("images", [])
        cover_url = images[0]["url"] if images else None

        return TrackMetadata(
            title=album.get("name"),
            artist=artists,
            album=album.get("name"),
            album_artist=artists,
            track_count=album.get("total_tracks"),
            release_date=album.get("release_date", ""),
            cover_url=cover_url,
            source_id=album_id,
            provider="spotify",
        )

    async def _get_playlist_metadata(self, sp: Any, pl_id: str) -> TrackMetadata:
        def _fetch() -> dict:
            return sp.playlist(pl_id)

        pl = await _await(_fetch)
        owner = pl.get("owner", {}).get("display_name", "")

        return TrackMetadata(
            title=pl.get("name"),
            artist=owner,
            source_id=pl_id,
            provider="spotify",
        )

    async def match_to_youtube(self, artist: str, title: str) -> str | None:
        query = f"{artist} {title}".strip()
        results = await self._ytm.search(query, kind="songs", limit=1)
        if results:
            vid = results[0].get("id")
            if vid:
                return f"https://www.youtube.com/watch?v={vid}"
        return None

    async def search_track(self, artist: str, title: str) -> TrackMetadata | None:
        """Search Spotify for a matching track and return metadata if found."""
        try:
            sp = self._client()
            query = f"{artist} {title}".strip()

            def _search() -> dict | None:
                results = sp.search(q=query, type="track", limit=1)
                tracks = results.get("tracks", {}).get("items", [])
                return tracks[0] if tracks else None

            track = await _await(_search)
            if not track:
                return None

            artists = ", ".join(a["name"] for a in track.get("artists", []))
            album = track.get("album", {})
            images = album.get("images", [])
            cover_url = images[0]["url"] if images else None
            release = album.get("release_date", "")
            track_num = track.get("track_number")
            track_total = album.get("total_tracks")
            disc_num = track.get("disc_number", 1)
            duration_ms = track.get("duration_ms")

            return TrackMetadata(
                title=track.get("name"),
                artist=artists,
                album=album.get("name"),
                album_artist=artists,
                track_number=track_num,
                track_count=track_total,
                disc_number=disc_num,
                release_date=release,
                cover_url=cover_url,
                duration=duration_ms / 1000.0 if duration_ms else None,
                source_id=track.get("id"),
                provider="spotify",
            )
        except Exception:
            return None

    async def resolve_and_match(self, url: str) -> tuple[TrackMetadata, str | None]:
        """Resolve Spotify URL, get metadata, match to YouTube Music.

        Returns (metadata, youtube_url_or_none).
        """
        res = await self.resolve(url)
        meta = await self.get_metadata(res.source_id, res.kind)
        yt_url = None
        if meta.artist and meta.title:
            yt_url = await self.match_to_youtube(meta.artist, meta.title)
        return meta, yt_url


async def _await(fn, *args, **kwargs):
    import asyncio
    return await asyncio.to_thread(fn, *args, **kwargs)
