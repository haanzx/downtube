"""mutagen-based tagging: embed metadata, cover art, and lyrics.

`write_tags()` writes normalized tags (title, artist, album, etc.) plus
optional cover art and lyrics (embedded USLT and/or sidecar .lrc) into
an audio file.

Cover art is cached in SQLite to reduce RAM usage on low-power devices.
"""

import sqlite3
import urllib.request
from datetime import datetime, timezone
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

    # Fetch cover once (shared between embed and file)
    cover_data = None
    if cover_option in (CoverOption.EMBED, CoverOption.BOTH, CoverOption.FILE):
        if meta.cover_url:
            if on_phase:
                on_phase("embedding cover", 93)
            cover_data = _fetch_cover_cached(meta.cover_url)

    if cover_option in (CoverOption.EMBED, CoverOption.BOTH) and cover_data:
        _embed_cover(audio, cover_data)

    audio.save()

    if cover_option in (CoverOption.FILE, CoverOption.BOTH) and cover_data:
        _save_cover_file(file_path, cover_data)

    if lyrics_option in (LyricsOption.LRC, LyricsOption.BOTH) and meta.synced_lyrics:
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
    audio = _load_audio(file_path)
    if audio is None:
        return
    fmt = type(audio).__name__

    if fmt == "MP3":
        from mutagen.id3 import ID3, USLT
        if not isinstance(audio.tags, ID3):
            audio.add_tags()
        audio.tags.add(USLT(encoding=3, lang="eng", desc="", text=lyrics))
        audio.save()

    elif fmt == "MP4":
        # M4A/AAC: use iTunes-style lyrics tag
        if audio.tags is None:
            audio.add_tags()
        audio.tags["\xa9lyr"] = lyrics
        audio.save()

    elif fmt == "FLAC":
        # FLAC: use Vorbis comment
        if audio.tags is None:
            audio.add_tags()
        audio.tags["LYRICS"] = lyrics
        audio.save()

    elif fmt == "OggOpus" or fmt == "OggVorbis":
        # Ogg: use Vorbis comment
        if audio.tags is None:
            audio.add_tags()
        audio.tags["LYRICS"] = lyrics
        audio.save()


def _write_lrc(file_path: str, meta: TrackMetadata) -> None:
    if not meta.synced_lyrics:
        return
    p = Path(file_path)
    lrc_path = p.with_suffix(".lrc")
    lines = []
    if meta.title or meta.artist:
        lines.append(f"[ti:{meta.title or ''}]")
        lines.append(f"[ar:{meta.artist or ''}]")
    lines.append(meta.synced_lyrics)
    lrc_path.write_text("\n".join(lines), encoding="utf-8")


def _save_cover_file(file_path: str, data: bytes) -> None:
    p = Path(file_path)
    cover = p.with_name(p.stem + ".jpg")
    cover.write_bytes(data)


def _get_db_path() -> str:
    """Extract SQLite file path from DATABASE_URL."""
    from downtube.config import settings
    url = settings.database_url
    for prefix in ("sqlite+aiosqlite:///./", "sqlite:///./", "sqlite+aiosqlite:///", "sqlite:///"):
        if url.startswith(prefix):
            return url[len(prefix):]
    return url


def _check_cover_cache_sync(url: str) -> bytes | None:
    """Check SQLite cache for cover art (sync version for use in write_tags)."""
    try:
        db_path = _get_db_path()
        conn = sqlite3.connect(db_path, timeout=5)
        cursor = conn.execute("SELECT data FROM cover_cache WHERE url = ?", (url,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None
    except Exception:
        return None


def _save_cover_cache_sync(url: str, data: bytes) -> None:
    """Save cover art to SQLite cache (sync version for use in write_tags)."""
    try:
        db_path = _get_db_path()
        conn = sqlite3.connect(db_path, timeout=5)
        conn.execute(
            "INSERT OR REPLACE INTO cover_cache (url, data, created_at) VALUES (?, ?, ?)",
            (url, data, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass  # Cache failure is non-fatal


def _fetch_cover_cached(url: str) -> bytes | None:
    """Fetch cover art with SQLite cache.

    Priority: cache → URL fetch → resize → save cache.
    Uses sync sqlite3 for cache access (called from write_tags via asyncio.to_thread).
    """
    # 1. Check cache first
    cached = _check_cover_cache_sync(url)
    if cached:
        return cached

    try:
        # 2. Fetch from URL
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = resp.read()

        # 3. Resize if needed (min 500px, max 1500px for low-power devices)
        data = _resize_cover_if_needed(data, min_size=500, max_size=1500)

        # 4. Save to cache
        _save_cover_cache_sync(url, data)

        return data
    except Exception:
        return None


def _resize_cover_if_needed(data: bytes, min_size: int = 500, max_size: int = 1500) -> bytes:
    """Resize cover art to reasonable dimensions.

    - Upscale if smaller than min_size (maintains aspect ratio)
    - Downscale if larger than max_size (saves storage on low-power devices)
    - Output quality: JPEG 95%
    """
    try:
        from io import BytesIO
        from PIL import Image

        img = Image.open(BytesIO(data))
        width, height = img.size

        # Already in good range
        if min_size <= width <= max_size and min_size <= height <= max_size:
            return data

        # Calculate new size maintaining aspect ratio
        if width > max_size or height > max_size:
            # Downscale to max_size
            scale = max_size / max(width, height)
            new_width = int(width * scale)
            new_height = int(height * scale)
        elif width < min_size or height < min_size:
            # Upscale to min_size
            if width < height:
                new_width = min_size
                new_height = int(height * min_size / width)
            else:
                new_height = min_size
                new_width = int(width * min_size / height)
        else:
            return data

        img = img.resize((new_width, new_height), Image.LANCZOS)
        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=95)
        return buffer.getvalue()
    except Exception:
        return data


def _fetch_cover(url: str) -> bytes | None:
    """Legacy function for backward compatibility."""
    return _fetch_cover_cached(url)
