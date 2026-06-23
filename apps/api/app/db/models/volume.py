"""Volume outline model — volume-level story structure."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class VolumeOutline(Base):
    __tablename__ = "volume_outlines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("novel_projects.id", ondelete="CASCADE"), nullable=False
    )
    synopsis_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("novel_synopses.id", ondelete="CASCADE"), nullable=False
    )

    volume_index: Mapped[int] = mapped_column(Integer, nullable=False)
    volume_name: Mapped[str] = mapped_column(String(300), default="")
    status: Mapped[str] = mapped_column(String(20), default="draft")
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)

    volume_goal: Mapped[str] = mapped_column(Text, default="")
    core_conflict: Mapped[str] = mapped_column(Text, default="")
    start_state: Mapped[str] = mapped_column(Text, default="")
    end_state: Mapped[str] = mapped_column(Text, default="")
    main_enemy: Mapped[str] = mapped_column(Text, default="")
    character_changes: Mapped[str] = mapped_column(Text, default="")
    new_world_settings: Mapped[str] = mapped_column(Text, default="")
    growth_milestone: Mapped[str] = mapped_column(Text, default="")
    payoff_climax: Mapped[str] = mapped_column(Text, default="")
    volume_twist: Mapped[str] = mapped_column(Text, default="")
    foreshadow_planted: Mapped[str] = mapped_column(Text, default="")
    foreshadow_resolved: Mapped[str] = mapped_column(Text, default="")
    reader_promise_fulfilled: Mapped[str] = mapped_column(Text, default="")
    estimated_chapters: Mapped[int] = mapped_column(Integer, default=50)
    estimated_words: Mapped[int] = mapped_column(Integer, default=150000)

    ai_original_json: Mapped[str] = mapped_column(Text, default="")
    human_edits_json: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
