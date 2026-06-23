"""Synopsis routes — generate, list, edit, adopt, restore, compare."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import NovelProject, NovelSynopsis
from app.db.session import get_session
from app.schemas.synopsis import (
    GenerateSynopsisRequest,
    SynopsisOut,
    SynopsisUpdate,
)
from app.services.synopsis_service import (
    adopt_synopsis,
    edit_synopsis,
    generate_synopsis,
    restore_synopsis,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/projects/{project_id}/synopses", tags=["synopses"])

DB = Annotated[AsyncSession, Depends(get_session)]


def _to_dict(s: NovelSynopsis) -> dict:
    now = datetime.now(timezone.utc)
    try:
        created = s.created_at
    except Exception:
        created = now
    try:
        updated = s.updated_at
    except Exception:
        updated = now
    return {
        "id": s.id,
        "project_id": s.project_id,
        "direction_id": s.direction_id,
        "version": s.version,
        "is_current": s.is_current,
        "status": s.status,
        "one_liner": s.one_liner,
        "core_selling_point": s.core_selling_point,
        "protagonist_start": s.protagonist_start,
        "final_goal": s.final_goal,
        "core_conflict": s.core_conflict,
        "story_phases": s.story_phases,
        "growth_arc": s.growth_arc,
        "main_antagonist": s.main_antagonist,
        "relationship_changes": s.relationship_changes,
        "world_truth": s.world_truth,
        "key_foreshadowings": s.key_foreshadowings,
        "reader_promise_plan": s.reader_promise_plan,
        "ending": s.ending,
        "risk_warnings": s.risk_warnings,
        "ai_original_json": s.ai_original_json,
        "human_edits_json": s.human_edits_json,
        "created_at": created or now,
        "updated_at": updated or now,
    }


@router.post("/generate", response_model=SynopsisOut)
async def generate(project_id: str, req: GenerateSynopsisRequest, session: DB):
    """Generate a new synopsis draft from an adopted creative direction."""
    project = await session.get(NovelProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    try:
        synopsis = await generate_synopsis(session, project_id, req.direction_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Synopsis generation failed")
        raise HTTPException(status_code=500, detail=f"生成失败: {e}")
    return _to_dict(synopsis)


@router.get("", response_model=list[SynopsisOut])
async def list_synopses(project_id: str, session: DB):
    """List all synopsis versions for a project."""
    result = await session.execute(
        select(NovelSynopsis).where(NovelSynopsis.project_id == project_id).order_by(NovelSynopsis.version.desc())
    )
    return [_to_dict(s) for s in result.scalars().all()]


@router.get("/current", response_model=SynopsisOut | None)
async def get_current(project_id: str, session: DB):
    """Get the current adopted synopsis."""
    result = await session.execute(
        select(NovelSynopsis).where(
            NovelSynopsis.project_id == project_id,
            NovelSynopsis.is_current.is_(True),
        )
    )
    synopsis = result.scalar_one_or_none()
    if not synopsis:
        return None
    return _to_dict(synopsis)


@router.get("/{synopsis_id}", response_model=SynopsisOut)
async def get_synopsis(project_id: str, synopsis_id: str, session: DB):
    """Get a specific synopsis version."""
    synopsis = await session.get(NovelSynopsis, synopsis_id)
    if not synopsis or synopsis.project_id != project_id:
        raise HTTPException(status_code=404, detail="Synopsis not found")
    return _to_dict(synopsis)


@router.patch("/{synopsis_id}", response_model=SynopsisOut)
async def update_synopsis(project_id: str, synopsis_id: str, data: SynopsisUpdate, session: DB):
    """Edit a synopsis. AI original is preserved; human edits recorded."""
    try:
        synopsis = await edit_synopsis(session, synopsis_id, data.model_dump(exclude_unset=True))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _to_dict(synopsis)


@router.post("/{synopsis_id}/adopt", response_model=SynopsisOut)
async def adopt(project_id: str, synopsis_id: str, session: DB):
    """Adopt a synopsis as current. Supersedes previous adopted version."""
    try:
        synopsis = await adopt_synopsis(session, synopsis_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _to_dict(synopsis)


@router.post("/{synopsis_id}/restore", response_model=SynopsisOut)
async def restore(project_id: str, synopsis_id: str, session: DB):
    """Restore a superseded version as current."""
    try:
        synopsis = await restore_synopsis(session, synopsis_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _to_dict(synopsis)


@router.get("/{synopsis_id}/diff")
async def diff(project_id: str, synopsis_id: str, compare_with: str, session: DB):
    """Compare two synopsis versions. Returns changed fields."""
    s1 = await session.get(NovelSynopsis, synopsis_id)
    s2 = await session.get(NovelSynopsis, compare_with)
    if not s1 or s1.project_id != project_id:
        raise HTTPException(status_code=404, detail="Synopsis not found")
    if not s2 or s2.project_id != project_id:
        raise HTTPException(status_code=404, detail="Compare target not found")

    fields = [
        "one_liner",
        "core_selling_point",
        "protagonist_start",
        "final_goal",
        "core_conflict",
        "story_phases",
        "growth_arc",
        "main_antagonist",
        "relationship_changes",
        "world_truth",
        "key_foreshadowings",
        "reader_promise_plan",
        "ending",
        "risk_warnings",
    ]
    changes = []
    for f in fields:
        v1 = getattr(s1, f, "")
        v2 = getattr(s2, f, "")
        if v1 != v2:
            changes.append({"field": f, "version_a": s1.version, "value_a": v1, "version_b": s2.version, "value_b": v2})

    return {
        "synopsis_a": {"id": s1.id, "version": s1.version, "status": s1.status},
        "synopsis_b": {"id": s2.id, "version": s2.version, "status": s2.status},
        "changed_fields": changes,
        "total_changes": len(changes),
    }
