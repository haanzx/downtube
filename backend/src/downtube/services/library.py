"""Library scanner: walk MUSIC_ROOT, read audio tags via mutagen.

Uses SQLite cache for fast subsequent scans. Only re-reads tags when
file size or mtime has changed.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from downtube.config import settings
from downtube.core.constants import AUDIO_EXTS
from downtube.db.repositories import library as lib_repo
from downtube.db.session import SessionLocal


async def scan_library() -> list[dict]:
    """Scan music directory with cache. Returns list of audio entries."""
    root = settings.music_root
    if not root.exists():
        return []

    async with SessionLocal() as db:
        # Get cached items
        cached = await lib_repo.get_all_items(db)
        cached_map = {item.file_path: item for item in cached}

        # Scan files on disk
        current_paths: set[str] = set()
        entries: list[dict] = []

        for p in sorted(root.rglob("*")):
            if p.suffix.lower() not in AUDIO_EXTS or not p.is_file():
                continue

            rel = str(p.relative_to(root))
            current_paths.add(rel)
            stat = p.stat()

            # Check cache
            if rel in cached_map:
                item = cached_map[rel]
                if item.file_mtime == stat.st_mtime and item.file_size == stat.st_size:
                    entries.append(_item_to_dict(item, rel))
                    continue

            # File new or changed → scan with mutagen
            meta = _read_tags(p)
            await lib_repo.upsert_item(
                db,
                file_path=rel,
                file_size=stat.st_size,
                file_mtime=stat.st_mtime,
                title=meta.get("title"),
                artist=meta.get("artist"),
                album=meta.get("album"),
                duration=meta.get("duration"),
                format=p.suffix.lstrip(".").upper(),
            )
            entries.append(
                {
                    "path": rel,
                    "size": stat.st_size,
                    "title": meta.get("title") or p.stem,
                    "artist": meta.get("artist") or "Unknown Artist",
                    "album": meta.get("album") or "Unknown Album",
                    "duration": meta.get("duration"),
                    "format": p.suffix.lstrip(".").upper(),
                }
            )

        # Remove deleted files from cache
        await lib_repo.delete_items_by_paths(db, current_paths)

    return entries


def _item_to_dict(item: Any, rel_path: str) -> dict:
    """Convert a LibraryItem to a dict for API response."""
    return {
        "path": rel_path,
        "size": item.file_size,
        "title": item.title or Path(rel_path).stem,
        "artist": item.artist or "Unknown Artist",
        "album": item.album or "Unknown Album",
        "duration": item.duration,
        "format": item.format,
    }


def _read_tags(path: Path) -> dict:
    """Read audio tags via mutagen (sync)."""
    try:
        from mutagen import File as MutagenFile

        af = MutagenFile(str(path), easy=True)
        if af is None:
            return {}
        tags = af.tags or {}
        duration = None
        if af.info:
            duration = af.info.length
        return {
            "title": tags.get("title", [None])[0] if tags.get("title") else None,
            "artist": tags.get("artist", [None])[0] if tags.get("artist") else None,
            "album": tags.get("album", [None])[0] if tags.get("album") else None,
            "duration": duration,
        }
    except Exception:
        return {}
