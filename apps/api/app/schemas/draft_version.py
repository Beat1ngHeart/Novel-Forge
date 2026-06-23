"""Draft version schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class DraftVersionOut(BaseModel):
    id: str
    draft_id: str
    project_id: str
    version_index: int
    version_type: str
    body_text: str
    source: str
    model: str
    prompt_version: str
    word_count: int
    is_final: bool
    parent_version_id: Optional[str]
    diff_summary: str
    llm_call_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class RewriteRequest(BaseModel):
    draft_id: str
    selected_text: str = Field(..., min_length=1)
    instruction: str = Field(..., min_length=1)
    mode: Literal["rewrite", "expand", "compress", "tone"] = "rewrite"
    tone: str = ""


class DiffRequest(BaseModel):
    version_a_id: str
    version_b_id: str


class DiffResult(BaseModel):
    version_a_id: str
    version_b_id: str
    additions: int
    deletions: int
    changes: list[dict]
