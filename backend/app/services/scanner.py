import os
import asyncio
import logging
import json
from datetime import datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.media import Media
from app.models.scan_job import ScanJob
from app.services.rule_engine import RuleEngine
from app.services.metadata_service import MetadataService
from app.services.author_matcher import AuthorMatcher
from app.services.organize_service import OrganizeService
from app.services.dlsite_service import DlsiteService
from app.utils.hash import compute_file_hash
from app.utils.file_utils import get_media_type, get_format, is_supported_format
from app.config import get_settings

logger = logging.getLogger(__name__)


class FileInfo:
    def __init__(self, path: str):
        self.path = path
        self.first_seen = datetime.utcnow()
        self.last_size = 0
        self.stable_since: datetime | None = None


class ScannerService:
    """文件扫描服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()
        self.rule_engine = RuleEngine()
        self.metadata_service = MetadataService()
        self.author_matcher = AuthorMatcher(db)
        self.dlsite_service = DlsiteService()
        self.organize_service = OrganizeService(self.settings.library_dir)
        self._pending_files: dict[str, FileInfo] = {}

    async def scan_directory(
        self, path: str, scan_type: str = "full", recursive: bool = True
    ) -> ScanJob:
        """启动扫描任务"""
        job = ScanJob(
            scan_path=path,
            status="running",
            scan_type=scan_type,
            started_at=datetime.utcnow(),
        )
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)

        try:
            files = self._collect_files(path, recursive)
            job.total_files = len(files)
            await self.db.commit()

            new_count = 0
            error_count = 0

            for file_path in files:
                try:
                    if scan_type == "incremental":
                        # Skip if already in DB and not modified
                        existing = await self._find_existing(file_path)
                        if existing:
                            job.processed_files += 1
                            continue

                    media = await self._process_file(file_path)
                    if media:
                        new_count += 1
                    job.processed_files += 1
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
                    error_count += 1
                    job.error_files = error_count

                if job.processed_files % 100 == 0:
                    await self.db.commit()

            job.new_files = new_count
            job.error_files = error_count
            job.status = "completed"
            job.finished_at = datetime.utcnow()
            await self.db.commit()

        except Exception as e:
            logger.error(f"Scan job {job.id} failed: {e}")
            job.status = "failed"
            job.finished_at = datetime.utcnow()
            await self.db.commit()

        return job

    async def create_scan_job(
        self, path: str, scan_type: str = "full", recursive: bool = True
    ) -> ScanJob:
        """创建扫描任务并返回，实际扫描由后台任务执行。"""
        job = ScanJob(
            scan_path=path,
            status="running",
            scan_type=scan_type,
            started_at=datetime.utcnow(),
        )
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def run_scan_job(self, job_id: int, recursive: bool = True) -> None:
        """执行已创建的扫描任务，持续更新数据库进度供 WebSocket 轮询。"""
        result = await self.db.execute(select(ScanJob).where(ScanJob.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            logger.error(f"Scan job {job_id} not found")
            return

        errors = []
        try:
            files = self._collect_files(job.scan_path, recursive)
            job.total_files = len(files)
            await self.db.commit()

            for file_path in files:
                try:
                    if job.scan_type == "incremental":
                        existing = await self._find_existing(file_path)
                        if existing:
                            job.processed_files += 1
                            await self.db.commit()
                            continue

                    media = await self._process_file(file_path, commit=False)
                    if media:
                        job.new_files += 1
                    job.processed_files += 1
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
                    job.error_files += 1
                    errors.append({"path": file_path, "error": str(e)})

                await self.db.commit()

            job.status = "completed"
            job.finished_at = datetime.utcnow()
            if errors:
                job.errors = json.dumps(errors, ensure_ascii=False)
            await self.db.commit()

        except Exception as e:
            logger.error(f"Scan job {job.id} failed: {e}")
            job.status = "failed"
            job.finished_at = datetime.utcnow()
            job.errors = json.dumps([{"error": str(e)}], ensure_ascii=False)
            await self.db.commit()

    def _collect_files(self, path: str, recursive: bool = True) -> list[str]:
        """收集目录中的媒体文件"""
        files = []
        if recursive:
            for root, _, filenames in os.walk(path):
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    if is_supported_format(file_path):
                        files.append(file_path)
        else:
            for item in os.listdir(path):
                file_path = os.path.join(path, item)
                if os.path.isfile(file_path) and is_supported_format(file_path):
                    files.append(file_path)
        return files

    async def _find_existing(self, file_path: str) -> Media | None:
        result = await self.db.execute(
            select(Media).where(Media.file_path == file_path)
        )
        return result.scalar_one_or_none()

    async def _process_file(self, file_path: str, commit: bool = True) -> Media | None:
        """处理单个文件：哈希 → 元数据 → 正则解析 → DLsite 反查 → 作者匹配 → 保存

        优先级：手动作者规则 > DLsite API > 文件名正则解析 > 文件内置元数据
        """
        # Check if already exists
        existing = await self._find_existing(file_path)
        if existing:
            return None

        # Compute hash
        file_hash = compute_file_hash(file_path)
        file_size = os.path.getsize(file_path)
        media_type = get_media_type(file_path)
        if not media_type:
            return None

        # ① 读取文件内置元数据（最低优先级 fallback）
        metadata = await self.metadata_service.read_metadata(file_path)

        # ② 文件名正则解析（向上查找目录名中的 RJ号）
        parsed = await self.rule_engine.parse_with_ancestors(file_path, max_depth=2)

        # ③ DLsite API 反查（如果有 RJ/DL 号）
        dlsite_data = None
        work_id = parsed.get("rj_id") or parsed.get("dl_id")
        if work_id and self.dlsite_service.enabled:
            try:
                dlsite_data = await self.dlsite_service.fetch_by_id(work_id)
            except Exception as e:
                logger.warning(f"DLsite API 查询失败 {work_id}: {e}")

        # 合并元数据，优先级：dlsite > parsed > metadata
        title = (dlsite_data or {}).get("title") or parsed.get("title") or metadata.get("title")
        creator = (dlsite_data or {}).get("creator") or metadata.get("artist")
        circle = (dlsite_data or {}).get("circle")
        cv = parsed.get("cv") or (dlsite_data or {}).get("cv")
        language = parsed.get("language") or (dlsite_data or {}).get("language")
        platform = parsed.get("platform")
        description = (dlsite_data or {}).get("description")
        cover_url = (dlsite_data or {}).get("cover_url")
        metadata_source = "dlsite" if dlsite_data else "parsed"

        media = Media(
            file_path=file_path,
            file_name=os.path.basename(file_path),
            file_hash=file_hash,
            file_size=file_size,
            media_type=media_type,
            format=get_format(file_path),
            duration=metadata.get("duration"),
            bitrate=metadata.get("bitrate"),
            sample_rate=metadata.get("sample_rate"),
            channels=metadata.get("channels"),
            width=metadata.get("width"),
            height=metadata.get("height"),
            title=title,
            rj_id=parsed.get("rj_id"),
            dl_id=parsed.get("dl_id"),
            creator=creator,
            circle=circle,
            cv=cv,
            platform=platform,
            language=language,
            description=description,
            cover_url=cover_url,
            metadata_source=metadata_source,
            status="processed",
            scanned_at=datetime.utcnow(),
        )

        # ④ 作者匹配（手动规则，命中时覆盖所有已有值）
        match_result = await self.author_matcher.match(media)
        if match_result:
            media.creator = match_result["creator"]
            media.circle = match_result["circle"]
            if match_result["cv"]:
                media.cv = match_result["cv"]
            media.metadata_source = "manual"

        self.db.add(media)
        if commit:
            await self.db.commit()
        return media

    async def process_and_organize(self, file_path: str) -> Media:
        """完整处理流程：扫描 → 解析 → 匹配 → 移动到整理目录"""
        media = await self._process_file(file_path)
        if not media:
            existing = await self._find_existing(file_path)
            if existing:
                return existing
            raise ValueError(f"Failed to process file: {file_path}")

        # Move to library
        new_path = self.organize_service.move_to_library(media)
        media.file_path = new_path
        media.file_name = os.path.basename(new_path)
        media.status = "processed"
        await self.db.commit()
        return media
