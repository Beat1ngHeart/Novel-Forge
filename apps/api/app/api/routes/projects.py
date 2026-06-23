"""Project routes — full CRUD, archive/restore, search, filter, sort, pagination, stats."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from math import ceil
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Chapter, NovelProject, SourceDocument
from app.db.session import get_session
from app.schemas.project import (
    PaginatedResponse,
    ProjectCreate,
    ProjectOut,
    ProjectStats,
    ProjectUpdate,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/projects", tags=["projects"])

DB = Annotated[AsyncSession, Depends(get_session)]

# Subqueries for counts
_doc_count_sq = (
    select(SourceDocument.project_id, func.count(SourceDocument.id).label("cnt"))
    .group_by(SourceDocument.project_id)
    .subquery()
)
_ch_count_sq = (
    select(SourceDocument.project_id, func.count(Chapter.id).label("cnt"))
    .join(Chapter, Chapter.document_id == SourceDocument.id)
    .group_by(SourceDocument.project_id)
    .subquery()
)


def _base_query():
    return (
        select(
            NovelProject,
            func.coalesce(_doc_count_sq.c.cnt, 0).label("document_count"),
            func.coalesce(_ch_count_sq.c.cnt, 0).label("chapter_count"),
        )
        .outerjoin(_doc_count_sq, NovelProject.id == _doc_count_sq.c.project_id)
        .outerjoin(_ch_count_sq, NovelProject.id == _ch_count_sq.c.project_id)
    )


def _row_to_out(row) -> dict:
    p = row[0]
    return {
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "genre": p.genre,
        "subgenre": p.subgenre,
        "audience_type": p.audience_type,
        "target_platform": p.target_platform,
        "target_reader": p.target_reader,
        "target_word_count": p.target_word_count,
        "chapter_word_count": p.chapter_word_count,
        "update_frequency": p.update_frequency,
        "language": p.language,
        "status": p.status,
        "current_volume": p.current_volume,
        "current_chapter": p.current_chapter,
        "created_at": p.created_at,
        "updated_at": p.updated_at,
        "archived_at": p.archived_at,
        "document_count": row.document_count,
        "chapter_count": row.chapter_count,
    }


@router.post("", response_model=ProjectOut, status_code=201)
async def create_project(data: ProjectCreate, session: DB):
    project = NovelProject(**data.model_dump())
    session.add(project)
    await session.flush()
    result = await session.execute(_base_query().where(NovelProject.id == project.id))
    row = result.one()
    return _row_to_out(row)


@router.get("", response_model=PaginatedResponse)
async def list_projects(
    session: DB,
    search: str = Query("", description="搜索名称或描述"),
    genre: str = Query("", description="按题材筛选"),
    status: str = Query("", description="按状态筛选"),
    audience_type: str = Query("", description="按频道筛选"),
    include_archived: bool = Query(False, description="包含已归档"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    stmt = _base_query()

    if not include_archived:
        stmt = stmt.where(NovelProject.archived_at.is_(None))
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(or_(NovelProject.name.ilike(pattern), NovelProject.description.ilike(pattern)))
    if genre:
        stmt = stmt.where(NovelProject.genre == genre)
    if status:
        stmt = stmt.where(NovelProject.status == status)
    if audience_type:
        stmt = stmt.where(NovelProject.audience_type == audience_type)

    # Count total
    count_sub = stmt.subquery()
    total = (await session.execute(select(func.count()).select_from(count_sub))).scalar() or 0

    # Sort
    sort_col = getattr(NovelProject, sort_by, NovelProject.created_at)
    stmt = stmt.order_by(sort_col.desc() if sort_order == "desc" else sort_col.asc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    result = await session.execute(stmt)
    rows = result.all()

    return PaginatedResponse(
        items=[_row_to_out(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=ceil(total / page_size) if total > 0 else 0,
    )


@router.get("/stats", response_model=ProjectStats)
async def project_stats(session: DB):
    total = (await session.execute(select(func.count(NovelProject.id)))).scalar() or 0
    active = (
        await session.execute(select(func.count(NovelProject.id)).where(NovelProject.archived_at.is_(None)))
    ).scalar() or 0

    doc_count = (await session.execute(select(func.count(SourceDocument.id)))).scalar() or 0
    ch_count = (await session.execute(select(func.count(Chapter.id)))).scalar() or 0

    genre_rows = (
        await session.execute(
            select(NovelProject.genre, func.count(NovelProject.id))
            .where(NovelProject.archived_at.is_(None))
            .group_by(NovelProject.genre)
        )
    ).all()
    by_genre = {g or "未分类": c for g, c in genre_rows}

    status_rows = (
        await session.execute(
            select(NovelProject.status, func.count(NovelProject.id))
            .where(NovelProject.archived_at.is_(None))
            .group_by(NovelProject.status)
        )
    ).all()
    by_status = {s or "未知": c for s, c in status_rows}

    return ProjectStats(
        total_projects=total,
        active_projects=active,
        archived_projects=total - active,
        total_documents=doc_count,
        total_chapters=ch_count,
        by_genre=by_genre,
        by_status=by_status,
    )


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: str, session: DB):
    result = await session.execute(_base_query().where(NovelProject.id == project_id))
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Project not found")
    return _row_to_out(row)


@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project(project_id: str, data: ProjectUpdate, session: DB):
    project = await session.get(NovelProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.archived_at is not None:
        raise HTTPException(status_code=400, detail="Cannot edit archived project. Restore it first.")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(project, key, value)
    await session.flush()
    result = await session.execute(_base_query().where(NovelProject.id == project_id))
    return _row_to_out(result.one())


@router.post("/{project_id}/archive", response_model=ProjectOut)
async def archive_project(project_id: str, session: DB):
    project = await session.get(NovelProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.archived_at is not None:
        raise HTTPException(status_code=400, detail="Project is already archived")
    project.archived_at = datetime.now(timezone.utc)
    await session.flush()
    result = await session.execute(_base_query().where(NovelProject.id == project_id))
    return _row_to_out(result.one())


@router.post("/{project_id}/restore", response_model=ProjectOut)
async def restore_project(project_id: str, session: DB):
    project = await session.get(NovelProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.archived_at is None:
        raise HTTPException(status_code=400, detail="Project is not archived")
    project.archived_at = None
    await session.flush()
    result = await session.execute(_base_query().where(NovelProject.id == project_id))
    return _row_to_out(result.one())


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: str, session: DB):
    project = await session.get(NovelProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await session.delete(project)
