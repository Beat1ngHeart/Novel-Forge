"""Bible routes — CRUD for characters, world rules, plot threads, foreshadowings."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Character, Foreshadowing, NovelProject, PlotThread, WorldRule
from app.db.session import get_session
from app.schemas.bible import (
    CharacterCreate,
    CharacterOut,
    CharacterUpdate,
    ForeshadowingCreate,
    ForeshadowingOut,
    ForeshadowingUpdate,
    PlotThreadCreate,
    PlotThreadOut,
    PlotThreadUpdate,
    WorldRuleCreate,
    WorldRuleOut,
    WorldRuleUpdate,
)

DB = Annotated[AsyncSession, Depends(get_session)]

VALID_SOURCE_STATUSES = {"ai_suggestion", "user_confirmed", "text_fact", "deprecated"}


def _to_dict(obj) -> dict:
    now = datetime.now(timezone.utc)
    result = {}
    for col in obj.__table__.columns:
        try:
            val = getattr(obj, col.name)
        except Exception:
            val = now if "at" in col.name else ""
        if val is None and "at" in col.name:
            val = now
        result[col.name] = val
    return result


async def _get_project(project_id: str, session: AsyncSession) -> NovelProject:
    project = await session.get(NovelProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


# ============================================================
# Characters
# ============================================================

characters = APIRouter(prefix="/api/v1/projects/{project_id}/characters", tags=["characters"])


@characters.get("", response_model=list[CharacterOut])
async def list_characters(
    project_id: str,
    session: DB,
    source_status: str | None = Query(None),
    search: str = Query(""),
):
    await _get_project(project_id, session)
    stmt = select(Character).where(Character.project_id == project_id)
    if source_status:
        stmt = stmt.where(Character.source_status == source_status)
    if search:
        stmt = stmt.where(Character.name.ilike(f"%{search}%"))
    stmt = stmt.order_by(Character.created_at.desc())
    result = await session.execute(stmt)
    return [_to_dict(r) for r in result.scalars().all()]


@characters.post("", response_model=CharacterOut, status_code=201)
async def create_character(project_id: str, data: CharacterCreate, session: DB):
    await _get_project(project_id, session)
    obj = Character(project_id=project_id, **data.model_dump())
    session.add(obj)
    await session.flush()
    return _to_dict(obj)


@characters.get("/{item_id}", response_model=CharacterOut)
async def get_character(project_id: str, item_id: str, session: DB):
    obj = await session.get(Character, item_id)
    if not obj or obj.project_id != project_id:
        raise HTTPException(status_code=404, detail="Character not found")
    return _to_dict(obj)


@characters.patch("/{item_id}", response_model=CharacterOut)
async def update_character(project_id: str, item_id: str, data: CharacterUpdate, session: DB):
    obj = await session.get(Character, item_id)
    if not obj or obj.project_id != project_id:
        raise HTTPException(status_code=404, detail="Character not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    await session.flush()
    return _to_dict(obj)


@characters.delete("/{item_id}", status_code=204)
async def delete_character(project_id: str, item_id: str, session: DB):
    obj = await session.get(Character, item_id)
    if not obj or obj.project_id != project_id:
        raise HTTPException(status_code=404, detail="Character not found")
    await session.delete(obj)


# ============================================================
# World Rules
# ============================================================

world_rules = APIRouter(prefix="/api/v1/projects/{project_id}/world-rules", tags=["world-rules"])


@world_rules.get("", response_model=list[WorldRuleOut])
async def list_world_rules(project_id: str, session: DB, source_status: str | None = None):
    await _get_project(project_id, session)
    stmt = select(WorldRule).where(WorldRule.project_id == project_id)
    if source_status:
        stmt = stmt.where(WorldRule.source_status == source_status)
    result = await session.execute(stmt.order_by(WorldRule.created_at.desc()))
    return [_to_dict(r) for r in result.scalars().all()]


@world_rules.post("", response_model=WorldRuleOut, status_code=201)
async def create_world_rule(project_id: str, data: WorldRuleCreate, session: DB):
    await _get_project(project_id, session)
    obj = WorldRule(project_id=project_id, **data.model_dump())
    session.add(obj)
    await session.flush()
    return _to_dict(obj)


@world_rules.get("/{item_id}", response_model=WorldRuleOut)
async def get_world_rule(project_id: str, item_id: str, session: DB):
    obj = await session.get(WorldRule, item_id)
    if not obj or obj.project_id != project_id:
        raise HTTPException(status_code=404, detail="WorldRule not found")
    return _to_dict(obj)


@world_rules.patch("/{item_id}", response_model=WorldRuleOut)
async def update_world_rule(project_id: str, item_id: str, data: WorldRuleUpdate, session: DB):
    obj = await session.get(WorldRule, item_id)
    if not obj or obj.project_id != project_id:
        raise HTTPException(status_code=404, detail="WorldRule not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    await session.flush()
    return _to_dict(obj)


@world_rules.delete("/{item_id}", status_code=204)
async def delete_world_rule(project_id: str, item_id: str, session: DB):
    obj = await session.get(WorldRule, item_id)
    if not obj or obj.project_id != project_id:
        raise HTTPException(status_code=404, detail="WorldRule not found")
    await session.delete(obj)


# ============================================================
# Plot Threads
# ============================================================

plot_threads = APIRouter(prefix="/api/v1/projects/{project_id}/plot-threads", tags=["plot-threads"])


@plot_threads.get("", response_model=list[PlotThreadOut])
async def list_plot_threads(project_id: str, session: DB, source_status: str | None = None):
    await _get_project(project_id, session)
    stmt = select(PlotThread).where(PlotThread.project_id == project_id)
    if source_status:
        stmt = stmt.where(PlotThread.source_status == source_status)
    result = await session.execute(stmt.order_by(PlotThread.created_at.desc()))
    return [_to_dict(r) for r in result.scalars().all()]


@plot_threads.post("", response_model=PlotThreadOut, status_code=201)
async def create_plot_thread(project_id: str, data: PlotThreadCreate, session: DB):
    await _get_project(project_id, session)
    obj = PlotThread(project_id=project_id, **data.model_dump())
    session.add(obj)
    await session.flush()
    return _to_dict(obj)


@plot_threads.get("/{item_id}", response_model=PlotThreadOut)
async def get_plot_thread(project_id: str, item_id: str, session: DB):
    obj = await session.get(PlotThread, item_id)
    if not obj or obj.project_id != project_id:
        raise HTTPException(status_code=404, detail="PlotThread not found")
    return _to_dict(obj)


@plot_threads.patch("/{item_id}", response_model=PlotThreadOut)
async def update_plot_thread(project_id: str, item_id: str, data: PlotThreadUpdate, session: DB):
    obj = await session.get(PlotThread, item_id)
    if not obj or obj.project_id != project_id:
        raise HTTPException(status_code=404, detail="PlotThread not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    await session.flush()
    return _to_dict(obj)


@plot_threads.delete("/{item_id}", status_code=204)
async def delete_plot_thread(project_id: str, item_id: str, session: DB):
    obj = await session.get(PlotThread, item_id)
    if not obj or obj.project_id != project_id:
        raise HTTPException(status_code=404, detail="PlotThread not found")
    await session.delete(obj)


# ============================================================
# Foreshadowings
# ============================================================

foreshadowings = APIRouter(prefix="/api/v1/projects/{project_id}/foreshadowings", tags=["foreshadowings"])


@foreshadowings.get("", response_model=list[ForeshadowingOut])
async def list_foreshadowings(project_id: str, session: DB, source_status: str | None = None):
    await _get_project(project_id, session)
    stmt = select(Foreshadowing).where(Foreshadowing.project_id == project_id)
    if source_status:
        stmt = stmt.where(Foreshadowing.source_status == source_status)
    result = await session.execute(stmt.order_by(Foreshadowing.created_at.desc()))
    return [_to_dict(r) for r in result.scalars().all()]


@foreshadowings.post("", response_model=ForeshadowingOut, status_code=201)
async def create_foreshadowing(project_id: str, data: ForeshadowingCreate, session: DB):
    await _get_project(project_id, session)
    obj = Foreshadowing(project_id=project_id, **data.model_dump())
    session.add(obj)
    await session.flush()
    return _to_dict(obj)


@foreshadowings.get("/{item_id}", response_model=ForeshadowingOut)
async def get_foreshadowing(project_id: str, item_id: str, session: DB):
    obj = await session.get(Foreshadowing, item_id)
    if not obj or obj.project_id != project_id:
        raise HTTPException(status_code=404, detail="Foreshadowing not found")
    return _to_dict(obj)


@foreshadowings.patch("/{item_id}", response_model=ForeshadowingOut)
async def update_foreshadowing(project_id: str, item_id: str, data: ForeshadowingUpdate, session: DB):
    obj = await session.get(Foreshadowing, item_id)
    if not obj or obj.project_id != project_id:
        raise HTTPException(status_code=404, detail="Foreshadowing not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    await session.flush()
    return _to_dict(obj)


@foreshadowings.delete("/{item_id}", status_code=204)
async def delete_foreshadowing(project_id: str, item_id: str, session: DB):
    obj = await session.get(Foreshadowing, item_id)
    if not obj or obj.project_id != project_id:
        raise HTTPException(status_code=404, detail="Foreshadowing not found")
    await session.delete(obj)
