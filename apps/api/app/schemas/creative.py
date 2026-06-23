"""Creative direction schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CreativeInput(BaseModel):
    """User input for creative direction generation."""

    one_line_idea: str = Field(..., min_length=5, max_length=500, description="一句话创意")
    genre: str = ""
    target_platform: str = ""
    target_reader: str = ""
    expected_length: str = ""
    preferred_pacing: str = ""
    forbidden_content: str = ""
    gene_tags: str = ""


class DirectionContent(BaseModel):
    """The structured content of a single creative direction."""

    one_line_hook: str = ""
    core_reader_promise: str = ""
    protagonist_identity: str = ""
    protagonist_goal: str = ""
    core_ability: str = ""
    ability_cost: str = ""
    core_conflict: str = ""
    world_mystery: str = ""
    growth_cycle: str = ""
    resource_cycle: str = ""
    payoff_cycle: str = ""
    long_term_suspense: str = ""
    difference_from_tropes: str = ""
    homogenization_risk: str = ""
    sustainable_length: str = ""
    potential_collapse_point: str = ""


class SessionOut(BaseModel):
    id: str
    project_id: str
    one_line_idea: str
    genre: str
    target_platform: str
    target_reader: str
    expected_length: str
    preferred_pacing: str
    forbidden_content: str
    gene_tags: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DirectionOut(BaseModel):
    id: str
    session_id: str
    project_id: str
    direction_index: int
    status: str
    one_line_hook: str
    core_reader_promise: str
    protagonist_identity: str
    protagonist_goal: str
    core_ability: str
    ability_cost: str
    core_conflict: str
    world_mystery: str
    growth_cycle: str
    resource_cycle: str
    payoff_cycle: str
    long_term_suspense: str
    difference_from_tropes: str
    homogenization_risk: str
    sustainable_length: str
    potential_collapse_point: str
    rejection_reason: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DirectionEdit(BaseModel):
    """Edit specific fields of a direction."""

    one_line_hook: Optional[str] = None
    core_reader_promise: Optional[str] = None
    protagonist_identity: Optional[str] = None
    protagonist_goal: Optional[str] = None
    core_ability: Optional[str] = None
    ability_cost: Optional[str] = None
    core_conflict: Optional[str] = None
    world_mystery: Optional[str] = None
    growth_cycle: Optional[str] = None
    resource_cycle: Optional[str] = None
    payoff_cycle: Optional[str] = None
    long_term_suspense: Optional[str] = None
    difference_from_tropes: Optional[str] = None
    homogenization_risk: Optional[str] = None
    sustainable_length: Optional[str] = None
    potential_collapse_point: Optional[str] = None


class MergeRequest(BaseModel):
    """Merge fields from multiple directions."""

    source_ids: list[str] = Field(..., min_length=2, max_length=3, description="要合并的方向 ID")
    field_sources: dict[str, str] = Field(
        ...,
        description="字段名 → 来源方向 ID 的映射，决定每个字段取自哪个方向",
    )
