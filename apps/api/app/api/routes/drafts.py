"""Draft routes — generate, list, update, rewrite paragraph."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ChapterDraft, NovelProject
from app.db.session import get_session
from app.schemas.draft import (
    DraftOut,
    GenerateDraftRequest,
    RewriteParagraphRequest,
)
from app.services.draft_service import generate_draft, rewrite_paragraph, update_draft_text

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/projects/{project_id}/drafts", tags=["drafts"])

DB = Annotated[AsyncSession, Depends(get_session)]


def _to_dict(d: ChapterDraft) -> dict:
    now = datetime.now(timezone.utc)
    try:
        created = d.created_at
    except Exception:
        created = now
    try:
        updated = d.updated_at
    except Exception:
        updated = now
    return {
        "id": d.id,
        "project_id": d.project_id,
        "plan_id": d.plan_id,
        "draft_type": d.draft_type,
        "target_words": d.target_words,
        "person": d.person,
        "pov": d.pov,
        "dialogue_density": d.dialogue_density,
        "description_density": d.description_density,
        "pacing": d.pacing,
        "emotion_intensity": d.emotion_intensity,
        "paragraph_length": d.paragraph_length,
        "language_strictness": d.language_strictness,
        "hook_strength": d.hook_strength,
        "body_text": d.body_text,
        "chapter_summary": d.chapter_summary,
        "actual_word_count": d.actual_word_count,
        "new_character_candidates_json": d.new_character_candidates_json,
        "new_setting_candidates_json": d.new_setting_candidates_json,
        "state_change_candidates_json": d.state_change_candidates_json,
        "foreshadow_candidates_json": d.foreshadow_candidates_json,
        "facts_to_confirm_json": d.facts_to_confirm_json,
        "status": d.status,
        "llm_call_id": d.llm_call_id,
        "created_at": created or now,
        "updated_at": updated or now,
    }


@router.post("/generate", response_model=DraftOut)
async def generate(project_id: str, req: GenerateDraftRequest, session: DB):
    """Generate a chapter draft from an adopted plan."""
    project = await session.get(NovelProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    try:
        draft = await generate_draft(session, project_id, req.plan_id, req.parameters)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Draft generation failed")
        raise HTTPException(status_code=500, detail=str(e))
    return _to_dict(draft)


@router.get("", response_model=list[DraftOut])
async def list_drafts(project_id: str, session: DB, plan_id: str | None = None):
    stmt = select(ChapterDraft).where(ChapterDraft.project_id == project_id)
    if plan_id:
        stmt = stmt.where(ChapterDraft.plan_id == plan_id)
    stmt = stmt.order_by(ChapterDraft.created_at.desc())
    result = await session.execute(stmt)
    return [_to_dict(d) for d in result.scalars().all()]


@router.get("/{draft_id}", response_model=DraftOut)
async def get_draft(project_id: str, draft_id: str, session: DB):
    draft = await session.get(ChapterDraft, draft_id)
    if not draft or draft.project_id != project_id:
        raise HTTPException(status_code=404, detail="Draft not found")
    return _to_dict(draft)


class UpdateDraftBody(BaseModel):
    body_text: str


@router.patch("/{draft_id}", response_model=DraftOut)
async def update_draft(project_id: str, draft_id: str, data: UpdateDraftBody, session: DB):
    """Update draft body text (human revision)."""
    draft = await session.get(ChapterDraft, draft_id)
    if not draft or draft.project_id != project_id:
        raise HTTPException(status_code=404, detail="Draft not found")
    try:
        draft = await update_draft_text(session, draft_id, data.body_text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _to_dict(draft)


@router.post("/rewrite-paragraph", response_model=DraftOut)
async def rewrite_para(project_id: str, req: RewriteParagraphRequest, session: DB):
    """Rewrite a specific paragraph of the draft."""
    draft = await session.get(ChapterDraft, req.draft_id)
    if not draft or draft.project_id != project_id:
        raise HTTPException(status_code=404, detail="Draft not found")
    try:
        draft = await rewrite_paragraph(session, req.draft_id, req.paragraph_index, req.instruction)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _to_dict(draft)


@router.delete("/{draft_id}", status_code=204)
async def delete_draft(project_id: str, draft_id: str, session: DB):
    draft = await session.get(ChapterDraft, draft_id)
    if not draft or draft.project_id != project_id:
        raise HTTPException(status_code=404, detail="Draft not found")
    await session.delete(draft)
