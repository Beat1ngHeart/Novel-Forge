"""Chapter plan schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ChapterPlanContent(BaseModel):
    """Content of a single chapter plan variant."""

    chapter_goal: str = ""
    characters: str = ""
    scenes: str = ""
    obstacle: str = ""
    turning_point: str = ""
    information_gain: str = ""
    emotion_curve: str = ""
    payoff: str = ""
    foreshadow_action: str = ""
    foreshadow_resolved: str = ""
    relationship_changes: str = ""
    end_state: str = ""
    chapter_hook: str = ""
    repetition_risk: str = ""
    logic_issues: str = ""


class ChapterPlanOut(BaseModel):
    id: str
    project_id: str
    rhythm_id: str
    plan_index: int
    status: str
    is_adopted: bool
    chapter_goal: str
    characters: str
    scenes: str
    obstacle: str
    turning_point: str
    information_gain: str
    emotion_curve: str
    payoff: str
    foreshadow_action: str
    foreshadow_resolved: str
    relationship_changes: str
    end_state: str
    chapter_hook: str
    repetition_risk: str
    logic_issues: str
    ai_original_json: str
    human_edits_json: str
    locked_fields_json: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChapterPlanUpdate(BaseModel):
    chapter_goal: Optional[str] = None
    characters: Optional[str] = None
    scenes: Optional[str] = None
    obstacle: Optional[str] = None
    turning_point: Optional[str] = None
    information_gain: Optional[str] = None
    emotion_curve: Optional[str] = None
    payoff: Optional[str] = None
    foreshadow_action: Optional[str] = None
    foreshadow_resolved: Optional[str] = None
    relationship_changes: Optional[str] = None
    end_state: Optional[str] = None
    chapter_hook: Optional[str] = None
    repetition_risk: Optional[str] = None
    logic_issues: Optional[str] = None


class GeneratePlansRequest(BaseModel):
    rhythm_id: str


class MergeRequest(BaseModel):
    source_ids: list[str] = Field(..., min_length=2, max_length=3)
    field_sources: dict[str, str]
