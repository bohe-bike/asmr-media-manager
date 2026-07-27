import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.database import _ensure_sqlite_columns, _ensure_sqlite_database_directory


def test_ensure_sqlite_database_directory_creates_missing_parent(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    database_path = _ensure_sqlite_database_directory(
        "sqlite+aiosqlite:///runtime/data/asmr_manager.db"
    )

    assert database_path == tmp_path / "runtime" / "data" / "asmr_manager.db"
    assert database_path.parent.is_dir()


def test_ensure_sqlite_database_directory_ignores_memory_database():
    assert _ensure_sqlite_database_directory("sqlite+aiosqlite:///:memory:") is None


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
