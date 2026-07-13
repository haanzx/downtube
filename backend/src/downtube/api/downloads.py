import json

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from downtube.db.session import get_db
from downtube.schemas import DownloadRequest
from downtube.services import download as download_service
from downtube.worker.sse import broker

router = APIRouter(prefix="/downloads", tags=["downloads"])


@router.get("")
async def list_downloads(db: AsyncSession = Depends(get_db)) -> list:
    items = await download_service.list_queue(db)
    return [
        {
            "id": it.id,
            "url": it.url,
            "title": it.title,
            "artist": it.artist,
            "album": it.album,
            "status": it.status.value,
            "progress": it.progress,
            "phase": it.phase,
            "error": it.error,
            "format": it.format,
            "output_path": it.output_path,
            "cover_url": it.cover_url,
            "provider": it.provider,
            "created_at": it.created_at.isoformat() if it.created_at else None,
        }
        for it in items
    ]


@router.post("")
async def create_download(
    payload: DownloadRequest, db: AsyncSession = Depends(get_db)
) -> dict:
    item = await download_service.enqueue(db, payload)
    return {
        "id": item.id,
        "url": item.url,
        "title": item.title,
        "artist": item.artist,
        "album": item.album,
        "status": item.status.value,
        "format": item.format,
    }


@router.delete("/{item_id}")
async def delete_download(item_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    ok = await download_service.delete_item(db, item_id)
    if not ok:
        raise HTTPException(404, "Item tidak ditemukan")
    return {"ok": True}


@router.post("/{item_id}/retry")
async def retry_download(item_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    ok = await download_service.retry_item(db, item_id)
    if not ok:
        raise HTTPException(404, "Item tidak ditemukan")
    return {"ok": True}


@router.get("/events")
async def events(request: Request):
    async def event_stream():
        queue = broker.subscribe()
        try:
            while True:
                if await request.is_disconnected():
                    break
                event = await queue.get()
                yield f"data: {json.dumps(event)}\n\n"
        finally:
            broker.unsubscribe(queue)

    return StreamingResponse(event_stream(), media_type="text/event-stream")
