"""Novel synopsis model — versioned full-story synopsis."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class NovelSynopsis(Base):
    __tablename__ = "novel_synopses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("novel_projects.id", ondelete="CASCADE"), nullable=False
    )
    direction_id: Mapped[str] = mapped_column(String(36), default="")

    version: Mapped[int] = mapped_column(Integer, default=1)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    # draft / adopted / superseded

    # Content fields
    one_liner: Mapped[str] = mapped_column(Text, default="")
    core_selling_point: Mapped[str] = mapped_column(Text, default="")
    protagonist_start: Mapped[str] = mapped_column(Text, default="")
    final_goal: Mapped[str] = mapped_column(Text, default="")
    core_conflict: Mapped[str] = mapped_column(Text, default="")
    story_phases: Mapped[str] = mapped_column(Text, default="")
    growth_arc: Mapped[str] = mapped_column(Text, default="")
    main_antagonist: Mapped[str] = mapped_column(Text, default="")
    relationship_changes: Mapped[str] = mapped_column(Text, default="")
    world_truth: Mapped[str] = mapped_column(Text, default="")
    key_foreshadowings: Mapped[str] = mapped_column(Text, default="")
    reader_promise_plan: Mapped[str] = mapped_column(Text, default="")
    ending: Mapped[str] = mapped_column(Text, default="")
    risk_warnings: Mapped[str] = mapped_column(Text, default="")

    # AI original (immutable reference)
    ai_original_json: Mapped[str] = mapped_column(Text, default="")
    # Human edits history
    human_edits_json: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
