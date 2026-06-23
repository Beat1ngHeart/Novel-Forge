"""Task routes — batch analysis management."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import AnalysisTask, AnalysisTaskItem
from app.db.session import get_session
from app.schemas.task import (
    BatchCreateRequest,
    RetryRequest,
    TaskDetailOut,
    TaskOut,
)
from app.services.batch_service import (
    cancel_task,
    create_batch_task,
    execute_batch_task,
    retry_failed_items,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])

DB = Annotated[AsyncSession, Depends(get_session)]


def _task_to_dict(task: AnalysisTask, include_items: bool = False) -> dict:
    now = datetime.now(timezone.utc)
    try:
        updated = task.updated_at
    except Exception:
        updated = now
    try:
        created = task.created_at
    except Exception:
        created = now

    done = task.completed_items + task.failed_items + task.skipped_items
    progress = (done / task.total_items * 100) if task.total_items > 0 else 0

    result = {
        "id": task.id,
        "document_id": task.document_id,
        "project_id": task.project_id,
        "status": task.status,
        "total_items": task.total_items,
        "completed_items": task.completed_items,
        "failed_items": task.failed_items,
        "skipped_items": task.skipped_items,
        "prompt_version": task.prompt_version,
        "error_message": task.error_message,
        "summary": task.summary,
        "started_at": task.started_at,
        "completed_at": task.completed_at,
        "created_at": created or now,
        "updated_at": updated or now,
        "progress_percent": round(progress, 1),
    }

    if include_items and hasattr(task, "items") and task.items:
        result["items"] = [_item_to_dict(item) for item in task.items]

    return result


def _item_to_dict(item: AnalysisTaskItem) -> dict:
    now = datetime.now(timezone.utc)
    try:
        created = item.created_at
    except Exception:
        created = now
    return {
        "id": item.id,
        "task_id": item.task_id,
        "chapter_id": item.chapter_id,
        "chapter_index": item.chapter_index,
        "chapter_title": item.chapter_title,
        "status": item.status,
        "analysis_id": item.analysis_id,
        "error_message": item.error_message,
        "retry_count": item.retry_count,
        "started_at": item.started_at,
        "completed_at": item.completed_at,
        "created_at": created or now,
    }


@router.post("", response_model=TaskOut, status_code=201)
async def create_task(req: BatchCreateRequest, session: DB):
    """Create a batch analysis task and start execution."""
    try:
        task = await create_batch_task(session, req.chapter_ids, req.prompt_version)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Start background execution
    asyncio.create_task(execute_batch_task(task.id))

    return _task_to_dict(task)


@router.get("", response_model=list[TaskOut])
async def list_tasks(session: DB, document_id: str | None = None, limit: int = 20):
    """List tasks, optionally filtered by document."""
    stmt = select(AnalysisTask).order_by(AnalysisTask.created_at.desc()).limit(limit)
    if document_id:
        stmt = stmt.where(AnalysisTask.document_id == document_id)
    result = await session.execute(stmt)
    return [_task_to_dict(t) for t in result.scalars().all()]


@router.get("/{task_id}", response_model=TaskDetailOut)
async def get_task(task_id: str, session: DB):
    """Get task detail with all items."""
    result = await session.execute(
        select(AnalysisTask).options(selectinload(AnalysisTask.items)).where(AnalysisTask.id == task_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return _task_to_dict(task, include_items=True)


@router.post("/{task_id}/cancel", response_model=TaskOut)
async def cancel(task_id: str, session: DB):
    """Cancel a pending or running task."""
    try:
        success = await cancel_task(task_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not success:
        raise HTTPException(status_code=400, detail="Task cannot be cancelled")

    result = await session.execute(select(AnalysisTask).where(AnalysisTask.id == task_id))
    task = result.scalar_one_or_none()
    return _task_to_dict(task)


@router.post("/{task_id}/retry", response_model=TaskOut)
async def retry(task_id: str, req: RetryRequest, session: DB):
    """Retry failed items in a task."""
    try:
        await retry_failed_items(task_id, req.item_ids)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    result = await session.execute(select(AnalysisTask).where(AnalysisTask.id == task_id))
    task = result.scalar_one_or_none()
    return _task_to_dict(task)
