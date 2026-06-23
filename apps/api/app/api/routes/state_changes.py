"""State change routes — generate, list, accept, reject, undo."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import NovelProject, StateChangeCandidate
from app.db.session import get_session
from app.schemas.state_change import (
    GenerateChangesRequest,
    RejectRequest,
    StateChangeCandidateOut,
)
from app.services.state_change_service import (
    accept_candidate,
    generate_candidates,
    reject_candidate,
    undo_apply,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/projects/{project_id}/state-changes", tags=["state-changes"])

DB = Annotated[AsyncSession, Depends(get_session)]


def _to_dict(c: StateChangeCandidate) -> dict:
    now = datetime.now(timezone.utc)
    try:
        created = c.created_at
    except Exception:
        created = now
    try:
        updated = c.updated_at
    except Exception:
        updated = now
    return {
        "id": c.id,
        "draft_id": c.draft_id,
        "project_id": c.project_id,
        "change_type": c.change_type,
        "entity_name": c.entity_name,
        "before_value": c.before_value,
        "after_value": c.after_value,
        "reason": c.reason,
        "source_chapter": c.source_chapter,
        "source_version_id": c.source_version_id,
        "status": c.status,
        "rejection_reason": c.rejection_reason,
        "applied_bible_id": c.applied_bible_id,
        "applied_bible_table": c.applied_bible_table,
        "created_at": created or now,
        "updated_at": updated or now,
    }


@router.post("/generate", response_model=list[StateChangeCandidateOut])
async def generate(project_id: str, req: GenerateChangesRequest, session: DB):
    """Extract state change candidates from a draft."""
    project = await session.get(NovelProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    try:
        candidates = await generate_candidates(session, project_id, req.draft_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("State change extraction failed")
        raise HTTPException(status_code=500, detail=str(e))
    return [_to_dict(c) for c in candidates]


@router.get("", response_model=list[StateChangeCandidateOut])
async def list_candidates(
    project_id: str,
    session: DB,
    draft_id: str | None = None,
    status: str | None = None,
):
    stmt = select(StateChangeCandidate).where(StateChangeCandidate.project_id == project_id)
    if draft_id:
        stmt = stmt.where(StateChangeCandidate.draft_id == draft_id)
    if status:
        stmt = stmt.where(StateChangeCandidate.status == status)
    stmt = stmt.order_by(StateChangeCandidate.created_at.desc())
    result = await session.execute(stmt)
    return [_to_dict(c) for c in result.scalars().all()]


@router.post("/{candidate_id}/accept", response_model=StateChangeCandidateOut)
async def accept(project_id: str, candidate_id: str, session: DB):
    """Accept a candidate — applies to bible in same transaction."""
    try:
        candidate = await accept_candidate(session, candidate_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _to_dict(candidate)


@router.post("/{candidate_id}/reject", response_model=StateChangeCandidateOut)
async def reject(project_id: str, candidate_id: str, body: RejectRequest, session: DB):
    """Reject a candidate with reason."""
    try:
        candidate = await reject_candidate(session, candidate_id, body.reason)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _to_dict(candidate)


@router.post("/{candidate_id}/undo", response_model=StateChangeCandidateOut)
async def undo(project_id: str, candidate_id: str, session: DB):
    """Undo an applied candidate — delete from bible, reset to pending."""
    try:
        candidate = await undo_apply(session, candidate_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _to_dict(candidate)
