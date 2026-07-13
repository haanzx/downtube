"""Library scanner: walk MUSIC_ROOT, read audio tags via mutagen.

`scan_library()` returns a flat list of audio entries.  The tree structure
(artist → album → tracks) is built client-side for flexibility.
"""

from pathlib import Path

from downtube.config import settings

AUDIO_EXTS = {".mp3", ".m4a", ".flac", ".opus", ".ogg", ".wav", ".aac"}


def scan_library() -> list[dict]:
    root = settings.music_root
    if not root.exists():
        return []
    entries: list[dict] = []
    for p in sorted(root.rglob("*")):
        if p.suffix.lower() not in AUDIO_EXTS or not p.is_file():
            continue
        meta = _read_tags(p)
        rel = str(p.relative_to(root))
        entries.append(
            {
                "path": rel,
                "size": p.stat().st_size,
                "title": meta.get("title") or p.stem,
                "artist": meta.get("artist") or "Unknown Artist",
                "album": meta.get("album") or "Unknown Album",
                "duration": meta.get("duration"),
                "format": p.suffix.lstrip(".").upper(),
            }
        )
    return entries


def _read_tags(path: Path) -> dict:
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
