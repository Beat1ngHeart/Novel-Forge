"""Task schemas for batch analysis."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BatchCreateRequest(BaseModel):
    """Request to create a batch analysis task."""

    chapter_ids: list[str] = Field(..., min_length=1, description="要分析的章节 ID 列表")
    prompt_version: str = "v1"


class TaskItemOut(BaseModel):
    id: str
    task_id: str
    chapter_id: str
    chapter_index: int
    chapter_title: str
    status: str
    analysis_id: str
    error_message: str
    retry_count: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TaskOut(BaseModel):
    id: str
    document_id: str
    project_id: str
    status: str
    total_items: int
    completed_items: int
    failed_items: int
    skipped_items: int
    prompt_version: str
    error_message: str
    summary: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    progress_percent: float = 0.0

    model_config = {"from_attributes": True}


class TaskDetailOut(TaskOut):
    items: list[TaskItemOut] = []


class RetryRequest(BaseModel):
    """Request to retry failed items."""

    item_ids: list[str] = Field(..., min_length=1)
