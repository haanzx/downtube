from sqlalchemy.ext.asyncio import AsyncSession

from downtube.db.models import QueueItem
from downtube.db.repositories import queue as queue_repo
from downtube.db.repositories.queue import list_items
from downtube.schemas import DownloadRequest
from downtube.services import settings as settings_service


async def list_queue(db: AsyncSession, limit: int = 100, offset: int = 0) -> list:
    return await list_items(db, limit=limit, offset=offset)


async def enqueue(db: AsyncSession, payload: DownloadRequest) -> QueueItem:
    """Persist a download request as a pending QueueItem (processed by the worker)."""
    defaults = await settings_service.get_settings(db)
    fmt = payload.format or defaults.get("default_format", "mp3")
    quality = payload.quality or defaults.get("default_quality", "best")
    cover = payload.cover_option or defaults.get("default_cover_option", "embed")
    lyrics = payload.lyrics_option or defaults.get("default_lyrics_option", "embed")
    return await queue_repo.add_item(
        db,
        url=payload.url,
        title=payload.title,
        artist=payload.artist,
        album=payload.album,
        format=fmt,
        quality=quality,
        cover_option=cover,
        lyrics_option=lyrics,
    )


async def delete_item(db: AsyncSession, item_id: int) -> bool:
    """Delete a QueueItem and its file from disk."""
    import os
    from sqlalchemy import select
    from downtube.db.models import QueueItem

    result = await db.execute(select(QueueItem).where(QueueItem.id == item_id))
    item = result.scalar_one_or_none()
    if item is None:
        return False
    if item.output_path and os.path.exists(item.output_path):
        os.remove(item.output_path)
    await db.delete(item)
    await db.commit()
    return True


async def retry_item(db: AsyncSession, item_id: int) -> bool:
    """Reset a failed QueueItem back to pending for re-download."""
    from sqlalchemy import select
    from downtube.db.models import QueueItem, QueueStatus

    result = await db.execute(select(QueueItem).where(QueueItem.id == item_id))
    item = result.scalar_one_or_none()
    if item is None:
        return False
    item.status = QueueStatus.PENDING
    item.progress = 0.0
    item.error = None
    item.phase = None
    await db.commit()
    return True
