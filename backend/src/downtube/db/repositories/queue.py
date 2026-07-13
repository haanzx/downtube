from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from downtube.db.models import QueueItem, QueueStatus


async def list_items(db: AsyncSession, limit: int = 100, offset: int = 0) -> list[QueueItem]:
    result = await db.execute(
        select(QueueItem).order_by(QueueItem.created_at.desc()).limit(limit).offset(offset)
    )
    return list(result.scalars().all())


async def list_pending(db: AsyncSession, limit: int = 100) -> list[QueueItem]:
    result = await db.execute(
        select(QueueItem)
        .where(QueueItem.status == QueueStatus.PENDING)
        .order_by(QueueItem.created_at.asc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_item(db: AsyncSession, item_id: int) -> QueueItem | None:
    return await db.get(QueueItem, item_id)


async def add_item(db: AsyncSession, url: str, **fields) -> QueueItem:
    item = QueueItem(url=url, **fields)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def update_status(
    db: AsyncSession,
    item_id: int,
    status: QueueStatus,
    progress: float | None = None,
    error: str | None = None,
    output_path: str | None = None,
) -> QueueItem | None:
    item = await db.get(QueueItem, item_id)
    if item is None:
        return None
    item.status = status
    if progress is not None:
        item.progress = progress
    if error is not None:
        item.error = error
    if output_path is not None:
        item.output_path = output_path
    await db.commit()
    await db.refresh(item)
    return item
