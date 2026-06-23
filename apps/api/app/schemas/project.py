"""Project schemas for request/response validation."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="项目名称")
    description: str = ""
    genre: str = ""
    subgenre: str = ""
    audience_type: str = ""
    target_platform: str = ""
    target_reader: str = ""
    target_word_count: int = Field(0, ge=0)
    chapter_word_count: int = Field(3000, ge=100, le=50000)
    update_frequency: str = ""
    language: str = "zh-CN"


class ProjectUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    genre: str | None = None
    subgenre: str | None = None
    audience_type: str | None = None
    target_platform: str | None = None
    target_reader: str | None = None
    target_word_count: int | None = Field(None, ge=0)
    chapter_word_count: int | None = Field(None, ge=100, le=50000)
    update_frequency: str | None = None
    language: str | None = None
    status: str | None = None
    current_volume: int | None = Field(None, ge=0)
    current_chapter: int | None = Field(None, ge=0)


class ProjectOut(BaseModel):
    id: str
    name: str
    description: str
    genre: str
    subgenre: str
    audience_type: str
    target_platform: str
    target_reader: str
    target_word_count: int
    chapter_word_count: int
    update_frequency: str
    language: str
    status: str
    current_volume: int
    current_chapter: int
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None = None
    document_count: int = 0
    chapter_count: int = 0

    model_config = {"from_attributes": True}


class ProjectListParams(BaseModel):
    search: str = ""
    genre: str = ""
    status: str = ""
    audience_type: str = ""
    include_archived: bool = False
    sort_by: Literal["created_at", "updated_at", "name"] = "created_at"
    sort_order: Literal["asc", "desc"] = "desc"
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class PaginatedResponse(BaseModel):
    items: list[ProjectOut]
    total: int
    page: int
    page_size: int
    total_pages: int


class ProjectStats(BaseModel):
    total_projects: int
    active_projects: int
    archived_projects: int
    total_documents: int
    total_chapters: int
    by_genre: dict[str, int]
    by_status: dict[str, int]
