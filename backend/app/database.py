from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    connect_args={"check_same_thread": False},
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _ensure_sqlite_columns(conn)


async def _ensure_sqlite_columns(conn) -> None:
    """为早期 SQLite 数据库补齐新增列，兼容 Docker 自动升级。"""
    if conn.dialect.name != "sqlite":
        return

    required_columns = {
        "media": {
            "cover_url": "TEXT",
            "description": "TEXT",
            "metadata_source": "VARCHAR(20)",
            "rename_original_path": "TEXT",
            "rename_original_status": "VARCHAR(20)",
        },
        "scan_jobs": {"organized_files": "INTEGER DEFAULT 0"},
    }

    for table, columns in required_columns.items():
        result = await conn.execute(text(f"PRAGMA table_info({table})"))
        existing_columns = {row[1] for row in result}
        for column, definition in columns.items():
            if column not in existing_columns:
                await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {definition}"))
