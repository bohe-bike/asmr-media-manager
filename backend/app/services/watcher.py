import os
import asyncio
import logging
from datetime import datetime
from typing import Callable, Awaitable

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from app.utils.file_utils import is_supported_format
from app.config import get_settings

logger = logging.getLogger(__name__)

# 下载工具常见的临时文件后缀
TEMP_SUFFIXES = {
    ".part",        # Firefox, wget
    ".tmp",         # 通用临时文件
    ".crdownload",  # Chrome
    ".downloading", # 各种下载器
    ".aria2",       # aria2
    ".bt",          # BT 下载
    ".partial",     # Edge
    ".!ut",         # uTorrent
    ".bc!",         # BitComet
}


class FileInfo:
    def __init__(self, path: str):
        self.path = path
        self.first_seen = datetime.utcnow()
        self.last_size: int = -1
        self.stable_since: datetime | None = None


class DownloadWatcher:
    """监控下载目录，检测文件下载完成后触发处理"""

    def __init__(self, on_file_ready: Callable[[str], Awaitable[None]]):
        self.settings = get_settings()
        self.on_file_ready = on_file_ready
        self._pending: dict[str, FileInfo] = {}
        self._observer: Observer | None = None
        self._running = False
        self._check_task: asyncio.Task | None = None

    async def start(self, path: str | None = None):
        watch_path = path or self.settings.download_dir
        if not os.path.isdir(watch_path):
            logger.warning(f"Watch directory does not exist: {watch_path}")
            return

        self._running = True
        handler = _FileHandler(self._on_file_event)
        self._observer = Observer()
        self._observer.schedule(handler, watch_path, recursive=True)
        self._observer.start()
        logger.info(f"Started watching: {watch_path}")

        self._check_task = asyncio.create_task(self._check_loop())

    async def stop(self):
        self._running = False
        if self._observer:
            self._observer.stop()
            self._observer.join()
        if self._check_task:
            self._check_task.cancel()
            try:
                await self._check_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped watching")

    def _on_file_event(self, path: str):
        if not is_supported_format(path):
            return
        if path not in self._pending:
            self._pending[path] = FileInfo(path)
            logger.debug(f"New file detected: {path}")

    async def _check_loop(self):
        interval = self.settings.check_interval
        stable_seconds = self.settings.stable_seconds

        while self._running:
            try:
                await asyncio.sleep(interval)
                await self._check_pending(stable_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in check loop: {e}")

    async def _check_pending(self, stable_seconds: int):
        now = datetime.utcnow()
        ready_files = []

        for path, info in list(self._pending.items()):
            if not os.path.exists(path):
                del self._pending[path]
                continue

            # 检查 1: 是否存在关联的临时文件
            if self._has_temp_file(path):
                info.stable_since = None
                continue

            # 检查 2: 文件是否被其他进程锁定
            if self._is_file_locked(path):
                info.stable_since = None
                continue

            # 检查 3: 文件大小是否稳定
            try:
                current_size = os.path.getsize(path)
            except OSError:
                continue

            if current_size == info.last_size:
                if info.stable_since is None:
                    info.stable_since = now
                elif (now - info.stable_since).total_seconds() >= stable_seconds:
                    ready_files.append(path)
                    del self._pending[path]
            else:
                info.last_size = current_size
                info.stable_since = None

        for path in ready_files:
            logger.info(f"File download complete: {path}")
            try:
                await self.on_file_ready(path)
            except Exception as e:
                logger.error(f"Error processing ready file {path}: {e}")

    def _has_temp_file(self, path: str) -> bool:
        """检查是否存在关联的临时文件"""
        dir_name = os.path.dirname(path)
        base_name = os.path.basename(path)

        # 检查同名但不同后缀的临时文件
        for suffix in TEMP_SUFFIXES:
            temp_path = os.path.join(dir_name, base_name + suffix)
            if os.path.exists(temp_path):
                logger.debug(f"Temp file exists: {temp_path}")
                return True

        # 检查 aria2 控制文件
        aria2_path = path + ".aria2"
        if os.path.exists(aria2_path):
            logger.debug(f"aria2 control file exists: {aria2_path}")
            return True

        return False

    def _is_file_locked(self, path: str) -> bool:
        """检查文件是否被其他进程锁定（写入中）"""
        try:
            # 尝试以独占模式打开文件
            # 如果文件正在被下载工具写入，这会失败
            with open(path, "rb") as f:
                pass
            return False
        except (PermissionError, OSError):
            return True

    @property
    def pending_count(self) -> int:
        return len(self._pending)

    @property
    def pending_files(self) -> list[str]:
        return list(self._pending.keys())


class _FileHandler(FileSystemEventHandler):
    def __init__(self, callback: Callable[[str], None]):
        self.callback = callback

    def on_created(self, event):
        if not event.is_directory:
            self.callback(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self.callback(event.src_path)
