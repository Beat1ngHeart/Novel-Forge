"""Volume outline schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class VolumeContent(BaseModel):
    """Content of a single volume."""

    volume_name: str = ""
    volume_goal: str = ""
    core_conflict: str = ""
    start_state: str = ""
    end_state: str = ""
    main_enemy: str = ""
    character_changes: str = ""
    new_world_settings: str = ""
    growth_milestone: str = ""
    payoff_climax: str = ""
    volume_twist: str = ""
    foreshadow_planted: str = ""
    foreshadow_resolved: str = ""
    reader_promise_fulfilled: str = ""
    estimated_chapters: int = 50
    estimated_words: int = 150000


class VolumeOut(BaseModel):
    id: str
    project_id: str
    synopsis_id: str
    volume_index: int
    volume_name: str
    status: str
    is_current: bool
    volume_goal: str
    core_conflict: str
    start_state: str
    end_state: str
    main_enemy: str
    character_changes: str
    new_world_settings: str
    growth_milestone: str
    payoff_climax: str
    volume_twist: str
    foreshadow_planted: str
    foreshadow_resolved: str
    reader_promise_fulfilled: str
    estimated_chapters: int
    estimated_words: int
    ai_original_json: str
    human_edits_json: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class VolumeUpdate(BaseModel):
    volume_name: Optional[str] = None
    volume_goal: Optional[str] = None
    core_conflict: Optional[str] = None
    start_state: Optional[str] = None
    end_state: Optional[str] = None
    main_enemy: Optional[str] = None
    character_changes: Optional[str] = None
    new_world_settings: Optional[str] = None
    growth_milestone: Optional[str] = None
    payoff_climax: Optional[str] = None
    volume_twist: Optional[str] = None
    foreshadow_planted: Optional[str] = None
    foreshadow_resolved: Optional[str] = None
    reader_promise_fulfilled: Optional[str] = None
    estimated_chapters: Optional[int] = Field(None, ge=1)
    estimated_words: Optional[int] = Field(None, ge=1000)


class VolumeReorder(BaseModel):
    """Reorder volumes."""

    volume_ids: list[str] = Field(..., min_length=1, description="Volumes in desired order")


class GenerateVolumesRequest(BaseModel):
    synopsis_id: str


class RegenerateVolumeRequest(BaseModel):
    volume_id: str
