"""Chapter draft model — AI-generated draft and human revision."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class ChapterDraft(Base):
    __tablename__ = "chapter_drafts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("novel_projects.id", ondelete="CASCADE"), nullable=False
    )
    plan_id: Mapped[str] = mapped_column(String(36), ForeignKey("chapter_plans.id", ondelete="CASCADE"), nullable=False)

    draft_type: Mapped[str] = mapped_column(String(20), default="ai_draft")
    # ai_draft / human_revision

    # Generation parameters
    target_words: Mapped[int] = mapped_column(Integer, default=3000)
    person: Mapped[str] = mapped_column(String(20), default="third")
    pov: Mapped[str] = mapped_column(String(30), default="third_limited")
    dialogue_density: Mapped[str] = mapped_column(String(20), default="medium")
    description_density: Mapped[str] = mapped_column(String(20), default="medium")
    pacing: Mapped[str] = mapped_column(String(20), default="medium")
    emotion_intensity: Mapped[str] = mapped_column(String(20), default="medium")
    paragraph_length: Mapped[str] = mapped_column(String(20), default="medium")
    language_strictness: Mapped[str] = mapped_column(String(20), default="normal")
    hook_strength: Mapped[str] = mapped_column(String(20), default="medium")

    # Content
    body_text: Mapped[str] = mapped_column(Text, default="")
    chapter_summary: Mapped[str] = mapped_column(Text, default="")
    actual_word_count: Mapped[int] = mapped_column(Integer, default=0)

    # Candidate data (requires user confirmation)
    new_character_candidates_json: Mapped[str] = mapped_column(Text, default="[]")
    new_setting_candidates_json: Mapped[str] = mapped_column(Text, default="[]")
    state_change_candidates_json: Mapped[str] = mapped_column(Text, default="[]")
    foreshadow_candidates_json: Mapped[str] = mapped_column(Text, default="[]")
    facts_to_confirm_json: Mapped[str] = mapped_column(Text, default="[]")

    # Status
    status: Mapped[str] = mapped_column(String(20), default="ai_draft")

    # Linked LLM call
    llm_call_id: Mapped[str] = mapped_column(String(36), default="")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
