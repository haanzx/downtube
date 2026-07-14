
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse, StreamingResponse

from downtube.config import settings
from downtube.services import library as library_service

router = APIRouter(prefix="/library", tags=["library"])

MIME_MAP = {
    ".mp3": "audio/mpeg",
    ".m4a": "audio/mp4",
    ".flac": "audio/flac",
    ".opus": "audio/opus",
    ".ogg": "audio/ogg",
    ".wav": "audio/wav",
    ".aac": "audio/aac",
}


@router.get("")
async def library() -> list[dict]:
    return await library_service.scan_library()


@router.get("/stream")
async def stream(request: Request, path: str = Query(...)):
    full = (settings.music_root / path).resolve()
    if not str(full).startswith(str(settings.music_root.resolve())):
        raise HTTPException(status_code=403, detail="forbidden")
    if not full.is_file():
        raise HTTPException(status_code=404, detail="file not found")
    mime = MIME_MAP.get(full.suffix.lower(), "application/octet-stream")
    size = full.stat().st_size
    range_header = request.headers.get("range")

    if range_header:
        rng = range_header.replace("bytes=", "").split("-")
        start = int(rng[0]) if rng[0] else 0
        end = int(rng[1]) if rng[1] else size - 1
        end = min(end, size - 1)
        length = end - start + 1

        def ranged():
            with open(full, "rb") as f:
                f.seek(start)
                remaining = length
                while remaining > 0:
                    chunk = f.read(min(8192, remaining))
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    yield chunk

        return StreamingResponse(
            ranged(),
            status_code=206,
            media_type=mime,
            headers={
                "Content-Range": f"bytes {start}-{end}/{size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(length),
            },
        )
    return FileResponse(full, media_type=mime, headers={"Accept-Ranges": "bytes"})
