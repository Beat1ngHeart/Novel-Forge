"""Bible schemas — character, world rule, plot thread, foreshadowing."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

SourceStatus = Literal["ai_suggestion", "user_confirmed", "text_fact", "deprecated"]


# === Character ===


class CharacterCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    aliases: str = ""
    age: str = ""
    identity: str = ""
    appearance: str = ""
    personality: str = ""
    desire: str = ""
    fear: str = ""
    current_goal: str = ""
    long_term_goal: str = ""
    abilities: str = ""
    weaknesses: str = ""
    current_location: str = ""
    physical_status: str = ""
    known_information: str = ""
    unknown_information: str = ""
    last_appeared_chapter: str = ""
    source_status: SourceStatus = "user_confirmed"
    notes: str = ""


class CharacterUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    aliases: str | None = None
    age: str | None = None
    identity: str | None = None
    appearance: str | None = None
    personality: str | None = None
    desire: str | None = None
    fear: str | None = None
    current_goal: str | None = None
    long_term_goal: str | None = None
    abilities: str | None = None
    weaknesses: str | None = None
    current_location: str | None = None
    physical_status: str | None = None
    known_information: str | None = None
    unknown_information: str | None = None
    last_appeared_chapter: str | None = None
    source_status: SourceStatus | None = None
    notes: str | None = None


class CharacterOut(BaseModel):
    id: str
    project_id: str
    name: str
    aliases: str
    age: str
    identity: str
    appearance: str
    personality: str
    desire: str
    fear: str
    current_goal: str
    long_term_goal: str
    abilities: str
    weaknesses: str
    current_location: str
    physical_status: str
    known_information: str
    unknown_information: str
    last_appeared_chapter: str
    source_status: str
    notes: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# === World Rule ===


class WorldRuleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=300)
    category: str = ""
    description: str = ""
    scope: str = ""
    exceptions: str = ""
    examples: str = ""
    source_status: SourceStatus = "user_confirmed"
    notes: str = ""


class WorldRuleUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=300)
    category: str | None = None
    description: str | None = None
    scope: str | None = None
    exceptions: str | None = None
    examples: str | None = None
    source_status: SourceStatus | None = None
    notes: str | None = None


class WorldRuleOut(BaseModel):
    id: str
    project_id: str
    name: str
    category: str
    description: str
    scope: str
    exceptions: str
    examples: str
    source_status: str
    notes: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# === Plot Thread ===


class PlotThreadCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    thread_type: str = "main"
    description: str = ""
    characters_involved: str = ""
    start_chapter: str = ""
    current_status: str = "active"
    resolution: str = ""
    resolution_chapter: str = ""
    source_status: SourceStatus = "user_confirmed"
    notes: str = ""


class PlotThreadUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=300)
    thread_type: str | None = None
    description: str | None = None
    characters_involved: str | None = None
    start_chapter: str | None = None
    current_status: str | None = None
    resolution: str | None = None
    resolution_chapter: str | None = None
    source_status: SourceStatus | None = None
    notes: str | None = None


class PlotThreadOut(BaseModel):
    id: str
    project_id: str
    title: str
    thread_type: str
    description: str
    characters_involved: str
    start_chapter: str
    current_status: str
    resolution: str
    resolution_chapter: str
    source_status: str
    notes: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# === Foreshadowing ===


class ForeshadowingCreate(BaseModel):
    content: str = Field(..., min_length=1)
    planted_chapter: str = ""
    evidence: str = ""
    expected_payoff_range: str = ""
    actual_payoff_chapter: str = ""
    status: str = "planted"
    related_characters: str = ""
    related_plot_threads: str = ""
    source_status: SourceStatus = "user_confirmed"
    notes: str = ""


class ForeshadowingUpdate(BaseModel):
    content: str | None = Field(None, min_length=1)
    planted_chapter: str | None = None
    evidence: str | None = None
    expected_payoff_range: str | None = None
    actual_payoff_chapter: str | None = None
    status: str | None = None
    related_characters: str | None = None
    related_plot_threads: str | None = None
    source_status: SourceStatus | None = None
    notes: str | None = None


class ForeshadowingOut(BaseModel):
    id: str
    project_id: str
    content: str
    planted_chapter: str
    evidence: str
    expected_payoff_range: str
    actual_payoff_chapter: str
    status: str
    related_characters: str
    related_plot_threads: str
    source_status: str
    notes: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
