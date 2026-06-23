"""Analysis schemas for request/response validation."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AnalysisRequest(BaseModel):
    """Request to analyze a chapter."""

    prompt_version: str = "v1"


class AnalysisOut(BaseModel):
    id: str
    chapter_id: str
    document_id: str
    project_id: str
    schema_version: int
    prompt_version: str
    provider: str
    model: str
    status: str
    confidence: float
    chapter_function: str
    chapter_summary: str
    hook_type: str
    hook_intensity: int
    error_message: str
    llm_call_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AnalysisDetail(AnalysisOut):
    result_json: str
    llm_call_id: str


class AnalysisResultView(BaseModel):
    """Structured view of analysis result for frontend display."""

    schema_version: int = 1
    confidence: float = 0.0
    ambiguities: list[str] = []
    genre: str = ""
    subgenre: str = ""
    chapter_function: str = ""
    pacing: str = ""
    scene_count: int = 0
    point_of_view: str = ""
    conflict: dict[str, Any] = {}
    emotion: dict[str, Any] = {}
    suspense: dict[str, Any] = {}
    state_changes: dict[str, Any] = {}
    foreshadowing: dict[str, Any] = {}
    text_stats: dict[str, Any] = {}
    chapter_summary: str = ""
