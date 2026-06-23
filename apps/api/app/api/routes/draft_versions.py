"""Draft version routes — list, detail, diff, restore, mark final, AI rewrite."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ChapterDraft, DraftVersion
from app.db.session import get_session
from app.schemas.draft_version import (
    DiffRequest,
    DiffResult,
    DraftVersionOut,
    RewriteRequest,
)
from app.services.version_service import (
    ai_rewrite,
    diff_versions,
    mark_final,
    restore_version,
    save_version,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/projects/{project_id}/draft-versions", tags=["draft-versions"])

DB = Annotated[AsyncSession, Depends(get_session)]


def _to_dict(v: DraftVersion) -> dict:
    now = datetime.now(timezone.utc)
    try:
        created = v.created_at
    except Exception:
        created = now
    return {
        "id": v.id,
        "draft_id": v.draft_id,
        "project_id": v.project_id,
        "version_index": v.version_index,
        "version_type": v.version_type,
        "body_text": v.body_text,
        "source": v.source,
        "model": v.model,
        "prompt_version": v.prompt_version,
        "word_count": v.word_count,
        "is_final": v.is_final,
        "parent_version_id": v.parent_version_id,
        "diff_summary": v.diff_summary,
        "llm_call_id": v.llm_call_id,
        "created_at": created or now,
    }


class SaveVersionBody(BaseModel):
    draft_id: str
    body_text: str
    version_type: str = "user_edit"


@router.post("/save", response_model=DraftVersionOut)
async def save(project_id: str, data: SaveVersionBody, session: DB):
    """Save a new version of the draft."""
    draft = await session.get(ChapterDraft, data.draft_id)
    if not draft or draft.project_id != project_id:
        raise HTTPException(status_code=404, detail="Draft not found")

    final_exists = (
        await session.execute(
            select(DraftVersion).where(
                DraftVersion.draft_id == data.draft_id,
                DraftVersion.is_final.is_(True),
            )
        )
    ).scalar_one_or_none()
    if final_exists:
        raise HTTPException(status_code=400, detail="Cannot modify a draft with a final version.")

    version = await save_version(
        session,
        data.draft_id,
        project_id,
        data.body_text,
        data.version_type,
    )
    return _to_dict(version)


@router.get("", response_model=list[DraftVersionOut])
async def list_versions(project_id: str, draft_id: str, session: DB):
    """List all versions of a draft."""
    result = await session.execute(
        select(DraftVersion)
        .where(DraftVersion.draft_id == draft_id, DraftVersion.project_id == project_id)
        .order_by(DraftVersion.version_index.desc())
    )
    return [_to_dict(v) for v in result.scalars().all()]


@router.get("/{version_id}", response_model=DraftVersionOut)
async def get_version(project_id: str, version_id: str, session: DB):
    version = await session.get(DraftVersion, version_id)
    if not version or version.project_id != project_id:
        raise HTTPException(status_code=404, detail="Version not found")
    return _to_dict(version)


@router.post("/diff", response_model=DiffResult)
async def diff(project_id: str, req: DiffRequest, session: DB):
    """Compare two versions."""
    try:
        result = await diff_versions(session, req.version_a_id, req.version_b_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result


@router.post("/{version_id}/restore", response_model=DraftVersionOut)
async def restore(project_id: str, version_id: str, session: DB):
    """Restore a version as current draft body."""
    try:
        version = await restore_version(session, version_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _to_dict(version)


@router.post("/{version_id}/mark-final", response_model=DraftVersionOut)
async def final(project_id: str, version_id: str, session: DB):
    """Mark a version as final."""
    try:
        version = await mark_final(session, version_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _to_dict(version)


@router.post("/rewrite", response_model=DraftVersionOut)
async def rewrite(project_id: str, req: RewriteRequest, session: DB):
    """AI rewrite of selected text."""
    draft = await session.get(ChapterDraft, req.draft_id)
    if not draft or draft.project_id != project_id:
        raise HTTPException(status_code=404, detail="Draft not found")

    try:
        version = await ai_rewrite(
            session,
            req.draft_id,
            project_id,
            req.selected_text,
            req.instruction,
            req.mode,
            req.tone,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _to_dict(version)
