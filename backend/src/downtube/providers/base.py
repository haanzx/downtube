from dataclasses import dataclass
from typing import Any, Callable, Protocol, runtime_checkable


@dataclass
class TrackMetadata:
    """Normalized metadata shared across providers."""

    title: str | None = None
    artist: str | None = None
    album: str | None = None
    album_artist: str | None = None
    track_number: int | None = None
    track_count: int | None = None
    disc_number: int | None = None
    disc_count: int | None = None
    genre: str | None = None
    release_date: str | None = None
    cover_url: str | None = None
    lyrics: str | None = None
    duration: float | None = None
    source_id: str | None = None
    provider: str | None = None


@dataclass
class ResolveResult:
    url: str
    provider: str
    source_id: str
    kind: str  # "track" | "album" | "playlist" | "artist"
    title: str | None = None


# (percent: float | None, phase: str | None) -> None
ProgressCallback = Callable[[float | None, str | None], Any]


@runtime_checkable
class MusicProvider(Protocol):
    """Protocol for music providers (YouTube, Spotify, etc.)."""

    name: str

    def can_handle(self, url: str) -> bool: ...

    async def search(self, query: str, limit: int = 20) -> list[dict[str, Any]]: ...

    async def resolve(self, url: str) -> ResolveResult: ...

    async def get_metadata(self, source_id: str) -> TrackMetadata: ...

    async def download(
        self, url: str, out_path: str, on_progress: ProgressCallback
    ) -> str: ...
