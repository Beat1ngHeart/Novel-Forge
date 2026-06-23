"""Document routes — file upload with rights registration, list, detail, delete."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import NovelProject, SourceDocument
from app.db.session import get_session
from app.schemas.document import DocumentOut
from app.services import file_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

DB = Annotated[AsyncSession, Depends(get_session)]


@router.post("", response_model=DocumentOut, status_code=201)
async def upload_document(
    session: DB,
    file: UploadFile = File(...),
    project_id: str | None = Form(None),
    title: str = Form(""),
    source_name: str = Form(""),
    author_name: str = Form(""),
    rights_status: str = Form("unknown"),
):
    """Upload a TXT or Markdown file with rights registration."""
    filename = file.filename or "unknown.txt"

    # Read file data
    data = await file.read()

    # Validate extension
    ext_error = file_service.validate_extension(filename)
    if ext_error:
        raise HTTPException(status_code=400, detail=ext_error)

    # Validate size
    if len(data) > file_service.MAX_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"文件过大: {len(data) / 1024 / 1024:.1f}MB，最大 {file_service.MAX_SIZE_BYTES / 1024 / 1024:.0f}MB",
        )
    if len(data) == 0:
        raise HTTPException(status_code=400, detail="文件为空")

    # Detect and validate MIME type
    mime_type = file_service.detect_mime_type(filename, data)
    mime_error = file_service.validate_mime(mime_type)
    if mime_error:
        raise HTTPException(status_code=400, detail=mime_error)

    # Check project exists if specified
    if project_id:
        project = await session.get(NovelProject, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

    # Compute hash
    sha = file_service.compute_sha256(data)

    # Check for duplicate (same SHA-256 in same project)
    dup_stmt = select(SourceDocument).where(SourceDocument.sha256 == sha)
    if project_id:
        dup_stmt = dup_stmt.where(SourceDocument.project_id == project_id)
    existing = (await session.execute(dup_stmt.limit(1))).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"文件已存在 (ID: {existing.id})，SHA-256: {sha[:16]}...",
        )

    # Determine rights defaults
    rights_defaults = file_service.file_rights_defaults(rights_status)

    # Sanitize filename and save
    safe_filename = file_service.sanitize_filename(filename)
    ext = Path(safe_filename).suffix.lower()

    file_path = None
    try:
        file_path = file_service.save_file(project_id or "_unassigned", safe_filename, data)
    except Exception:
        logger.exception("Failed to save file")
        raise HTTPException(status_code=500, detail="文件保存失败")

    try:
        doc = SourceDocument(
            project_id=project_id,
            title=title or safe_filename,
            original_filename=safe_filename,
            stored_filename=file_path.name,
            file_type=ext.lstrip("."),
            mime_type=mime_type,
            file_size=len(data),
            sha256=sha,
            source_name=source_name,
            author_name=author_name,
            rights_status=rights_status,
            analysis_allowed=rights_defaults["analysis_allowed"],
            generation_reference_allowed=rights_defaults["generation_reference_allowed"],
            storage_path=str(file_path),
            parse_status="completed",
        )
        session.add(doc)
        await session.flush()
        await session.refresh(doc)
        return doc
    except Exception:
        # Cleanup file on database error
        if file_path:
            file_service.cleanup_file(str(file_path))
        raise


@router.get("", response_model=list[DocumentOut])
async def list_documents(
    session: DB,
    project_id: str | None = Query(None),
    rights_status: str | None = Query(None),
):
    """List documents, optionally filtered by project or rights status."""
    stmt = select(SourceDocument).order_by(SourceDocument.created_at.desc())
    if project_id:
        stmt = stmt.where(SourceDocument.project_id == project_id)
    if rights_status:
        stmt = stmt.where(SourceDocument.rights_status == rights_status)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get("/{doc_id}", response_model=DocumentOut)
async def get_document(doc_id: str, session: DB):
    doc = await session.get(SourceDocument, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.delete("/{doc_id}", status_code=204)
async def delete_document(doc_id: str, session: DB):
    """Delete document and its file from disk. Cascade deletes chapters."""
    doc = await session.get(SourceDocument, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    # Delete file from disk
    if doc.storage_path:
        file_service.cleanup_file(doc.storage_path)
    await session.delete(doc)
