from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from downtube.db.repositories import playlists as pl_repo
from downtube.db.repositories import queue as queue_repo
from downtube.providers.ytmusic import YtmProvider


async def list_playlists(session: AsyncSession):
    return await pl_repo.list_playlists(session)


async def create_playlist(session: AsyncSession, name: str, url: str, format: str = "mp3"):
    return await pl_repo.create_playlist(session, name, url, format)


async def delete_playlist(session: AsyncSession, pid: int):
    return await pl_repo.delete_playlist(session, pid)


async def get_playlist_items(session: AsyncSession, pid: int):
    return await pl_repo.get_playlist_items(session, pid)


def _extract_playlist_id(url: str) -> str:
    patterns = [
        r"[?&]list=([A-Za-z0-9_-]+)",
        r"playlist\?list=([A-Za-z0-9_-]+)",
    ]
    for pat in patterns:
        m = re.search(pat, url)
        if m:
            return m.group(1)
    raise ValueError(f"Gagal ekstrak playlist ID dari URL: {url}")


async def sync_playlist(session: AsyncSession, pid: int, music_root: Path) -> dict:
    p = await pl_repo.get_playlist(session, pid)
    if not p:
        raise ValueError("Playlist tidak ditemukan")

    provider = YtmProvider()
    pl_id = _extract_playlist_id(p.url)
    remote_items = await provider.get_playlist_items(pl_id)

    existing = await pl_repo.get_playlist_items(session, pid)
    existing_ids = {item.video_id for item in existing}
    new_items = [it for it in remote_items if it["video_id"] not in existing_ids]

    queued = []
    for item in new_items:
        url_yt = f"https://www.youtube.com/watch?v={item['video_id']}"
        qid = await queue_repo.add_item(
            session,
            url=url_yt,
            title=item.get("title", ""),
            format=p.format,
            quality="best",
        )
        queued.append({"id": qid, "video_id": item["video_id"], "title": item.get("title", "")})

        item_row = {
            "video_id": item["video_id"],
            "title": item.get("title", ""),
            "artist": item.get("artist", ""),
        }
        await pl_repo.add_playlist_items(session, pid, [item_row])

    await pl_repo.update_playlist_sync(session, pid, datetime.utcnow())

    return {
        "total_remote": len(remote_items),
        "already_synced": len(existing_ids),
        "new_queued": len(queued),
        "items": queued,
    }
