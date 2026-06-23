"""Bible candidate model — stores AI-generated bible items awaiting user confirmation."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class BibleCandidate(Base):
    __tablename__ = "bible_candidates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("novel_projects.id", ondelete="CASCADE"), nullable=False
    )
    direction_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("creative_directions.id", ondelete="CASCADE"), nullable=False
    )

    category: Mapped[str] = mapped_column(String(50), nullable=False)
    # world_rule, character, plot_thread, foreshadowing, secret, limitation, reader_promise
    title: Mapped[str] = mapped_column(String(300), default="")
    content_json: Mapped[str] = mapped_column(Text, nullable=False)
    source_status: Mapped[str] = mapped_column(String(20), default="ai_suggestion")
    status: Mapped[str] = mapped_column(String(20), default="pending")
    # pending / approved / rejected / applied

    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    applied_bible_id: Mapped[str] = mapped_column(String(36), default="")
    rejection_reason: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
