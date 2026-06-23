"""State change candidate schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

VALID_CHANGE_TYPES = [
    "character_location",
    "character_relationship",
    "character_goal",
    "power_change",
    "resource_change",
    "health_change",
    "new_skill",
    "new_world_rule",
    "new_character",
    "new_foreshadow",
    "foreshadow_resolved",
    "plot_thread_progress",
    "timeline_event",
    "knowledge_change",
]


class StateChangeCandidateOut(BaseModel):
    id: str
    draft_id: str
    project_id: str
    change_type: str
    entity_name: str
    before_value: str
    after_value: str
    reason: str
    source_chapter: str
    source_version_id: str
    status: str
    rejection_reason: str
    applied_bible_id: str
    applied_bible_table: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RejectRequest(BaseModel):
    reason: str = ""


class GenerateChangesRequest(BaseModel):
    draft_id: str


class UndoApplyRequest(BaseModel):
    candidate_id: str
