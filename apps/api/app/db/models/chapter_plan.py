"""Chapter plan model — single-chapter detailed planning."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class ChapterPlan(Base):
    __tablename__ = "chapter_plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("novel_projects.id", ondelete="CASCADE"), nullable=False
    )
    rhythm_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("chapter_rhythm_plans.id", ondelete="CASCADE"), nullable=False
    )

    plan_index: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    is_adopted: Mapped[bool] = mapped_column(Boolean, default=False)

    chapter_goal: Mapped[str] = mapped_column(Text, default="")
    characters: Mapped[str] = mapped_column(Text, default="")
    scenes: Mapped[str] = mapped_column(Text, default="")
    obstacle: Mapped[str] = mapped_column(Text, default="")
    turning_point: Mapped[str] = mapped_column(Text, default="")
    information_gain: Mapped[str] = mapped_column(Text, default="")
    emotion_curve: Mapped[str] = mapped_column(Text, default="")
    payoff: Mapped[str] = mapped_column(Text, default="")
    foreshadow_action: Mapped[str] = mapped_column(Text, default="")
    foreshadow_resolved: Mapped[str] = mapped_column(Text, default="")
    relationship_changes: Mapped[str] = mapped_column(Text, default="")
    end_state: Mapped[str] = mapped_column(Text, default="")
    chapter_hook: Mapped[str] = mapped_column(Text, default="")
    repetition_risk: Mapped[str] = mapped_column(Text, default="")
    logic_issues: Mapped[str] = mapped_column(Text, default="")

    ai_original_json: Mapped[str] = mapped_column(Text, default="")
    human_edits_json: Mapped[str] = mapped_column(Text, default="")
    locked_fields_json: Mapped[str] = mapped_column(Text, default="[]")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
