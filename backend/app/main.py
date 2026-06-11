import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.core.middleware import ExceptionMiddleware
from app.api import scan, media, rename, tags, author_rules, settings as settings_api, metadata, ws

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Global watcher instance
_watcher = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _watcher
    logger.info("Starting ASMR Media Manager...")
    await init_db()
    logger.info("Database initialized")

    # Start file watcher if enabled
    if settings.watch_enabled:
        from app.services.watcher import DownloadWatcher
        from app.services.scanner import ScannerService
        from app.database import async_session

        async def on_file_ready(path: str):
            async with async_session() as db:
                scanner = ScannerService(db)
                try:
                    if settings.watch_auto_organize:
                        await scanner.process_and_organize(path)
                        logger.info(f"Auto-processed and organized: {path}")
                    else:
                        media = await scanner._process_file(path)
                        if media:
                            await scanner._post_process(media)
                        logger.info(f"Auto-scanned (no organize): {path}")
                except Exception as e:
                    logger.error(f"Auto-process failed for {path}: {e}")

        _watcher = DownloadWatcher(on_file_ready=on_file_ready)
        try:
            await _watcher.start()
            logger.info("File watcher started")
        except Exception as e:
            logger.warning(f"Failed to start file watcher: {e}")

    yield

    # Stop watcher
    if _watcher:
        await _watcher.stop()
    logger.info("Shutting down ASMR Media Manager...")


app = FastAPI(
    title="ASMR Media Manager",
    description="ASMR 媒体整理中心 API",
    version="1.0.0",
    lifespan=lifespan,
)

# Middleware (order matters: last added = first executed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ExceptionMiddleware)

# Mount API routes
app.include_router(scan.router, prefix="/api/v1", tags=["scan"])
app.include_router(media.router, prefix="/api/v1", tags=["media"])
app.include_router(rename.router, prefix="/api/v1", tags=["rename"])
app.include_router(tags.router, prefix="/api/v1", tags=["tags"])
app.include_router(author_rules.router, prefix="/api/v1", tags=["author-rules"])
app.include_router(settings_api.router, prefix="/api/v1", tags=["settings"])
app.include_router(metadata.router, prefix="/api/v1", tags=["metadata"])
app.include_router(ws.router, prefix="/api/v1", tags=["websocket"])


@app.get("/api/v1/health")
async def health_check():
    watcher_status = "disabled"
    if _watcher:
        watcher_status = f"watching ({_watcher.pending_count} pending)"
    return {
        "status": "healthy",
        "version": "1.0.0",
        "watcher": watcher_status,
    }
