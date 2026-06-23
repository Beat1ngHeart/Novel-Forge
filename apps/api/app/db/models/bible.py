"""Novel Bible models — characters, world rules, plot threads, foreshadowings."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Character(Base):
    __tablename__ = "bible_characters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("novel_projects.id", ondelete="CASCADE"), nullable=False
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    aliases: Mapped[str] = mapped_column(Text, default="")
    age: Mapped[str] = mapped_column(String(100), default="")
    identity: Mapped[str] = mapped_column(String(300), default="")
    appearance: Mapped[str] = mapped_column(Text, default="")
    personality: Mapped[str] = mapped_column(Text, default="")
    desire: Mapped[str] = mapped_column(Text, default="")
    fear: Mapped[str] = mapped_column(Text, default="")
    current_goal: Mapped[str] = mapped_column(Text, default="")
    long_term_goal: Mapped[str] = mapped_column(Text, default="")
    abilities: Mapped[str] = mapped_column(Text, default="")
    weaknesses: Mapped[str] = mapped_column(Text, default="")
    current_location: Mapped[str] = mapped_column(String(300), default="")
    physical_status: Mapped[str] = mapped_column(String(300), default="")
    known_information: Mapped[str] = mapped_column(Text, default="")
    unknown_information: Mapped[str] = mapped_column(Text, default="")
    last_appeared_chapter: Mapped[str] = mapped_column(String(200), default="")

    source_status: Mapped[str] = mapped_column(String(20), default="user_confirmed")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class WorldRule(Base):
    __tablename__ = "bible_world_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("novel_projects.id", ondelete="CASCADE"), nullable=False
    )

    name: Mapped[str] = mapped_column(String(300), nullable=False)
    category: Mapped[str] = mapped_column(String(100), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    scope: Mapped[str] = mapped_column(String(200), default="")
    exceptions: Mapped[str] = mapped_column(Text, default="")
    examples: Mapped[str] = mapped_column(Text, default="")

    source_status: Mapped[str] = mapped_column(String(20), default="user_confirmed")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class PlotThread(Base):
    __tablename__ = "bible_plot_threads"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("novel_projects.id", ondelete="CASCADE"), nullable=False
    )

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    thread_type: Mapped[str] = mapped_column(String(50), default="main")
    description: Mapped[str] = mapped_column(Text, default="")
    characters_involved: Mapped[str] = mapped_column(Text, default="")
    start_chapter: Mapped[str] = mapped_column(String(200), default="")
    current_status: Mapped[str] = mapped_column(String(100), default="active")
    resolution: Mapped[str] = mapped_column(Text, default="")
    resolution_chapter: Mapped[str] = mapped_column(String(200), default="")

    source_status: Mapped[str] = mapped_column(String(20), default="user_confirmed")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Foreshadowing(Base):
    __tablename__ = "bible_foreshadowings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("novel_projects.id", ondelete="CASCADE"), nullable=False
    )

    content: Mapped[str] = mapped_column(Text, nullable=False)
    planted_chapter: Mapped[str] = mapped_column(String(200), default="")
    evidence: Mapped[str] = mapped_column(Text, default="")
    expected_payoff_range: Mapped[str] = mapped_column(String(200), default="")
    actual_payoff_chapter: Mapped[str] = mapped_column(String(200), default="")
    status: Mapped[str] = mapped_column(String(30), default="planted")
    related_characters: Mapped[str] = mapped_column(Text, default="")
    related_plot_threads: Mapped[str] = mapped_column(Text, default="")

    source_status: Mapped[str] = mapped_column(String(20), default="user_confirmed")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
