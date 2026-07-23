import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.database import _ensure_sqlite_columns


def test_ensure_sqlite_columns_upgrades_legacy_schema():
    async def run_test():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        try:
            async with engine.begin() as conn:
                await conn.execute(text("CREATE TABLE media (id INTEGER PRIMARY KEY)"))
                await conn.execute(text("CREATE TABLE scan_jobs (id INTEGER PRIMARY KEY)"))

                await _ensure_sqlite_columns(conn)

                media_columns = {
                    row[1]
                    for row in await conn.execute(text("PRAGMA table_info(media)"))
                }
                scan_columns = {
                    row[1]
                    for row in await conn.execute(text("PRAGMA table_info(scan_jobs)"))
                }
                assert {"rename_original_path", "rename_original_status"} <= media_columns
                assert "organized_files" in scan_columns
        finally:
            await engine.dispose()

    asyncio.run(run_test())
