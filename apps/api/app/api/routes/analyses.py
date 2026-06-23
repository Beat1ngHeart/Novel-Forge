"""Analysis routes — trigger analysis, view results, view history."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Chapter, ChapterAnalysis, SourceDocument
from app.db.session import get_session
from app.schemas.analysis import (
    AnalysisDetail,
    AnalysisOut,
    AnalysisRequest,
    AnalysisResultView,
)
from app.services.analysis_service import (
    analyze_chapter,
    get_analysis_history,
    get_latest_analysis,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/chapters/{chapter_id}/analyses", tags=["analyses"])

DB = Annotated[AsyncSession, Depends(get_session)]


def _analysis_to_dict(a: ChapterAnalysis) -> dict:
    now = datetime.now(timezone.utc)
    try:
        updated = a.updated_at
    except Exception:
        updated = now
    try:
        created = a.created_at
    except Exception:
        created = now
    return {
        "id": a.id,
        "chapter_id": a.chapter_id,
        "document_id": a.document_id,
        "project_id": a.project_id,
        "schema_version": a.schema_version,
        "prompt_version": a.prompt_version,
        "provider": a.provider,
        "model": a.model,
        "status": a.status,
        "confidence": a.confidence,
        "chapter_function": a.chapter_function,
        "chapter_summary": a.chapter_summary,
        "hook_type": a.hook_type,
        "hook_intensity": a.hook_intensity,
        "error_message": a.error_message,
        "result_json": a.result_json,
        "llm_call_id": a.llm_call_id,
        "created_at": created or now,
        "updated_at": updated or now,
    }


async def _validate_chapter_access(chapter_id: str, session: AsyncSession) -> tuple[Chapter, SourceDocument]:
    """Validate chapter exists and return chapter + document."""
    chapter = await session.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    doc = await session.get(SourceDocument, chapter.document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return chapter, doc


@router.post("", response_model=AnalysisOut, status_code=201)
async def trigger_analysis(chapter_id: str, session: DB, req: AnalysisRequest | None = None):
    """Trigger story gene analysis for a chapter. Returns the analysis result."""
    chapter, doc = await _validate_chapter_access(chapter_id, session)

    # Rights check
    if doc.rights_status == "prohibited":
        raise HTTPException(
            status_code=403,
            detail="该资料权利状态为「禁止使用」，不允许分析",
        )

    prompt_version = req.prompt_version if req else "v1"

    try:
        analysis = await analyze_chapter(session, chapter_id, prompt_version)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Analysis failed")
        raise HTTPException(status_code=500, detail=f"分析失败: {e}")

    return _analysis_to_dict(analysis)


@router.get("", response_model=list[AnalysisOut])
async def list_analyses(chapter_id: str, session: DB):
    """List all analysis results for a chapter (newest first)."""
    await _validate_chapter_access(chapter_id, session)
    analyses = await get_analysis_history(session, chapter_id)
    return [_analysis_to_dict(a) for a in analyses]


@router.get("/latest", response_model=AnalysisOut | None)
async def get_latest(chapter_id: str, session: DB):
    """Get the most recent completed analysis for a chapter."""
    await _validate_chapter_access(chapter_id, session)
    analysis = await get_latest_analysis(session, chapter_id)
    if not analysis:
        return None
    return _analysis_to_dict(analysis)


@router.get("/{analysis_id}", response_model=AnalysisDetail)
async def get_analysis(chapter_id: str, analysis_id: str, session: DB):
    """Get a specific analysis result by ID."""
    await _validate_chapter_access(chapter_id, session)
    analysis = await session.get(ChapterAnalysis, analysis_id)
    if not analysis or analysis.chapter_id != chapter_id:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return _analysis_to_dict(analysis)


@router.get("/{analysis_id}/result", response_model=AnalysisResultView)
async def get_analysis_result(chapter_id: str, analysis_id: str, session: DB):
    """Get the structured result of a completed analysis."""
    await _validate_chapter_access(chapter_id, session)
    analysis = await session.get(ChapterAnalysis, analysis_id)
    if not analysis or analysis.chapter_id != chapter_id:
        raise HTTPException(status_code=404, detail="Analysis not found")
    if analysis.status != "completed":
        raise HTTPException(status_code=400, detail=f"Analysis status is {analysis.status}, not completed")
    if not analysis.result_json:
        raise HTTPException(status_code=404, detail="No result data")

    try:
        data = json.loads(analysis.result_json)
        return AnalysisResultView(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse result: {e}")
