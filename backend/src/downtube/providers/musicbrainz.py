"""MusicBrainz + Cover Art Archive provider for cover art.

Searches MusicBrainz for release metadata and fetches cover art
from Cover Art Archive (CAA). All images are 1:1 square format.

No credentials required - free and open source.
"""

import asyncio
from typing import Any

import musicbrainzngs

# Set user agent (required by MusicBrainz API)
musicbrainzngs.set_useragent(
    "downtube", "0.2.0", "https://github.com/haanzx/downtube"
)


class MusicBrainzCover:
    """Cover art provider using MusicBrainz + Cover Art Archive."""

    name = "musicbrainz"

    async def search_cover(self, artist: str, title: str) -> str | None:
        """Search for cover art by artist and title.

        Args:
            artist: Artist name
            title: Song/album title

        Returns:
            Cover art URL (500x500 square) or None
        """

        def _search() -> str | None:
            try:
                # 1. Search releases (not release-groups) for better matching
                result = musicbrainzngs.search_releases(
                    artist=artist,
                    release=title,
                    limit=5,  # Get top 5 matches
                )

                if not result.get("release-list"):
                    return None

                # 2. Find best release with cover art
                for release in result["release-list"]:
                    release_mbid = release["id"]
                    cover_url = self._get_cover_art(release_mbid)
                    if cover_url:
                        return cover_url

                return None
            except Exception:
                return None

        return await asyncio.to_thread(_search)

    def _get_cover_art(self, mbid: str) -> str | None:
        """Get cover art URL from Cover Art Archive."""
        try:
            # Check if cover art exists for this release
            cover_data = musicbrainzngs.get_image_list(mbid)

            if not cover_data.get("images"):
                return None

            # Find front cover
            for image in cover_data["images"]:
                if image.get("front"):
                    # Return 500x500 thumbnail
                    return image["thumbnails"].get("500")

            # If no front, return first image
            return cover_data["images"][0]["thumbnails"].get("500")
        except Exception:
            return None


# Singleton instance
musicbrainz_cover = MusicBrainzCover()
