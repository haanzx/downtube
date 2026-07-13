from __future__ import annotations

from datetime import datetime
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from downtube.db.models import Playlist, PlaylistItem


async def create_playlist(
    session: AsyncSession, name: str, url: str, format: str = "mp3"
) -> Playlist:
    p = Playlist(name=name, url=url, format=format)
    session.add(p)
    await session.commit()
    await session.refresh(p)
    return p


async def list_playlists(session: AsyncSession) -> Sequence[Playlist]:
    r = await session.execute(select(Playlist).order_by(Playlist.id.desc()))
    return list(r.scalars().all())


async def get_playlist(session: AsyncSession, pid: int) -> Playlist | None:
    return await session.get(Playlist, pid)


async def delete_playlist(session: AsyncSession, pid: int) -> bool:
    p = await session.get(Playlist, pid)
    if not p:
        return False
    await session.delete(p)
    await session.commit()
    return True


async def get_playlist_items(
    session: AsyncSession, pid: int
) -> Sequence[PlaylistItem]:
    r = await session.execute(
        select(PlaylistItem)
        .where(PlaylistItem.playlist_id == pid)
        .order_by(PlaylistItem.id)
    )
    return list(r.scalars().all())


async def add_playlist_items(
    session: AsyncSession, pid: int, items: list[dict]
) -> int:
    count = 0
    for item in items:
        obj = PlaylistItem(playlist_id=pid, **item)
        session.add(obj)
        count += 1
    await session.commit()
    return count


async def update_playlist_sync(
    session: AsyncSession, pid: int, ts: datetime | None = None
) -> None:
    p = await session.get(Playlist, pid)
    if p:
        p.last_sync = ts or datetime.utcnow()
        await session.commit()
