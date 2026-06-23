"""Creative direction routes — generate, list, edit, accept/reject, merge."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CreativeDirection, CreativeSession, NovelProject
from app.db.session import get_session
from app.schemas.creative import (
    CreativeInput,
    DirectionEdit,
    DirectionOut,
    MergeRequest,
    SessionOut,
)
from app.services.creative_service import (
    accept_direction,
    edit_direction,
    generate_directions,
    reject_direction,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/projects/{project_id}/creative", tags=["creative"])

DB = Annotated[AsyncSession, Depends(get_session)]


def _session_to_dict(cs: CreativeSession) -> dict:
    now = datetime.now(timezone.utc)
    try:
        created = cs.created_at
    except Exception:
        created = now
    try:
        updated = cs.updated_at
    except Exception:
        updated = now
    return {
        "id": cs.id,
        "project_id": cs.project_id,
        "one_line_idea": cs.one_line_idea,
        "genre": cs.genre,
        "target_platform": cs.target_platform,
        "target_reader": cs.target_reader,
        "expected_length": cs.expected_length,
        "preferred_pacing": cs.preferred_pacing,
        "forbidden_content": cs.forbidden_content,
        "gene_tags": cs.gene_tags,
        "status": cs.status,
        "created_at": created or now,
        "updated_at": updated or now,
    }


def _dir_to_dict(d: CreativeDirection) -> dict:
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
        "session_id": d.session_id,
        "project_id": d.project_id,
        "direction_index": d.direction_index,
        "status": d.status,
        "one_line_hook": d.one_line_hook,
        "core_reader_promise": d.core_reader_promise,
        "protagonist_identity": d.protagonist_identity,
        "protagonist_goal": d.protagonist_goal,
        "core_ability": d.core_ability,
        "ability_cost": d.ability_cost,
        "core_conflict": d.core_conflict,
        "world_mystery": d.world_mystery,
        "growth_cycle": d.growth_cycle,
        "resource_cycle": d.resource_cycle,
        "payoff_cycle": d.payoff_cycle,
        "long_term_suspense": d.long_term_suspense,
        "difference_from_tropes": d.difference_from_tropes,
        "homogenization_risk": d.homogenization_risk,
        "sustainable_length": d.sustainable_length,
        "potential_collapse_point": d.potential_collapse_point,
        "rejection_reason": d.rejection_reason,
        "created_at": created or now,
        "updated_at": updated or now,
    }


@router.post("/generate", response_model=list[DirectionOut])
async def generate(project_id: str, data: CreativeInput, session: DB):
    """Generate 3 creative directions from user input."""
    project = await session.get(NovelProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        _cs, directions = await generate_directions(session, data, project_id)
    except Exception as e:
        logger.exception("Generation failed")
        raise HTTPException(status_code=500, detail=f"生成失败: {e}")

    return [_dir_to_dict(d) for d in directions]


@router.get("/sessions", response_model=list[SessionOut])
async def list_sessions(project_id: str, session: DB):
    """List creative sessions for a project."""
    result = await session.execute(
        select(CreativeSession)
        .where(CreativeSession.project_id == project_id)
        .order_by(CreativeSession.created_at.desc())
    )
    return [_session_to_dict(s) for s in result.scalars().all()]


@router.get("/sessions/{session_id}/directions", response_model=list[DirectionOut])
async def list_session_directions(project_id: str, session_id: str, session: DB):
    """List all directions in a session."""
    result = await session.execute(
        select(CreativeDirection)
        .where(CreativeDirection.session_id == session_id, CreativeDirection.project_id == project_id)
        .order_by(CreativeDirection.direction_index)
    )
    return [_dir_to_dict(d) for d in result.scalars().all()]


@router.patch("/directions/{direction_id}", response_model=DirectionOut)
async def update_direction(project_id: str, direction_id: str, data: DirectionEdit, session: DB):
    """Edit a direction. AI original is preserved; human edits are recorded."""
    try:
        direction = await edit_direction(session, direction_id, data.model_dump(exclude_unset=True))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _dir_to_dict(direction)


@router.post("/directions/{direction_id}/accept", response_model=DirectionOut)
async def accept(project_id: str, direction_id: str, session: DB):
    """Accept a direction. Siblings are automatically rejected."""
    try:
        direction = await accept_direction(session, direction_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _dir_to_dict(direction)


@router.post("/directions/{direction_id}/reject", response_model=DirectionOut)
async def reject(
    project_id: str,
    direction_id: str,
    session: DB,
    reason: str = "",
):
    """Reject a direction."""
    try:
        direction = await reject_direction(session, direction_id, reason)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _dir_to_dict(direction)


@router.post("/merge", response_model=DirectionOut)
async def merge_directions(project_id: str, req: MergeRequest, session: DB):
    """Merge fields from multiple directions into a new one."""
    # Load source directions
    sources: dict[str, CreativeDirection] = {}
    for sid in req.source_ids:
        d = await session.get(CreativeDirection, sid)
        if not d or d.project_id != project_id:
            raise HTTPException(status_code=404, detail=f"Direction not found: {sid}")
        sources[sid] = d

    if len(sources) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 valid source directions")

    # Build merged content
    merged: dict[str, str] = {}
    direction_fields = [
        "one_line_hook",
        "core_reader_promise",
        "protagonist_identity",
        "protagonist_goal",
        "core_ability",
        "ability_cost",
        "core_conflict",
        "world_mystery",
        "growth_cycle",
        "resource_cycle",
        "payoff_cycle",
        "long_term_suspense",
        "difference_from_tropes",
        "homogenization_risk",
        "sustainable_length",
        "potential_collapse_point",
    ]
    for field in direction_fields:
        source_id = req.field_sources.get(field, req.source_ids[0])
        source = sources.get(source_id)
        if source:
            merged[field] = getattr(source, field, "")

    # Create new direction as merge result
    new_dir = CreativeDirection(
        session_id=sources[req.source_ids[0]].session_id,
        project_id=project_id,
        direction_index=99,  # Merge result
        status="draft",
        **merged,
        ai_original_json=json.dumps(merged, ensure_ascii=False),
    )
    session.add(new_dir)
    await session.flush()
    await session.refresh(new_dir)
    return _dir_to_dict(new_dir)
