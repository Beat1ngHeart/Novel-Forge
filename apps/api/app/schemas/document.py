"""Document schemas for request/response validation."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

RIGHTS_STATUSES = ("owned", "authorized", "public_domain", "analysis_only", "unknown", "prohibited")


class DocumentCreate(BaseModel):
    """Metadata submitted alongside file upload (via form fields)."""

    project_id: str | None = None
    title: str = ""
    source_name: str = ""
    author_name: str = ""
    rights_status: Literal["owned", "authorized", "public_domain", "analysis_only", "unknown", "prohibited"] = "unknown"


class DocumentOut(BaseModel):
    id: str
    project_id: str | None
    title: str
    original_filename: str
    file_type: str
    mime_type: str
    file_size: int
    sha256: str
    source_name: str
    author_name: str
    rights_status: str
    analysis_allowed: bool
    generation_reference_allowed: bool
    storage_path: str
    parse_status: str
    error_message: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentDuplicate(BaseModel):
    """Response when a duplicate file is detected."""

    is_duplicate: bool = True
    existing_document_id: str
    sha256: str
    message: str = "文件已存在，跳过重复上传"
