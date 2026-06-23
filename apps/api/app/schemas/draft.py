"""Chapter draft schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class DraftParameters(BaseModel):
    """Generation parameters for a chapter draft."""

    target_words: int = Field(3000, ge=500, le=50000)
    person: str = "third"
    pov: str = "third_limited"
    dialogue_density: str = "medium"
    description_density: str = "medium"
    pacing: str = "medium"
    emotion_intensity: str = "medium"
    paragraph_length: str = "medium"
    language_strictness: str = "normal"
    hook_strength: str = "medium"


class GenerateDraftRequest(BaseModel):
    plan_id: str
    parameters: DraftParameters = Field(default_factory=DraftParameters)


class RewriteParagraphRequest(BaseModel):
    draft_id: str
    paragraph_index: int = Field(..., ge=0)
    instruction: str = Field(..., min_length=1)


class DraftOut(BaseModel):
    id: str
    project_id: str
    plan_id: str
    draft_type: str
    target_words: int
    person: str
    pov: str
    dialogue_density: str
    description_density: str
    pacing: str
    emotion_intensity: str
    paragraph_length: str
    language_strictness: str
    hook_strength: str
    body_text: str
    chapter_summary: str
    actual_word_count: int
    new_character_candidates_json: str
    new_setting_candidates_json: str
    state_change_candidates_json: str
    foreshadow_candidates_json: str
    facts_to_confirm_json: str
    status: str
    llm_call_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
