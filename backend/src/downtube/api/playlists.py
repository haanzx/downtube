from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from downtube.db.session import get_db
from downtube.services.playlist import (
    create_playlist,
    delete_playlist,
    get_playlist_items,
    list_playlists,
    sync_playlist,
)
from downtube.config import settings

router = APIRouter(prefix="/playlists", tags=["playlists"])


class PlaylistCreate(BaseModel):
    name: str
    url: str
    format: str = "mp3"


@router.get("")
async def get_playlists(db: AsyncSession = Depends(get_db)):
    items = await list_playlists(db)
    return [
        {
            "id": p.id,
            "name": p.name,
            "url": p.url,
            "format": p.format,
            "last_sync": p.last_sync.isoformat() if p.last_sync else None,
            "created_at": p.created_at.isoformat(),
        }
        for p in items
    ]


@router.post("")
async def add_playlist(body: PlaylistCreate, db: AsyncSession = Depends(get_db)):
    p = await create_playlist(db, body.name, body.url, body.format)
    return {
        "id": p.id,
        "name": p.name,
        "url": p.url,
        "format": p.format,
        "created_at": p.created_at.isoformat(),
    }


@router.delete("/{pid}")
async def remove_playlist(pid: int, db: AsyncSession = Depends(get_db)):
    ok = await delete_playlist(db, pid)
    if not ok:
        raise HTTPException(404, "Playlist tidak ditemukan")
    return {"ok": True}


@router.get("/{pid}/items")
async def playlist_items(pid: int, db: AsyncSession = Depends(get_db)):
    items = await get_playlist_items(db, pid)
    return [
        {
            "id": it.id,
            "video_id": it.video_id,
            "title": it.title,
            "artist": it.artist,
            "output_path": it.output_path,
            "synced_at": it.synced_at.isoformat(),
        }
        for it in items
    ]


@router.post("/{pid}/sync")
async def do_sync(pid: int, db: AsyncSession = Depends(get_db)):
    music_root = Path(settings.music_root)
    try:
        result = await sync_playlist(db, pid, music_root)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return result
