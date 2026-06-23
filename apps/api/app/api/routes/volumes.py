"""Volume routes — generate, list, edit, adopt, regenerate, reorder."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import NovelProject, VolumeOutline
from app.db.session import get_session
from app.schemas.volume import (
    GenerateVolumesRequest,
    VolumeOut,
    VolumeReorder,
    VolumeUpdate,
)
from app.services.volume_service import (
    adopt_volume,
    edit_volume,
    generate_all_volumes,
    regenerate_volume,
    reorder_volumes,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/projects/{project_id}/volumes", tags=["volumes"])

DB = Annotated[AsyncSession, Depends(get_session)]


def _to_dict(v: VolumeOutline) -> dict:
    now = datetime.now(timezone.utc)
    try:
        created = v.created_at
    except Exception:
        created = now
    try:
        updated = v.updated_at
    except Exception:
        updated = now
    return {
        "id": v.id,
        "project_id": v.project_id,
        "synopsis_id": v.synopsis_id,
        "volume_index": v.volume_index,
        "volume_name": v.volume_name,
        "status": v.status,
        "is_current": v.is_current,
        "volume_goal": v.volume_goal,
        "core_conflict": v.core_conflict,
        "start_state": v.start_state,
        "end_state": v.end_state,
        "main_enemy": v.main_enemy,
        "character_changes": v.character_changes,
        "new_world_settings": v.new_world_settings,
        "growth_milestone": v.growth_milestone,
        "payoff_climax": v.payoff_climax,
        "volume_twist": v.volume_twist,
        "foreshadow_planted": v.foreshadow_planted,
        "foreshadow_resolved": v.foreshadow_resolved,
        "reader_promise_fulfilled": v.reader_promise_fulfilled,
        "estimated_chapters": v.estimated_chapters,
        "estimated_words": v.estimated_words,
        "ai_original_json": v.ai_original_json,
        "human_edits_json": v.human_edits_json,
        "created_at": created or now,
        "updated_at": updated or now,
    }


@router.post("/generate", response_model=list[VolumeOut])
async def generate(project_id: str, req: GenerateVolumesRequest, session: DB):
    """Generate all volume outlines from an adopted synopsis."""
    project = await session.get(NovelProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    try:
        volumes = await generate_all_volumes(session, project_id, req.synopsis_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Volume generation failed")
        raise HTTPException(status_code=500, detail=str(e))
    return [_to_dict(v) for v in volumes]


@router.get("", response_model=list[VolumeOut])
async def list_volumes(project_id: str, session: DB, synopsis_id: str | None = None):
    """List volumes, optionally filtered by synopsis."""
    stmt = select(VolumeOutline).where(VolumeOutline.project_id == project_id)
    if synopsis_id:
        stmt = stmt.where(VolumeOutline.synopsis_id == synopsis_id)
    stmt = stmt.order_by(VolumeOutline.volume_index)
    result = await session.execute(stmt)
    return [_to_dict(v) for v in result.scalars().all()]


@router.get("/{volume_id}", response_model=VolumeOut)
async def get_volume(project_id: str, volume_id: str, session: DB):
    vol = await session.get(VolumeOutline, volume_id)
    if not vol or vol.project_id != project_id:
        raise HTTPException(status_code=404, detail="Volume not found")
    return _to_dict(vol)


@router.patch("/{volume_id}", response_model=VolumeOut)
async def update_volume(project_id: str, volume_id: str, data: VolumeUpdate, session: DB):
    """Edit a volume. AI original preserved; human edits recorded."""
    try:
        vol = await edit_volume(session, volume_id, data.model_dump(exclude_unset=True))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _to_dict(vol)


@router.post("/{volume_id}/adopt", response_model=VolumeOut)
async def adopt(project_id: str, volume_id: str, session: DB):
    """Adopt a volume."""
    try:
        vol = await adopt_volume(session, volume_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _to_dict(vol)


@router.post("/{volume_id}/regenerate", response_model=VolumeOut)
async def regenerate(project_id: str, volume_id: str, session: DB):
    """Regenerate a single volume without affecting others."""
    try:
        vol = await regenerate_volume(session, project_id, volume_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _to_dict(vol)


@router.post("/reorder", response_model=list[VolumeOut])
async def reorder(project_id: str, body: VolumeReorder, session: DB):
    """Reorder volumes."""
    try:
        volumes = await reorder_volumes(session, project_id, body.volume_ids)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return [_to_dict(v) for v in volumes]
