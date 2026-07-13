from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from downtube.db.models import Setting


async def get_setting(db: AsyncSession, key: str) -> dict | None:
    row = await db.get(Setting, key)
    return dict(row.value) if row else None


async def set_setting(db: AsyncSession, key: str, value: dict[str, Any]) -> dict[str, Any]:
    row = await db.get(Setting, key)
    if row is None:
        row = Setting(key=key, value=value)
        db.add(row)
    else:
        row.value = value
    await db.commit()
    await db.refresh(row)
    return dict(row.value)


async def all_settings(db: AsyncSession) -> dict[str, dict]:
    result = await db.execute(select(Setting))
    return {row.key: dict(row.value) for row in result.scalars().all()}
