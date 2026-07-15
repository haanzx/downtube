"""Health check endpoint: comprehensive status of all dependencies."""

import asyncio
import shutil
from pathlib import Path

from fastapi import APIRouter

from downtube.config import settings
from downtube.core.constants import APP_VERSION

router = APIRouter(tags=["health"])


async def _check_database() -> dict:
    """Check SQLite database connectivity."""
    try:
        from sqlalchemy import text
        from downtube.db.session import SessionLocal

        async with SessionLocal() as db:
            await db.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "detail": str(e)[:200]}


async def _check_ffmpeg() -> dict:
    """Check ffmpeg availability."""
    try:
        ffmpeg_path = settings.ffmpeg_path
        if ffmpeg_path == "ffmpeg":
            # Check if ffmpeg is in PATH
            if shutil.which("ffmpeg"):
                return {"status": "ok"}
            return {"status": "error", "detail": "ffmpeg not found in PATH"}
        else:
            # Check custom path
            p = Path(ffmpeg_path)
            if p.exists():
                return {"status": "ok"}
            return {"status": "error", "detail": f"ffmpeg not found at {ffmpeg_path}"}
    except Exception as e:
        return {"status": "error", "detail": str(e)[:200]}


async def _check_ytdlp() -> dict:
    """Check yt-dlp availability."""
    try:
        result = await asyncio.create_subprocess_exec(
            "python", "-m", "yt_dlp", "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await result.communicate()
        if result.returncode == 0:
            version = stdout.decode().strip()
            return {"status": "ok", "version": version}
        return {"status": "error", "detail": "yt-dlp not available"}
    except Exception as e:
        return {"status": "error", "detail": str(e)[:200]}


async def _check_music_dir() -> dict:
    """Check music directory write permission."""
    try:
        import os
        root = settings.music_root
        if not root.exists():
            root.mkdir(parents=True, exist_ok=True)
        if os.access(root, os.W_OK):
            return {"status": "ok", "path": str(root)}
        return {"status": "error", "detail": "No write permission"}
    except Exception as e:
        return {"status": "error", "detail": str(e)[:200]}


@router.get("/health")
async def health():
    """Comprehensive health check."""
    checks = await asyncio.gather(
        _check_database(),
        _check_ffmpeg(),
        _check_ytdlp(),
        _check_music_dir(),
    )

    db_check, ffmpeg_check, ytdlp_check, music_check = checks

    all_ok = all(
        c.get("status") == "ok"
        for c in [db_check, ffmpeg_check, ytdlp_check, music_check]
    )

    return {
        "status": "ok" if all_ok else "degraded",
        "version": APP_VERSION,
        "checks": {
            "database": db_check,
            "ffmpeg": ffmpeg_check,
            "ytdlp": ytdlp_check,
            "music_dir": music_check,
        },
    }
