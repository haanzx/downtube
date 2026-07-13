"""Resolve a URL to the appropriate provider.

URL routing: YouTube Music / YouTube -> ytdlp, Spotify -> spotify.
The actual provider instances are wired in services; this module only
classifies the URL so the rest of the code stays provider-agnostic.
"""

from downtube.providers.spotify import is_spotify
from downtube.providers.ytdlp import is_youtube, is_youtube_music


def provider_for_url(url: str) -> str:
    """Return the provider name for a given URL."""
    if is_spotify(url):
        return "spotify"
    if is_youtube(url) or is_youtube_music(url):
        return "ytdlp"
    raise ValueError(f"Unsupported URL: {url}")


def classify(url: str) -> str:
    if "open.spotify.com" in url:
        if "/track/" in url:
            return "track"
        if "/album/" in url:
            return "album"
        if "/playlist/" in url:
            return "playlist"
        if "/artist/" in url:
            return "artist"
    if "music.youtube.com" in url or "youtube.com" in url or "youtu.be" in url:
        if "playlist" in url:
            return "playlist"
        if "/channel/" in url:
            return "artist"
        return "track"
    raise ValueError(f"Unsupported URL: {url}")
