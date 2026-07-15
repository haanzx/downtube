"""MusicBrainz + Cover Art Archive provider for cover art and metadata.

Searches MusicBrainz for release metadata and fetches cover art
from Cover Art Archive (CAA). All images are 1:1 square format.

No credentials required - free and open source.

Rate limiting: MusicBrainz allows ~1 request per second.
We use a semaphore to limit concurrent requests and add delay between them.
"""

import asyncio
import time
from typing import Any

import musicbrainzngs

# Set user agent (required by MusicBrainz API)
musicbrainzngs.set_useragent(
    "downtube", "0.2.0", "https://github.com/haanzx/downtube"
)

# Rate limiting: 1 concurrent request, minimum 1 second between requests
_rate_semaphore = asyncio.Semaphore(1)
_last_request_time = 0.0


class MusicBrainzCover:
    """Cover art provider using MusicBrainz + Cover Art Archive."""

    name = "musicbrainz"

    async def search_cover(self, artist: str, title: str) -> str | None:
        """Search for cover art by artist and title.

        Args:
            artist: Artist name
            title: Song/album title

        Returns:
            Cover art URL (full resolution or 500x500) or None
        """

        async def _search_with_rate_limit() -> str | None:
            global _last_request_time
            async with _rate_semaphore:
                # Ensure minimum 1 second between requests
                elapsed = time.monotonic() - _last_request_time
                if elapsed < 1.0:
                    await asyncio.sleep(1.0 - elapsed)

                def _search() -> str | None:
                    global _last_request_time
                    try:
                        result = musicbrainzngs.search_releases(
                            artist=artist,
                            release=title,
                            limit=5,
                        )
                        _last_request_time = time.monotonic()

                        if not result.get("release-list"):
                            return None

                        for release in result["release-list"]:
                            # Validasi judul: harus sama (case-insensitive)
                            release_title = (release.get("title") or "").strip()
                            if release_title.lower() != title.lower():
                                continue

                            # Validasi artis: harus match
                            release_artists = [
                                a.get("name", "").lower()
                                for a in release.get("artist-credit", [])
                            ]
                            if artist.lower() not in release_artists:
                                continue

                            release_mbid = release["id"]
                            cover_url = self._get_cover_art(release_mbid)
                            if cover_url:
                                return cover_url

                        return None
                    except Exception:
                        return None

                return await asyncio.to_thread(_search)

        return await _search_with_rate_limit()

    async def search_metadata(self, artist: str, title: str) -> dict[str, Any] | None:
        """Search for release metadata by artist and title.

        Returns:
            Dict with release_date, album, cover_url or None
        """

        async def _search_with_rate_limit() -> dict[str, Any] | None:
            global _last_request_time
            async with _rate_semaphore:
                elapsed = time.monotonic() - _last_request_time
                if elapsed < 1.0:
                    await asyncio.sleep(1.0 - elapsed)

                def _search() -> dict[str, Any] | None:
                    global _last_request_time
                    try:
                        result = musicbrainzngs.search_releases(
                            artist=artist,
                            release=title,
                            limit=3,
                        )
                        _last_request_time = time.monotonic()

                        if not result.get("release-list"):
                            return None

                        for release in result["release-list"]:
                            metadata: dict[str, Any] = {}

                            date = release.get("date")
                            if date:
                                metadata["release_date"] = date

                            if release.get("title"):
                                metadata["album"] = release["title"]

                            release_mbid = release["id"]
                            cover_url = self._get_cover_art(release_mbid)
                            if cover_url:
                                metadata["cover_url"] = cover_url

                            if metadata:
                                return metadata

                        return None
                    except Exception:
                        return None

                return await asyncio.to_thread(_search)

        return await _search_with_rate_limit()

    def _get_cover_art(self, mbid: str) -> str | None:
        """Get cover art URL from Cover Art Archive.

        Priority: full resolution image > 500px thumbnail > 250px thumbnail.
        CAA API provides full resolution via 'image' field (no upper bound).
        """
        try:
            cover_data = musicbrainzngs.get_image_list(mbid)

            if not cover_data.get("images"):
                return None

            # Find front cover first, fallback to first image
            target = None
            for image in cover_data["images"]:
                if image.get("front"):
                    target = image
                    break
            if not target:
                target = cover_data["images"][0]

            # Priority: full resolution > 500px > 250px
            full_url = target.get("image")
            if full_url:
                return full_url

            thumb_500 = target.get("thumbnails", {}).get("500")
            if thumb_500:
                return thumb_500

            thumb_250 = target.get("thumbnails", {}).get("250")
            if thumb_250:
                return thumb_250

            return None
        except Exception:
            return None


# Singleton instance
musicbrainz_cover = MusicBrainzCover()
