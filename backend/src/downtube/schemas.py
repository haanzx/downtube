from typing import Any

from pydantic import BaseModel


class DownloadRequest(BaseModel):
    url: str
    title: str | None = None
    artist: str | None = None
    album: str | None = None
    format: str | None = None
    quality: str | None = None
    cover_option: str | None = None
    lyrics_option: str | None = None


class SearchRequest(BaseModel):
    q: str
    type: str = "song"
    limit: int = 20


class SettingsUpdate(BaseModel):
    settings: dict[str, Any] = {}
