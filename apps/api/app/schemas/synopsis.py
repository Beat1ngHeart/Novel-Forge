"""Synopsis schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SynopsisContent(BaseModel):
    """Structured synopsis content."""

    one_liner: str = ""
    core_selling_point: str = ""
    protagonist_start: str = ""
    final_goal: str = ""
    core_conflict: str = ""
    story_phases: str = ""
    growth_arc: str = ""
    main_antagonist: str = ""
    relationship_changes: str = ""
    world_truth: str = ""
    key_foreshadowings: str = ""
    reader_promise_plan: str = ""
    ending: str = ""
    risk_warnings: str = ""


class SynopsisOut(BaseModel):
    id: str
    project_id: str
    direction_id: str
    version: int
    is_current: bool
    status: str
    one_liner: str
    core_selling_point: str
    protagonist_start: str
    final_goal: str
    core_conflict: str
    story_phases: str
    growth_arc: str
    main_antagonist: str
    relationship_changes: str
    world_truth: str
    key_foreshadowings: str
    reader_promise_plan: str
    ending: str
    risk_warnings: str
    ai_original_json: str
    human_edits_json: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SynopsisUpdate(BaseModel):
    """Edit specific fields of a synopsis."""

    one_liner: Optional[str] = None
    core_selling_point: Optional[str] = None
    protagonist_start: Optional[str] = None
    final_goal: Optional[str] = None
    core_conflict: Optional[str] = None
    story_phases: Optional[str] = None
    growth_arc: Optional[str] = None
    main_antagonist: Optional[str] = None
    relationship_changes: Optional[str] = None
    world_truth: Optional[str] = None
    key_foreshadowings: Optional[str] = None
    reader_promise_plan: Optional[str] = None
    ending: Optional[str] = None
    risk_warnings: Optional[str] = None


class GenerateSynopsisRequest(BaseModel):
    direction_id: str
