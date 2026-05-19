import asyncio
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.scan_job import ScanJob
from app.schemas.scan import ScanRequest, ScanJobResponse
from app.schemas.common import ApiResponse, PaginatedResponse
from app.services.scanner import ScannerService
from app.core.exceptions import NotFoundException, ValidationException

router = APIRouter()


@router.post("/scan")
async def start_scan(request: ScanRequest, db: AsyncSession = Depends(get_db)):
    """启动扫描任务"""
    import os
    if not os.path.isdir(request.path):
        raise ValidationException(f"路径不存在或不是目录: {request.path}")

    scanner = ScannerService(db)
    job = await scanner.scan_directory(request.path, request.scan_type, request.recursive)

    return ApiResponse(data=ScanJobResponse(
        id=job.id,
        scan_path=job.scan_path,
        status=job.status,
        scan_type=job.scan_type,
        total_files=job.total_files,
        processed_files=job.processed_files,
        new_files=job.new_files,
        error_files=job.error_files,
        started_at=job.started_at,
        finished_at=job.finished_at,
        created_at=job.created_at,
        progress_percent=100.0 if job.total_files == 0 else (job.processed_files / job.total_files * 100),
    ))


@router.get("/scan/jobs")
async def list_scan_jobs(
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """获取扫描任务列表"""
    query = select(ScanJob).order_by(ScanJob.created_at.desc())
    if status:
        query = query.where(ScanJob.status == status)

    # Count
    count_result = await db.execute(select(ScanJob))
    total = len(count_result.scalars().all())

    # Paginate
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    jobs = result.scalars().all()

    items = [
        ScanJobResponse(
            id=j.id,
            scan_path=j.scan_path,
            status=j.status,
            scan_type=j.scan_type,
            total_files=j.total_files,
            processed_files=j.processed_files,
            new_files=j.new_files,
            error_files=j.error_files,
            started_at=j.started_at,
            finished_at=j.finished_at,
            created_at=j.created_at,
            progress_percent=100.0 if j.total_files == 0 else (j.processed_files / j.total_files * 100),
        )
        for j in jobs
    ]

    return ApiResponse(data=PaginatedResponse(items=items, total=total, page=page, page_size=page_size))


@router.get("/scan/{job_id}")
async def get_scan_job(job_id: int, db: AsyncSession = Depends(get_db)):
    """获取扫描任务状态"""
    result = await db.execute(select(ScanJob).where(ScanJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise NotFoundException(f"扫描任务 {job_id} 不存在")

    return ApiResponse(data=ScanJobResponse(
        id=job.id,
        scan_path=job.scan_path,
        status=job.status,
        scan_type=job.scan_type,
        total_files=job.total_files,
        processed_files=job.processed_files,
        new_files=job.new_files,
        error_files=job.error_files,
        started_at=job.started_at,
        finished_at=job.finished_at,
        created_at=job.created_at,
        progress_percent=100.0 if job.total_files == 0 else (job.processed_files / job.total_files * 100),
    ))
