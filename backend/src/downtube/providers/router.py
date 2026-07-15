"""Resolve a URL to the appropriate provider.

URL routing via provider registry: YouTube -> ytdlp, YouTube Music -> ytmusic, Spotify -> embed scraper.
The actual provider instances are wired in services; this module only
classifies the URL so the rest of the code stays provider-agnostic.
"""

from downtube.providers.registry import find_provider_for_url


def provider_for_url(url: str) -> str:
    """Return the provider name for a given URL."""
    return find_provider_for_url(url).name


def classify(url: str) -> str:
    """Classify the URL type (track, album, playlist, artist)."""
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
