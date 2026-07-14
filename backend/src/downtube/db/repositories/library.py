"""Library repository: CRUD operations for LibraryItem cache."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from downtube.db.models import LibraryItem


async def get_all_items(db: AsyncSession) -> list[LibraryItem]:
    """Get all cached library items."""
    result = await db.execute(select(LibraryItem).order_by(LibraryItem.file_path))
    return list(result.scalars().all())


async def get_item_by_path(db: AsyncSession, file_path: str) -> LibraryItem | None:
    """Get a library item by file path."""
    result = await db.execute(
        select(LibraryItem).where(LibraryItem.file_path == file_path)
    )
    return result.scalar_one_or_none()


async def upsert_item(
    db: AsyncSession,
    file_path: str,
    file_size: int,
    file_mtime: float,
    title: str | None,
    artist: str | None,
    album: str | None,
    duration: float | None,
    format: str,
) -> LibraryItem:
    """Insert or update a library item."""
    existing = await get_item_by_path(db, file_path)
    if existing:
        existing.file_size = file_size
        existing.file_mtime = file_mtime
        existing.title = title
        existing.artist = artist
        existing.album = album
        existing.duration = duration
        existing.format = format
        from datetime import datetime
        existing.last_scan = datetime.utcnow()
        await db.commit()
        await db.refresh(existing)
        return existing

    from datetime import datetime
    item = LibraryItem(
        file_path=file_path,
        file_size=file_size,
        file_mtime=file_mtime,
        title=title,
        artist=artist,
        album=album,
        duration=duration,
        format=format,
        last_scan=datetime.utcnow(),
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def delete_item(db: AsyncSession, file_path: str) -> bool:
    """Delete a library item by file path."""
    item = await get_item_by_path(db, file_path)
    if item is None:
        return False
    await db.delete(item)
    await db.commit()
    return True


async def delete_items_by_paths(db: AsyncSession, file_paths: set[str]) -> int:
    """Delete library items not in the given set of paths. Returns count deleted."""
    result = await db.execute(select(LibraryItem))
    all_items = list(result.scalars().all())
    deleted = 0
    for item in all_items:
        if item.file_path not in file_paths:
            await db.delete(item)
            deleted += 1
    if deleted > 0:
        await db.commit()
    return deleted
