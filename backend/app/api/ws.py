import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.database import async_session
from app.models.scan_job import ScanJob

logger = logging.getLogger(__name__)

router = APIRouter()

# Active WebSocket connections per scan job
_connections: dict[int, set[WebSocket]] = {}


async def broadcast_scan_progress(job_id: int, data: dict):
    """向指定扫描任务的所有 WebSocket 连接广播进度"""
    connections = _connections.get(job_id, set())
    dead = set()
    for ws in connections:
        try:
            await ws.send_json(data)
        except Exception:
            dead.add(ws)
    connections -= dead


@router.websocket("/ws/scan/{job_id}")
async def scan_progress_ws(websocket: WebSocket, job_id: int):
    """扫描进度实时推送"""
    await websocket.accept()

    if job_id not in _connections:
        _connections[job_id] = set()
    _connections[job_id].add(websocket)

    try:
        # Poll job status and push updates
        last_processed = -1
        while True:
            async with async_session() as db:
                result = await db.execute(select(ScanJob).where(ScanJob.id == job_id))
                job = result.scalar_one_or_none()

                if not job:
                    await websocket.send_json({"type": "error", "data": {"message": "Job not found"}})
                    break

                if job.processed_files != last_processed:
                    progress = {
                        "type": "progress",
                        "data": {
                            "processed_files": job.processed_files,
                            "total_files": job.total_files,
                            "new_files": job.new_files,
                            "error_files": job.error_files,
                            "organized_files": job.organized_files,
                            "progress_percent": 100.0 if job.total_files == 0 else (job.processed_files / job.total_files * 100),
                        },
                    }
                    await websocket.send_json(progress)
                    last_processed = job.processed_files

                if job.status in ("completed", "failed"):
                    await websocket.send_json({
                        "type": "completed",
                        "data": {
                            "status": job.status,
                            "total_files": job.total_files,
                            "new_files": job.new_files,
                            "error_files": job.error_files,
                            "organized_files": job.organized_files,
                        },
                    })
                    break

            await asyncio.sleep(1)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error for job {job_id}: {e}")
    finally:
        _connections.get(job_id, set()).discard(websocket)
