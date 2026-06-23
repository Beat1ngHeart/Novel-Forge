"""Rhythm routes — chapter rhythm plan CRUD, generate, reorder, insert, delete."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ChapterRhythmPlan, NovelProject
from app.db.session import get_session
from app.schemas.rhythm import (
    ChapterRhythmOut,
    ChapterRhythmUpdate,
    GenerateRhythmRequest,
    InsertRequest,
    ReorderRequest,
)
from app.services.rhythm_service import (
    adopt_plan,
    delete_chapter,
    edit_plan,
    generate_rhythm_plans,
    insert_chapter,
    regenerate_single,
    reorder_plans,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/projects/{project_id}/rhythms", tags=["rhythms"])

DB = Annotated[AsyncSession, Depends(get_session)]


def _to_dict(p: ChapterRhythmPlan) -> dict:
    now = datetime.now(timezone.utc)
    try:
        created = p.created_at
    except Exception:
        created = now
    try:
        updated = p.updated_at
    except Exception:
        updated = now
    return {
        "id": p.id,
        "project_id": p.project_id,
        "volume_id": p.volume_id,
        "chapter_index": p.chapter_index,
        "status": p.status,
        "is_current": p.is_current,
        "temp_title": p.temp_title,
        "chapter_function": p.chapter_function,
        "core_event": p.core_event,
        "protagonist_goal": p.protagonist_goal,
        "main_obstacle": p.main_obstacle,
        "conflict_type": p.conflict_type,
        "information_gain": p.information_gain,
        "character_change": p.character_change,
        "payoff_or_emotion": p.payoff_or_emotion,
        "foreshadow_action": p.foreshadow_action,
        "chapter_hook": p.chapter_hook,
        "volume_goal_connection": p.volume_goal_connection,
        "estimated_words": p.estimated_words,
        "risk_notes": p.risk_notes,
        "ai_original_json": p.ai_original_json,
        "human_edits_json": p.human_edits_json,
        "created_at": created or now,
        "updated_at": updated or now,
    }


@router.post("/generate", response_model=list[ChapterRhythmOut])
async def generate(project_id: str, req: GenerateRhythmRequest, session: DB):
    """Generate chapter rhythm plans for a volume."""
    project = await session.get(NovelProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    try:
        plans = await generate_rhythm_plans(session, project_id, req.volume_id, req.chapter_count)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Rhythm generation failed")
        raise HTTPException(status_code=500, detail=str(e))
    return [_to_dict(p) for p in plans]


@router.get("", response_model=list[ChapterRhythmOut])
async def list_plans(project_id: str, session: DB, volume_id: str | None = None):
    stmt = select(ChapterRhythmPlan).where(ChapterRhythmPlan.project_id == project_id)
    if volume_id:
        stmt = stmt.where(ChapterRhythmPlan.volume_id == volume_id)
    stmt = stmt.order_by(ChapterRhythmPlan.chapter_index)
    result = await session.execute(stmt)
    return [_to_dict(p) for p in result.scalars().all()]


@router.get("/{plan_id}", response_model=ChapterRhythmOut)
async def get_plan(project_id: str, plan_id: str, session: DB):
    plan = await session.get(ChapterRhythmPlan, plan_id)
    if not plan or plan.project_id != project_id:
        raise HTTPException(status_code=404, detail="Plan not found")
    return _to_dict(plan)


@router.patch("/{plan_id}", response_model=ChapterRhythmOut)
async def update_plan(project_id: str, plan_id: str, data: ChapterRhythmUpdate, session: DB):
    try:
        plan = await edit_plan(session, plan_id, data.model_dump(exclude_unset=True))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _to_dict(plan)


@router.post("/{plan_id}/adopt", response_model=ChapterRhythmOut)
async def adopt(project_id: str, plan_id: str, session: DB):
    try:
        plan = await adopt_plan(session, plan_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _to_dict(plan)


@router.post("/{plan_id}/regenerate", response_model=ChapterRhythmOut)
async def regenerate(project_id: str, plan_id: str, session: DB):
    try:
        plan = await regenerate_single(session, project_id, plan_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _to_dict(plan)


@router.post("/insert", response_model=list[ChapterRhythmOut])
async def insert(project_id: str, body: InsertRequest, session: DB):
    """Insert a new chapter after the given index."""
    project = await session.get(NovelProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    # Get volume_id from existing plans
    existing = (
        await session.execute(select(ChapterRhythmPlan).where(ChapterRhythmPlan.project_id == project_id).limit(1))
    ).scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=400, detail="No rhythm plans exist yet")
    try:
        plans = await insert_chapter(
            session,
            project_id,
            existing.volume_id,
            body.after_index,
            body.temp_title,
            body.chapter_function,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return [_to_dict(p) for p in plans]


@router.delete("/{plan_id}", response_model=list[ChapterRhythmOut])
async def delete_plan(project_id: str, plan_id: str, session: DB):
    try:
        plans = await delete_chapter(session, project_id, plan_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return [_to_dict(p) for p in plans]


@router.post("/reorder", response_model=list[ChapterRhythmOut])
async def reorder(project_id: str, body: ReorderRequest, session: DB):
    try:
        plans = await reorder_plans(session, project_id, body.chapter_ids)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return [_to_dict(p) for p in plans]
