import shutil

from fastapi import APIRouter

from downtube.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    yt_dlp = shutil.which(settings.ytdlp_path) or settings.ytdlp_path
    ffmpeg = shutil.which(settings.ffmpeg_path) or settings.ffmpeg_path
    return {
        "status": "ok",
        "version": "0.1.0",
        "music_root": str(settings.music_root),
        "data_dir": str(settings.data_dir),
        "yt_dlp": yt_dlp,
        "ffmpeg": ffmpeg,
    }
