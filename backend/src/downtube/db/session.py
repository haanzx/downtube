from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import event

from downtube.config import settings

engine = create_async_engine(settings.database_url, future=True, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable WAL mode for SQLite to support concurrent reads/writes on low-power devices."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()


async def init_db() -> None:
    """Create tables if they do not exist."""
    from pathlib import Path

    from downtube.db.models import Base
    from downtube.config import settings

    settings.ensure_dirs()
    db_path = settings.database_url
    for prefix in ("sqlite+aiosqlite:///", "sqlite:///"):
        if db_path.startswith(prefix):
            Path(db_path[len(prefix) :]).parent.mkdir(parents=True, exist_ok=True)
            break

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
