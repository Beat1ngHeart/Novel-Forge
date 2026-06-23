"""Creative direction models — stores user input and generated directions."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class CreativeSession(Base):
    __tablename__ = "creative_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("novel_projects.id", ondelete="CASCADE"), nullable=False
    )

    # User input
    one_line_idea: Mapped[str] = mapped_column(Text, nullable=False)
    genre: Mapped[str] = mapped_column(String(100), default="")
    target_platform: Mapped[str] = mapped_column(String(200), default="")
    target_reader: Mapped[str] = mapped_column(String(200), default="")
    expected_length: Mapped[str] = mapped_column(String(100), default="")
    preferred_pacing: Mapped[str] = mapped_column(String(100), default="")
    forbidden_content: Mapped[str] = mapped_column(Text, default="")
    gene_tags: Mapped[str] = mapped_column(Text, default="")

    status: Mapped[str] = mapped_column(String(20), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class CreativeDirection(Base):
    __tablename__ = "creative_directions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("creative_sessions.id", ondelete="CASCADE"), nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("novel_projects.id", ondelete="CASCADE"), nullable=False
    )

    direction_index: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft")

    # Core content (all user-visible)
    one_line_hook: Mapped[str] = mapped_column(Text, default="")
    core_reader_promise: Mapped[str] = mapped_column(Text, default="")
    protagonist_identity: Mapped[str] = mapped_column(Text, default="")
    protagonist_goal: Mapped[str] = mapped_column(Text, default="")
    core_ability: Mapped[str] = mapped_column(Text, default="")
    ability_cost: Mapped[str] = mapped_column(Text, default="")
    core_conflict: Mapped[str] = mapped_column(Text, default="")
    world_mystery: Mapped[str] = mapped_column(Text, default="")
    growth_cycle: Mapped[str] = mapped_column(Text, default="")
    resource_cycle: Mapped[str] = mapped_column(Text, default="")
    payoff_cycle: Mapped[str] = mapped_column(Text, default="")
    long_term_suspense: Mapped[str] = mapped_column(Text, default="")
    difference_from_tropes: Mapped[str] = mapped_column(Text, default="")
    homogenization_risk: Mapped[str] = mapped_column(Text, default="")
    sustainable_length: Mapped[str] = mapped_column(String(200), default="")
    potential_collapse_point: Mapped[str] = mapped_column(Text, default="")

    # AI original output (immutable reference)
    ai_original_json: Mapped[str] = mapped_column(Text, default="")

    # Human edits
    human_edits_json: Mapped[str] = mapped_column(Text, default="")

    # Meta
    rejection_reason: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
