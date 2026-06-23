"""Batch analysis service — manages multi-chapter analysis tasks."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import app.db.session as db_session_module
from app.db.models import AnalysisTask, AnalysisTaskItem, Chapter, SourceDocument
from app.services.analysis_service import analyze_chapter

logger = logging.getLogger(__name__)

# Global set to track chapters currently being analyzed (prevents concurrent duplicate)
_running_chapters: set[str] = set()
_running_lock = asyncio.Lock()


def _now():
    return datetime.now(timezone.utc)


async def create_batch_task(
    session: AsyncSession,
    chapter_ids: list[str],
    prompt_version: str = "v1",
) -> AnalysisTask:
    """Create a batch analysis task with items for each chapter."""
    # Load chapters to get metadata
    chapters = []
    for cid in chapter_ids:
        ch = await session.get(Chapter, cid)
        if not ch:
            raise ValueError(f"Chapter not found: {cid}")
        chapters.append(ch)

    if not chapters:
        raise ValueError("No chapters provided")

    # Get document and project from first chapter
    doc = await session.get(SourceDocument, chapters[0].document_id)
    if not doc:
        raise ValueError("Document not found")

    # Check rights
    if doc.rights_status == "prohibited":
        raise PermissionError("该资料权利状态为「禁止使用」，不允许分析")

    # Filter out chapters that already have a running/pending task item
    async with _running_lock:
        active_chapters = set()
        existing_items = (
            (
                await session.execute(
                    select(AnalysisTaskItem.chapter_id).where(
                        AnalysisTaskItem.chapter_id.in_(chapter_ids),
                        AnalysisTaskItem.status.in_(["pending", "running"]),
                    )
                )
            )
            .scalars()
            .all()
        )
        active_chapters = set(existing_items)

    task = AnalysisTask(
        document_id=doc.id,
        project_id=doc.project_id,
        status="pending",
        total_items=len(chapters),
        prompt_version=prompt_version,
    )
    session.add(task)
    await session.flush()

    items = []
    for ch in chapters:
        skipped = ch.id in active_chapters
        item = AnalysisTaskItem(
            task_id=task.id,
            chapter_id=ch.id,
            chapter_index=ch.chapter_index,
            chapter_title=ch.title,
            status="skipped" if skipped else "pending",
        )
        if skipped:
            task.skipped_items += 1
        session.add(item)
        items.append(item)

    await session.flush()
    return task


async def execute_batch_task(task_id: str) -> None:
    """Execute a batch task in the background. Runs each chapter item sequentially.

    Each item is executed in its own session to isolate failures.
    """
    await asyncio.sleep(0.1)  # Yield to let the API respond first

    async with db_session_module.async_session_factory() as session:
        task = await session.get(AnalysisTask, task_id)
        if not task or task.status not in ("pending", "running"):
            return

        task.status = "running"
        task.started_at = _now()
        await session.commit()

    # Load prompt_version
    prompt_version = "v1"
    async with db_session_module.async_session_factory() as session:
        task_for_pv = await session.get(AnalysisTask, task_id)
        if task_for_pv:
            prompt_version = task_for_pv.prompt_version

    # Load items
    async with db_session_module.async_session_factory() as session:
        result = await session.execute(
            select(AnalysisTaskItem)
            .where(AnalysisTaskItem.task_id == task_id, AnalysisTaskItem.status == "pending")
            .order_by(AnalysisTaskItem.chapter_index)
        )
        pending_items = list(result.scalars().all())

        # If no pending items, check if we are already done
        if not pending_items:
            task = await session.get(AnalysisTask, task_id)
            if task:
                done = task.completed_items + task.failed_items + task.skipped_items
                if done >= task.total_items:
                    task.status = "succeeded" if task.failed_items == 0 else "failed"
                    task.completed_at = _now()
                    task.summary = (
                        f"完成: {task.completed_items}, 失败: {task.failed_items}, "
                        f"跳过: {task.skipped_items}, 总计: {task.total_items}"
                    )
                    await session.commit()
            return

    for item_data in pending_items:
        # Check if task was cancelled
        async with db_session_module.async_session_factory() as session:
            task = await session.get(AnalysisTask, task_id)
            if not task or task.status == "cancelled":
                return

        item_id = item_data.id
        chapter_id = item_data.chapter_id

        # Concurrency guard
        async with _running_lock:
            if chapter_id in _running_chapters:
                async with db_session_module.async_session_factory() as session:
                    item = await session.get(AnalysisTaskItem, item_id)
                    if item:
                        item.status = "skipped"
                        item.error_message = "Chapter is being analyzed by another task"
                    task = await session.get(AnalysisTask, task_id)
                    if task:
                        task.skipped_items += 1
                    await session.commit()
                continue
            _running_chapters.add(chapter_id)

        try:
            # Mark item as running
            async with db_session_module.async_session_factory() as session:
                item = await session.get(AnalysisTaskItem, item_id)
                if item:
                    item.status = "running"
                    item.started_at = _now()
                await session.commit()

            # Execute single chapter analysis
            async with db_session_module.async_session_factory() as session:
                analysis = await analyze_chapter(session, chapter_id, prompt_version)
                analysis_id = analysis.id
                is_success = analysis.status == "completed"
                error_msg = analysis.error_message if not is_success else ""
                await session.commit()

            # Update item
            async with db_session_module.async_session_factory() as session:
                item = await session.get(AnalysisTaskItem, item_id)
                if item:
                    item.status = "succeeded" if is_success else "failed"
                    item.analysis_id = analysis_id if is_success else ""
                    item.error_message = error_msg
                    item.completed_at = _now()

                task = await session.get(AnalysisTask, task_id)
                if task:
                    if is_success:
                        task.completed_items += 1
                    else:
                        task.failed_items += 1

                    # Check if all done
                    done = task.completed_items + task.failed_items + task.skipped_items
                    if done >= task.total_items:
                        task.status = "succeeded" if task.failed_items == 0 else "failed"
                        task.completed_at = _now()
                        task.summary = (
                            f"完成: {task.completed_items}, 失败: {task.failed_items}, "
                            f"跳过: {task.skipped_items}, 总计: {task.total_items}"
                        )
                await session.commit()

        except Exception as e:
            logger.exception("Batch item failed: %s", e)
            async with db_session_module.async_session_factory() as session:
                item = await session.get(AnalysisTaskItem, item_id)
                if item:
                    item.status = "failed"
                    item.error_message = str(e)[:2000]
                    item.completed_at = _now()
                task = await session.get(AnalysisTask, task_id)
                if task:
                    task.failed_items += 1
                    done = task.completed_items + task.failed_items + task.skipped_items
                    if done >= task.total_items:
                        task.status = "failed"
                        task.completed_at = _now()
                        task.summary = (
                            f"完成: {task.completed_items}, 失败: {task.failed_items}, "
                            f"跳过: {task.skipped_items}, 总计: {task.total_items}"
                        )
                await session.commit()
        finally:
            async with _running_lock:
                _running_chapters.discard(chapter_id)


async def retry_failed_items(task_id: str, item_ids: list[str]) -> int:
    """Reset failed items to pending and re-execute them."""
    async with db_session_module.async_session_factory() as session:
        task = await session.get(AnalysisTask, task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        if task.status not in ("failed", "succeeded"):
            raise ValueError(f"Cannot retry items in task status: {task.status}")

        count = 0
        for item_id in item_ids:
            item = await session.get(AnalysisTaskItem, item_id)
            if item and item.task_id == task_id and item.status == "failed":
                item.status = "pending"
                item.error_message = ""
                item.retry_count += 1
                item.started_at = None
                item.completed_at = None
                task.failed_items -= 1
                count += 1

        if count == 0:
            await session.commit()
            raise ValueError("No failed items found to retry")

        task.status = "running"
        task.completed_at = None
        await session.commit()

    # Re-execute pending items
    asyncio.create_task(execute_batch_task(task_id))

    return count


async def cancel_task(task_id: str) -> bool:
    """Cancel a pending or running task."""
    async with db_session_module.async_session_factory() as session:
        task = await session.get(AnalysisTask, task_id)
        if not task:
            return False
        if task.status in ("succeeded", "failed", "cancelled"):
            return False

        task.status = "cancelled"
        task.completed_at = _now()

        # Cancel pending items
        result = await session.execute(
            select(AnalysisTaskItem).where(
                AnalysisTaskItem.task_id == task_id,
                AnalysisTaskItem.status == "pending",
            )
        )
        for item in result.scalars().all():
            item.status = "cancelled"

        task.summary = (
            f"已取消。完成: {task.completed_items}, 失败: {task.failed_items}, "
            f"取消: {task.total_items - task.completed_items - task.failed_items - task.skipped_items}"
        )
        await session.commit()
        return True


async def get_task_with_items(session: AsyncSession, task_id: str) -> AnalysisTask | None:
    """Get task with items loaded."""
    result = await session.execute(select(AnalysisTask).where(AnalysisTask.id == task_id))
    task = result.scalar_one_or_none()
    if task:
        # Force load items
        _ = task.items
    return task
