"""Chapter schemas for request/response validation."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ChapterOut(BaseModel):
    id: str
    document_id: str
    chapter_index: int
    volume_name: str
    title: str
    word_count: int
    parse_source: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChapterDetail(ChapterOut):
    content: str
    content_hash: str


class ChapterUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=500)
    volume_name: str | None = None
    chapter_index: int | None = Field(None, ge=0)
    parse_source: str | None = None


class ChapterMergeRequest(BaseModel):
    chapter_ids: list[str] = Field(..., min_length=2, description="要合并的章节 ID 列表，按顺序")
    new_title: str | None = Field(None, description="合并后的标题，默认用第一个章节的标题")


class ChapterSplitRequest(BaseModel):
    split_position: int = Field(..., ge=1, description="拆分位置（字符索引）")
    new_title: str = Field(..., min_length=1, max_length=500, description="新章节的标题")


class ParsePreviewItem(BaseModel):
    index: int
    title: str
    volume_name: str
    word_count: int
    preview: str


class ParsePreviewResponse(BaseModel):
    encoding_detected: str
    total_chapters: int
    chapters: list[ParsePreviewItem]


class ParseExecuteRequest(BaseModel):
    confirm: bool = True
