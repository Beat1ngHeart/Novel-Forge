"""StoryGene database model — stores validated narrative analysis results."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class StoryGeneRecord(Base):
    __tablename__ = "story_genes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    chapter_id: Mapped[str] = mapped_column(String(36), ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False)
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("source_documents.id", ondelete="CASCADE"), nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("novel_projects.id", ondelete="CASCADE"), nullable=False
    )

    # Schema version for migration
    schema_version: Mapped[int] = mapped_column(Integer, default=1)

    # Stored as validated JSON (the full StoryGene)
    gene_json: Mapped[str] = mapped_column(Text, nullable=False)

    # Summary fields for querying without parsing JSON
    genre: Mapped[str] = mapped_column(String(50), default="")
    chapter_function: Mapped[str] = mapped_column(String(50), default="")
    pacing: Mapped[str] = mapped_column(String(20), default="")
    conflict_type: Mapped[str] = mapped_column(String(50), default="")
    hook_type: Mapped[str] = mapped_column(String(50), default="")
    hook_intensity: Mapped[int] = mapped_column(Integer, default=0)
    payoff_intensity: Mapped[int] = mapped_column(Integer, default=0)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    chapter_summary: Mapped[str] = mapped_column(Text, default="")

    # LLM call reference
    llm_call_id: Mapped[str] = mapped_column(String(36), default="")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
