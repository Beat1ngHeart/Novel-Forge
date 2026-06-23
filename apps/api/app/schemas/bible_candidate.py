"""Bible candidate schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class BibleCandidateOut(BaseModel):
    id: str
    project_id: str
    direction_id: str
    category: str
    title: str
    content_json: str
    source_status: str
    status: str
    confirmed_at: Optional[datetime] = None
    applied_bible_id: str
    rejection_reason: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BibleCandidateUpdate(BaseModel):
    title: Optional[str] = None
    content_json: Optional[str] = None


class BibleCandidateAction(BaseModel):
    reason: str = ""


class GenerateBibleRequest(BaseModel):
    direction_id: str = Field(..., description="已采用的创意方向 ID")


class GeneratedBiblePreview(BaseModel):
    """Preview of what AI generated before saving as candidates."""

    world_rules: list[dict[str, Any]] = []
    characters: list[dict[str, Any]] = []
    plot_threads: list[dict[str, Any]] = []
    foreshadowings: list[dict[str, Any]] = []
    secrets: list[dict[str, Any]] = []
    limitations: list[dict[str, Any]] = []
    reader_promises: list[dict[str, Any]] = []
