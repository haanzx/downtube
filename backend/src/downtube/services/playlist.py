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


def _is_spotify_url(url: str) -> bool:
    return any(d in url for d in ("open.spotify.com", "spotify.link"))


async def sync_playlist(session: AsyncSession, pid: int, music_root: Path) -> dict:
    p = await pl_repo.get_playlist(session, pid)
    if not p:
        raise ValueError("Playlist tidak ditemukan")

    existing = await pl_repo.get_playlist_items(session, pid)
    existing_ids = {item.video_id for item in existing}
    new_items = []
    playlist_name = p.name

    if _is_spotify_url(p.url):
        # Spotify playlist
        from downtube.providers.spotify_embed import scrape_playlist

        embed_name, tracks = await scrape_playlist(p.url)
        playlist_name = embed_name

        for track in tracks:
            video_id = track.get("song_id", "")
            if not video_id or video_id in existing_ids:
                continue

            # Search YTMusic by duration
            ytm = YtmProvider()
            match = await ytm.search_by_duration(
                track.get("name", ""),
                track.get("artist", ""),
                track.get("duration", 0),
            )
            if match:
                yt_video_id = match["id"]
                url_yt = f"https://www.youtube.com/watch?v={yt_video_id}"
                await queue_repo.add_item(
                    session,
                    url=url_yt,
                    title=track.get("name", ""),
                    artist=track.get("artist", ""),
                    cover_url=track.get("cover_url") or match.get("thumbnail"),
                    format=p.format,
                    quality="best",
                )
                new_items.append({
                    "video_id": yt_video_id,
                    "title": track.get("name", ""),
                    "artist": track.get("artist", ""),
                })
    else:
        # YouTube playlist
        provider = YtmProvider()
        pl_id = _extract_playlist_id(p.url)
        remote_items = await provider.get_playlist_items(pl_id)

        for item in remote_items:
            vid = item["video_id"]
            if vid in existing_ids:
                continue

            url_yt = f"https://www.youtube.com/watch?v={vid}"
            await queue_repo.add_item(
                session,
                url=url_yt,
                title=item.get("title", ""),
                artist=item.get("artist", ""),
                cover_url=item.get("thumbnail"),
                format=p.format,
                quality="best",
            )
            new_items.append({
                "video_id": vid,
                "title": item.get("title", ""),
                "artist": item.get("artist", ""),
            })

    # Add to playlist_items
    if new_items:
        await pl_repo.add_playlist_items(session, pid, new_items)

    await pl_repo.update_playlist_sync(session, pid, datetime.utcnow())

    return {
        "playlist_name": playlist_name,
        "total_remote": len(new_items) + len(existing_ids),
        "already_synced": len(existing_ids),
        "new_queued": len(new_items),
        "items": new_items,
    }
