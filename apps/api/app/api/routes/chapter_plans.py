"""Chapter plan routes — generate, list, edit, adopt, reject, regenerate, merge."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ChapterPlan, NovelProject
from app.db.session import get_session
from app.schemas.chapter_plan import (
    ChapterPlanOut,
    ChapterPlanUpdate,
    GeneratePlansRequest,
    MergeRequest,
)
from app.services.chapter_plan_service import (
    adopt_plan,
    edit_plan,
    generate_plans,
    merge_plans,
    regenerate_plan,
    reject_plan,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/projects/{project_id}/chapter-plans", tags=["chapter-plans"])

DB = Annotated[AsyncSession, Depends(get_session)]


def _to_dict(p: ChapterPlan) -> dict:
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
        "rhythm_id": p.rhythm_id,
        "plan_index": p.plan_index,
        "status": p.status,
        "is_adopted": p.is_adopted,
        "chapter_goal": p.chapter_goal,
        "characters": p.characters,
        "scenes": p.scenes,
        "obstacle": p.obstacle,
        "turning_point": p.turning_point,
        "information_gain": p.information_gain,
        "emotion_curve": p.emotion_curve,
        "payoff": p.payoff,
        "foreshadow_action": p.foreshadow_action,
        "foreshadow_resolved": p.foreshadow_resolved,
        "relationship_changes": p.relationship_changes,
        "end_state": p.end_state,
        "chapter_hook": p.chapter_hook,
        "repetition_risk": p.repetition_risk,
        "logic_issues": p.logic_issues,
        "ai_original_json": p.ai_original_json,
        "human_edits_json": p.human_edits_json,
        "locked_fields_json": p.locked_fields_json,
        "created_at": created or now,
        "updated_at": updated or now,
    }


@router.post("/generate", response_model=list[ChapterPlanOut])
async def generate(project_id: str, req: GeneratePlansRequest, session: DB):
    """Generate 3 distinct chapter plan variants from a rhythm record."""
    project = await session.get(NovelProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    try:
        plans = await generate_plans(session, project_id, req.rhythm_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Plan generation failed")
        raise HTTPException(status_code=500, detail=str(e))
    return [_to_dict(p) for p in plans]


@router.get("", response_model=list[ChapterPlanOut])
async def list_plans(project_id: str, session: DB, rhythm_id: str | None = None):
    stmt = select(ChapterPlan).where(ChapterPlan.project_id == project_id)
    if rhythm_id:
        stmt = stmt.where(ChapterPlan.rhythm_id == rhythm_id)
    stmt = stmt.order_by(ChapterPlan.plan_index)
    result = await session.execute(stmt)
    return [_to_dict(p) for p in result.scalars().all()]


@router.get("/{plan_id}", response_model=ChapterPlanOut)
async def get_plan(project_id: str, plan_id: str, session: DB):
    plan = await session.get(ChapterPlan, plan_id)
    if not plan or plan.project_id != project_id:
        raise HTTPException(status_code=404, detail="Plan not found")
    return _to_dict(plan)


@router.patch("/{plan_id}", response_model=ChapterPlanOut)
async def update_plan(project_id: str, plan_id: str, data: ChapterPlanUpdate, session: DB):
    try:
        plan = await edit_plan(session, plan_id, data.model_dump(exclude_unset=True))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _to_dict(plan)


@router.post("/{plan_id}/adopt", response_model=ChapterPlanOut)
async def adopt(project_id: str, plan_id: str, session: DB):
    try:
        plan = await adopt_plan(session, plan_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _to_dict(plan)


@router.post("/{plan_id}/reject", response_model=ChapterPlanOut)
async def reject(project_id: str, plan_id: str, session: DB):
    try:
        plan = await reject_plan(session, plan_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _to_dict(plan)


@router.post("/{plan_id}/regenerate", response_model=ChapterPlanOut)
async def regenerate(project_id: str, plan_id: str, session: DB):
    try:
        plan = await regenerate_plan(session, project_id, plan_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _to_dict(plan)


@router.post("/merge", response_model=ChapterPlanOut)
async def merge(project_id: str, req: MergeRequest, session: DB):
    project = await session.get(NovelProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    try:
        plan = await merge_plans(session, project_id, req.source_ids, req.field_sources)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _to_dict(plan)
