from sqlalchemy.ext.asyncio import AsyncSession

from downtube.db.repositories import settings as settings_repo

DEFAULTS = {
    "default_format": "mp3",
    "default_quality": "best",
    "default_cover_option": "embed",
    "default_lyrics_option": "lrc",
    "download_concurrency": "2",
}


async def get_settings(db: AsyncSession) -> dict:
    stored = await settings_repo.all_settings(db)
    merged: dict = {}
    for key, default in DEFAULTS.items():
        val = stored.get(key, {})
        merged[key] = val.get("value", default) if isinstance(val, dict) else val
    return merged


async def update_setting(db: AsyncSession, key: str, value: str) -> None:
    await settings_repo.set_setting(db, key, {"value": value})
