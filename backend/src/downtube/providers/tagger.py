"""mutagen-based tagging: embed metadata, cover art, and lyrics.

`write_tags()` writes normalized tags (title, artist, album, etc.) plus
optional cover art and lyrics (embedded USLT and/or sidecar .lrc) into
an audio file.

Cover art is cached in SQLite to reduce RAM usage on low-power devices.
"""

import asyncio
import urllib.request
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from downtube.providers.base import TrackMetadata


class CoverOption(str, Enum):
    EMBED = "embed"
    FILE = "file"
    BOTH = "both"
    NONE = "none"


class LyricsOption(str, Enum):
    EMBED = "embed"
    LRC = "lrc"
    BOTH = "both"
    NONE = "none"


def write_tags(
    file_path: str,
    meta: TrackMetadata,
    cover_option: CoverOption = CoverOption.EMBED,
    lyrics_option: LyricsOption = LyricsOption.EMBED,
    on_phase=None,
) -> None:
    """Write normalized tags (and optionally cover/lyrics) into the audio file."""
    if on_phase:
        on_phase("writing metadata", 91)
    audio = _load_audio(file_path)
    if audio is None:
        return

    _write_base_tags(audio, meta)

    if cover_option in (CoverOption.EMBED, CoverOption.BOTH):
        cover_data = None
        if meta.cover_url:
            if on_phase:
                on_phase("embedding cover", 93)
            cover_data = _fetch_cover_cached(meta.cover_url)
        if cover_data:
            _embed_cover(audio, cover_data)

    audio.save()

    if cover_option in (CoverOption.FILE, CoverOption.BOTH) and meta.cover_url:
        cover_data = _fetch_cover_cached(meta.cover_url)
        if cover_data:
            _save_cover_file(file_path, cover_data)

    if lyrics_option in (LyricsOption.LRC, LyricsOption.BOTH) and meta.lyrics:
        if on_phase:
            on_phase("embedding lyrics", 95)
        _write_lrc(file_path, meta)

    if lyrics_option in (LyricsOption.EMBED, LyricsOption.BOTH) and meta.lyrics:
        _embed_lyrics(file_path, meta.lyrics)


def _load_audio(file_path: str) -> Any:
    from mutagen import File

    try:
        return File(file_path, easy=False)
    except Exception:
        return None


def _write_base_tags(audio: Any, meta: TrackMetadata) -> None:
    from mutagen.id3 import ID3

    tags_map: dict[str, Any] = {}
    if meta.title:
        tags_map["title"] = meta.title
    if meta.artist:
        tags_map["artist"] = meta.artist
    if meta.album:
        tags_map["album"] = meta.album
    if meta.album_artist:
        tags_map["albumartist"] = meta.album_artist
    if meta.genre:
        tags_map["genre"] = meta.genre
    if meta.release_date:
        tags_map["date"] = meta.release_date

    fmt = type(audio).__name__

    if fmt == "MP3":
        if not isinstance(audio.tags, ID3):
            audio.add_tags()
        t = audio.tags
        if meta.title:
            t.add(_tcon("TIT2", meta.title))
        if meta.artist:
            t.add(_tcon("TPE1", meta.artist))
        if meta.album:
            t.add(_tcon("TALB", meta.album))
        if meta.album_artist:
            t.add(_tcon("TPE2", meta.album_artist))
        if meta.genre:
            t.add(_tcon("TCON", meta.genre))
        if meta.release_date:
            t.add(_tcon("TDRC", meta.release_date))
        if meta.track_number:
            t.add(_tcon("TRCK", str(meta.track_number)))
        if meta.disc_number:
            t.add(_tcon("TPOS", str(meta.disc_number)))
    elif fmt == "MP4":
        if audio.tags is None:
            audio.add_tags()
        t = audio.tags
        if meta.title:
            t["\xa9nam"] = [meta.title]
        if meta.artist:
            t["\xa9ART"] = [meta.artist]
        if meta.album:
            t["\xa9alb"] = [meta.album]
        if meta.album_artist:
            t["aART"] = [meta.album_artist]
        if meta.genre:
            t["\xa9gen"] = [meta.genre]
        if meta.release_date:
            t["\xa9day"] = [meta.release_date]
        if meta.track_number:
            t["trkn"] = [(meta.track_number, 0)]
        if meta.disc_number:
            t["disk"] = [(meta.disc_number, 0)]
    elif fmt == "FLAC":
        if audio.tags is None:
            audio.add_tags()
        t = audio.tags
        if meta.title:
            t["title"] = meta.title
        if meta.artist:
            t["artist"] = meta.artist
        if meta.album:
            t["album"] = meta.album
        if meta.album_artist:
            t["albumartist"] = meta.album_artist
        if meta.genre:
            t["genre"] = meta.genre
        if meta.release_date:
            t["date"] = meta.release_date
        if meta.track_number:
            t["tracknumber"] = str(meta.track_number)
        if meta.disc_number:
            t["discnumber"] = str(meta.disc_number)
    elif fmt == "OggOpus":
        if audio.tags is None:
            audio.add_tags()
        t = audio.tags
        if meta.title:
            t["title"] = meta.title
        if meta.artist:
            t["artist"] = meta.artist
        if meta.album:
            t["album"] = meta.album
        if meta.album_artist:
            t["albumartist"] = meta.album_artist
        if meta.genre:
            t["genre"] = meta.genre
        if meta.release_date:
            t["date"] = meta.release_date
        if meta.track_number:
            t["tracknumber"] = str(meta.track_number)
        if meta.disc_number:
            t["discnumber"] = str(meta.disc_number)
    else:
        for key, val in tags_map.items():
            try:
                audio[key] = val
            except Exception:
                pass


def _tcon(tag_name: str, value: str):

    frame_map = {
        "TIT2": "TIT2",
        "TPE1": "TPE1",
        "TALB": "TALB",
        "TPE2": "TPE2",
        "TCON": "TCON",
        "TDRC": "TDRC",
        "TRCK": "TRCK",
        "TPOS": "TPOS",
    }
    import importlib

    mod = importlib.import_module("mutagen.id3")
    cls = getattr(mod, frame_map.get(tag_name, "TIT2"))
    return cls(encoding=3, text=value)


def _embed_cover(audio: Any, data: bytes) -> None:
    from mutagen.id3 import ID3, APIC
    from mutagen.mp4 import MP4Cover
    from mutagen.flac import Picture
    import base64

    fmt = type(audio).__name__
    if fmt == "MP3":
        if not isinstance(audio.tags, ID3):
            audio.add_tags()
        audio.tags.add(
            APIC(encoding=3, mime="image/jpeg", type=3, desc="Cover", data=data)
        )
    elif fmt == "MP4":
        if audio.tags is None:
            audio.add_tags()
        audio.tags["covr"] = [MP4Cover(data, imageformat=MP4Cover.FORMAT_JPEG)]
    elif fmt == "FLAC":
        pic = Picture()
        pic.type = 3
        pic.mime = "image/jpeg"
        pic.desc = "Cover"
        pic.data = data
        audio.clear_pictures()
        audio.add_picture(pic)
    elif fmt == "OggOpus":
        pic = Picture()
        pic.type = 3
        pic.mime = "image/jpeg"
        pic.desc = "Cover"
        pic.data = data
        pic_block = pic.write()
        b64 = base64.b64encode(pic_block).decode()
        if audio.tags is None:
            audio.add_tags()
        audio.tags["METADATA_BLOCK_PICTURE"] = [b64]


def _embed_lyrics(file_path: str, lyrics: str) -> None:
    from mutagen.id3 import ID3, USLT

    audio = _load_audio(file_path)
    if audio is None:
        return
    fmt = type(audio).__name__
    if fmt == "MP3":
        if not isinstance(audio.tags, ID3):
            audio.add_tags()
        audio.tags.add(USLT(encoding=3, lang="eng", desc="", text=lyrics))
        audio.save()


def _write_lrc(file_path: str, meta: TrackMetadata) -> None:
    if not meta.lyrics:
        return
    p = Path(file_path)
    lrc_path = p.with_suffix(".lrc")
    lines = []
    if meta.title or meta.artist:
        lines.append(f"[ti:{meta.title or ''}]")
        lines.append(f"[ar:{meta.artist or ''}]")
    lines.append(meta.lyrics)
    lrc_path.write_text("\n".join(lines), encoding="utf-8")


def _save_cover_file(file_path: str, data: bytes) -> None:
    p = Path(file_path)
    cover = p.with_name(p.stem + ".jpg")
    cover.write_bytes(data)


async def _check_cover_cache(url: str) -> bytes | None:
    """Check SQLite cache for cover art."""
    from downtube.db.session import SessionLocal
    from sqlalchemy import text

    async with SessionLocal() as db:
        result = await db.execute(
            text("SELECT data FROM cover_cache WHERE url = :url"), {"url": url}
        )
        row = result.fetchone()
        if row:
            return row[0]
    return None


async def _save_cover_cache(url: str, data: bytes) -> None:
    """Save cover art to SQLite cache."""
    from downtube.db.session import SessionLocal
    from sqlalchemy import text

    async with SessionLocal() as db:
        await db.execute(
            text("INSERT OR REPLACE INTO cover_cache (url, data, created_at) VALUES (:url, :data, :created_at)"),
            {"url": url, "data": data, "created_at": datetime.utcnow()}
        )
        await db.commit()


def _fetch_cover_cached(url: str) -> bytes | None:
    """Fetch cover art with SQLite cache to reduce RAM usage on low-power devices."""
    try:
        # Check cache first
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                cached_data = loop.run_until_complete(_check_cover_cache(url))
                loop.close()
            else:
                cached_data = loop.run_until_complete(_check_cover_cache(url))
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            cached_data = loop.run_until_complete(_check_cover_cache(url))
            loop.close()

        if cached_data:
            return cached_data

        # Fetch from URL
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = resp.read()

        # Save to cache
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(_save_cover_cache(url, data))
                loop.close()
            else:
                loop.run_until_complete(_save_cover_cache(url, data))
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_save_cover_cache(url, data))
            loop.close()

        return data

    except Exception:
        return None


def _fetch_cover(url: str) -> bytes | None:
    """Legacy function for backward compatibility."""
    return _fetch_cover_cached(url)
