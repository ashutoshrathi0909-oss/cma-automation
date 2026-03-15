"""Task status polling endpoints.

Clients poll GET /api/tasks/{task_id} to track background ARQ job progress.
"""

from __future__ import annotations

import logging

from arq import create_pool
from arq.jobs import Job, JobStatus
from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.models.schemas import TaskStatusResponse, UserProfile
from app.workers.worker import _get_redis_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

# Map ARQ JobStatus enum values → string labels expected by the API contract
_STATUS_MAP: dict[JobStatus, str] = {
    JobStatus.queued: "queued",
    JobStatus.in_progress: "in_progress",
    JobStatus.complete: "complete",
    JobStatus.not_found: "not_found",
    JobStatus.deferred: "queued",  # treat deferred same as queued for clients
}


@router.get("/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    current_user: UserProfile = Depends(get_current_user),
) -> TaskStatusResponse:
    """Poll the status of an ARQ background task.

    Returns a TaskStatusResponse with:
      - status: "queued" | "in_progress" | "complete" | "not_found"
      - progress: 0-100 (None until complete)
    """
    redis_settings = _get_redis_settings()
    redis_pool = await create_pool(redis_settings)
    try:
        job = Job(task_id, redis_pool)
        arq_status: JobStatus = await job.status()
    finally:
        await redis_pool.aclose()

    status_str = _STATUS_MAP.get(arq_status, "not_found")

    # Derive progress from status
    progress: int | None = None
    if status_str == "queued":
        progress = 0
    elif status_str == "in_progress":
        progress = 50
    elif status_str == "complete":
        progress = 100

    logger.debug("Task %s status: %s", task_id, status_str)

    return TaskStatusResponse(
        task_id=task_id,
        status=status_str,
        progress=progress,
    )
