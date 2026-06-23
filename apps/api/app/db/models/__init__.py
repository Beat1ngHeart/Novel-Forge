import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.analysis import ChapterAnalysis as ChapterAnalysis
from app.db.models.bible import Character as Character
from app.db.models.bible import Foreshadowing as Foreshadowing
from app.db.models.bible import PlotThread as PlotThread
from app.db.models.bible import WorldRule as WorldRule
from app.db.models.bible_candidate import BibleCandidate as BibleCandidate
from app.db.models.chapter_plan import ChapterPlan as ChapterPlan
from app.db.models.creative import CreativeDirection as CreativeDirection
from app.db.models.creative import CreativeSession as CreativeSession
from app.db.models.draft import ChapterDraft as ChapterDraft
from app.db.models.draft_version import DraftVersion as DraftVersion
from app.db.models.rhythm import ChapterRhythmPlan as ChapterRhythmPlan
from app.db.models.state_change import StateChangeCandidate as StateChangeCandidate
from app.db.models.story_gene import StoryGeneRecord as StoryGeneRecord
from app.db.models.synopsis import NovelSynopsis as NovelSynopsis
from app.db.models.task import AnalysisTask as AnalysisTask
from app.db.models.task import AnalysisTaskItem as AnalysisTaskItem
from app.db.models.volume import VolumeOutline as VolumeOutline


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


class NovelProject(Base):
    __tablename__ = "novel_projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    genre: Mapped[str] = mapped_column(String(100), default="")
    subgenre: Mapped[str] = mapped_column(String(100), default="")
    audience_type: Mapped[str] = mapped_column(String(50), default="")
    target_platform: Mapped[str] = mapped_column(String(100), default="")
    target_reader: Mapped[str] = mapped_column(String(200), default="")
    target_word_count: Mapped[int] = mapped_column(Integer, default=0)
    chapter_word_count: Mapped[int] = mapped_column(Integer, default=3000)
    update_frequency: Mapped[str] = mapped_column(String(50), default="")
    language: Mapped[str] = mapped_column(String(20), default="zh-CN")
    status: Mapped[str] = mapped_column(String(50), default="drafting")
    current_volume: Mapped[int] = mapped_column(Integer, default=0)
    current_chapter: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    documents = relationship("SourceDocument", back_populates="project", cascade="all, delete-orphan")


class SourceDocument(Base):
    __tablename__ = "source_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("novel_projects.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(500), default="")
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), default="")
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    sha256: Mapped[str] = mapped_column(String(64), default="")
    source_name: Mapped[str] = mapped_column(String(200), default="")
    author_name: Mapped[str] = mapped_column(String(200), default="")
    rights_status: Mapped[str] = mapped_column(String(100), default="unknown")
    analysis_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    generation_reference_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    storage_path: Mapped[str] = mapped_column(String(1000), default="")
    parse_status: Mapped[str] = mapped_column(String(20), default="pending")
    error_message: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    project = relationship("NovelProject", back_populates="documents")
    chapters = relationship("Chapter", back_populates="document", cascade="all, delete-orphan")


class Chapter(Base):
    __tablename__ = "chapters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("source_documents.id", ondelete="CASCADE"), nullable=False
    )
    chapter_index: Mapped[int] = mapped_column(Integer, nullable=False)
    volume_name: Mapped[str] = mapped_column(String(200), default="")
    title: Mapped[str] = mapped_column(String(500), default="")
    content: Mapped[str] = mapped_column(Text, default="")
    content_hash: Mapped[str] = mapped_column(String(64), default="")
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    parse_source: Mapped[str] = mapped_column(String(20), default="auto")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    document = relationship("SourceDocument", back_populates="chapters")


class LLMCallLog(Base):
    __tablename__ = "llm_call_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(100), default="")
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(50), default="")
    status: Mapped[str] = mapped_column(String(20), default="pending")
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost: Mapped[float] = mapped_column(Float, default=0.0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
