from typing import Any

from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession

from downtube.db.session import get_db
from downtube.services import settings as settings_service

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("")
async def get_settings(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    return await settings_service.get_settings(db)


@router.put("")
async def update_settings(
    payload: dict[str, Any], db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    for key, value in (payload.get("settings", payload) or {}).items():
        await settings_service.update_setting(db, key, str(value))
    return await settings_service.get_settings(db)
