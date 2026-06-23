"""Chapter rhythm plan schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ChapterRhythmContent(BaseModel):
    """Content of a single chapter rhythm plan."""

    temp_title: str = ""
    chapter_function: str = ""
    core_event: str = ""
    protagonist_goal: str = ""
    main_obstacle: str = ""
    conflict_type: str = ""
    information_gain: str = ""
    character_change: str = ""
    payoff_or_emotion: str = ""
    foreshadow_action: str = ""
    chapter_hook: str = ""
    volume_goal_connection: str = ""
    estimated_words: int = 3000
    risk_notes: str = ""


class ChapterRhythmOut(BaseModel):
    id: str
    project_id: str
    volume_id: str
    chapter_index: int
    status: str
    is_current: bool
    temp_title: str
    chapter_function: str
    core_event: str
    protagonist_goal: str
    main_obstacle: str
    conflict_type: str
    information_gain: str
    character_change: str
    payoff_or_emotion: str
    foreshadow_action: str
    chapter_hook: str
    volume_goal_connection: str
    estimated_words: int
    risk_notes: str
    ai_original_json: str
    human_edits_json: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChapterRhythmUpdate(BaseModel):
    temp_title: Optional[str] = None
    chapter_function: Optional[str] = None
    core_event: Optional[str] = None
    protagonist_goal: Optional[str] = None
    main_obstacle: Optional[str] = None
    conflict_type: Optional[str] = None
    information_gain: Optional[str] = None
    character_change: Optional[str] = None
    payoff_or_emotion: Optional[str] = None
    foreshadow_action: Optional[str] = None
    chapter_hook: Optional[str] = None
    volume_goal_connection: Optional[str] = None
    estimated_words: Optional[int] = Field(None, ge=100)
    risk_notes: Optional[str] = None


class GenerateRhythmRequest(BaseModel):
    volume_id: str
    chapter_count: int = Field(10, ge=1, le=100)


class ReorderRequest(BaseModel):
    chapter_ids: list[str] = Field(..., min_length=1)


class InsertRequest(BaseModel):
    after_index: int = Field(..., ge=0)
    temp_title: str = "新章节"
    chapter_function: str = ""
