"""Bible candidate routes — generate, list, approve, reject, apply, undo."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import BibleCandidate, NovelProject
from app.db.session import get_session
from app.schemas.bible_candidate import (
    BibleCandidateAction,
    BibleCandidateOut,
    BibleCandidateUpdate,
    GenerateBibleRequest,
)
from app.services.bible_generator import (
    apply_candidates,
    approve_candidate,
    generate_bible_candidates,
    reject_candidate,
    undo_apply,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/projects/{project_id}/bible-candidates", tags=["bible-candidates"])

DB = Annotated[AsyncSession, Depends(get_session)]


def _to_dict(c: BibleCandidate) -> dict:
    now = datetime.now(timezone.utc)
    try:
        created = c.created_at
    except Exception:
        created = now
    try:
        updated = c.updated_at
    except Exception:
        updated = now
    try:
        confirmed = c.confirmed_at
    except Exception:
        confirmed = None
    return {
        "id": c.id,
        "project_id": c.project_id,
        "direction_id": c.direction_id,
        "category": c.category,
        "title": c.title,
        "content_json": c.content_json,
        "source_status": c.source_status,
        "status": c.status,
        "confirmed_at": confirmed,
        "applied_bible_id": c.applied_bible_id,
        "rejection_reason": c.rejection_reason,
        "created_at": created or now,
        "updated_at": updated or now,
    }


@router.post("/generate", response_model=list[BibleCandidateOut])
async def generate(project_id: str, req: GenerateBibleRequest, session: DB):
    """Generate bible candidates from an adopted creative direction."""
    project = await session.get(NovelProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        candidates = await generate_bible_candidates(session, req.direction_id, project_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Bible generation failed")
        raise HTTPException(status_code=500, detail=f"Generation failed: {e}")

    return [_to_dict(c) for c in candidates]


@router.get("", response_model=list[BibleCandidateOut])
async def list_candidates(
    project_id: str,
    session: DB,
    direction_id: str | None = None,
    category: str | None = None,
    status: str | None = None,
):
    """List candidates with optional filters."""
    stmt = select(BibleCandidate).where(BibleCandidate.project_id == project_id)
    if direction_id:
        stmt = stmt.where(BibleCandidate.direction_id == direction_id)
    if category:
        stmt = stmt.where(BibleCandidate.category == category)
    if status:
        stmt = stmt.where(BibleCandidate.status == status)
    stmt = stmt.order_by(BibleCandidate.category, BibleCandidate.created_at)
    result = await session.execute(stmt)
    return [_to_dict(c) for c in result.scalars().all()]


@router.patch("/{candidate_id}", response_model=BibleCandidateOut)
async def update_candidate(project_id: str, candidate_id: str, data: BibleCandidateUpdate, session: DB):
    """Edit a candidate's title or content before approval."""
    candidate = await session.get(BibleCandidate, candidate_id)
    if not candidate or candidate.project_id != project_id:
        raise HTTPException(status_code=404, detail="Candidate not found")
    if candidate.status != "pending":
        raise HTTPException(status_code=400, detail="Can only edit pending candidates")
    if data.title is not None:
        candidate.title = data.title
    if data.content_json is not None:
        # Validate JSON
        try:
            json.loads(data.content_json)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")
        candidate.content_json = data.content_json
    await session.flush()
    return _to_dict(candidate)


@router.post("/{candidate_id}/approve", response_model=BibleCandidateOut)
async def approve(project_id: str, candidate_id: str, session: DB):
    """Approve a candidate (does not yet apply to bible)."""
    try:
        candidate = await approve_candidate(session, candidate_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _to_dict(candidate)


@router.post("/{candidate_id}/reject", response_model=BibleCandidateOut)
async def reject(project_id: str, candidate_id: str, body: BibleCandidateAction, session: DB):
    """Reject a candidate."""
    try:
        candidate = await reject_candidate(session, candidate_id, body.reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _to_dict(candidate)


@router.post("/apply")
async def apply(project_id: str, candidate_ids: list[str], session: DB):
    """Apply approved candidates to the actual bible tables."""
    try:
        results = await apply_candidates(session, project_id, candidate_ids)
    except Exception as e:
        logger.exception("Apply failed")
        raise HTTPException(status_code=500, detail=f"Apply failed (rolled back): {e}")
    return results


@router.post("/{candidate_id}/undo", response_model=BibleCandidateOut)
async def undo(project_id: str, candidate_id: str, session: DB):
    """Undo an applied candidate — delete from bible, reset to pending."""
    try:
        candidate = await undo_apply(session, candidate_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _to_dict(candidate)
