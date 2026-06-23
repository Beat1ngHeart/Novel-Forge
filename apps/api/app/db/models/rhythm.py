"""Chapter rhythm plan model — chapter-level beat sheet."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class ChapterRhythmPlan(Base):
    __tablename__ = "chapter_rhythm_plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("novel_projects.id", ondelete="CASCADE"), nullable=False
    )
    volume_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("volume_outlines.id", ondelete="CASCADE"), nullable=False
    )

    chapter_index: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)

    temp_title: Mapped[str] = mapped_column(String(300), default="")
    chapter_function: Mapped[str] = mapped_column(String(100), default="")
    core_event: Mapped[str] = mapped_column(Text, default="")
    protagonist_goal: Mapped[str] = mapped_column(Text, default="")
    main_obstacle: Mapped[str] = mapped_column(Text, default="")
    conflict_type: Mapped[str] = mapped_column(String(100), default="")
    information_gain: Mapped[str] = mapped_column(Text, default="")
    character_change: Mapped[str] = mapped_column(Text, default="")
    payoff_or_emotion: Mapped[str] = mapped_column(Text, default="")
    foreshadow_action: Mapped[str] = mapped_column(Text, default="")
    chapter_hook: Mapped[str] = mapped_column(Text, default="")
    volume_goal_connection: Mapped[str] = mapped_column(Text, default="")
    estimated_words: Mapped[int] = mapped_column(Integer, default=3000)
    risk_notes: Mapped[str] = mapped_column(Text, default="")

    ai_original_json: Mapped[str] = mapped_column(Text, default="")
    human_edits_json: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
