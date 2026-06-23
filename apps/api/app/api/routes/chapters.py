"""Chapter routes — parse, list, detail, update, merge, split."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Chapter, SourceDocument
from app.db.session import get_session
from app.schemas.chapter import (
    ChapterDetail,
    ChapterMergeRequest,
    ChapterOut,
    ChapterSplitRequest,
    ChapterUpdate,
    ParseExecuteRequest,
    ParsePreviewItem,
    ParsePreviewResponse,
)
from app.services.text_cleaner import clean_text, detect_and_decode
from app.services.text_splitter import preview_split, split_text

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/documents/{doc_id}/chapters", tags=["chapters"])

DB = Annotated[AsyncSession, Depends(get_session)]


def _ch_to_dict(ch: Chapter) -> dict:
    """Serialize Chapter to dict to avoid lazy-load issues after flush."""
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    try:
        updated = ch.updated_at
    except Exception:
        updated = now
    try:
        created = ch.created_at
    except Exception:
        created = now
    return {
        "id": ch.id,
        "document_id": ch.document_id,
        "chapter_index": ch.chapter_index,
        "volume_name": ch.volume_name,
        "title": ch.title,
        "word_count": ch.word_count,
        "parse_source": ch.parse_source,
        "created_at": created or now,
        "updated_at": updated or now,
    }


def _ch_detail_dict(ch: Chapter) -> dict:
    d = _ch_to_dict(ch)
    d["content"] = ch.content
    d["content_hash"] = ch.content_hash
    return d


async def _get_document(doc_id: str, session: AsyncSession) -> SourceDocument:
    doc = await session.get(SourceDocument, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


def _read_and_clean(doc: SourceDocument) -> tuple[str, str]:
    """Read file, detect encoding, clean text. Returns (cleaned_text, encoding)."""
    raw = Path(doc.storage_path).read_bytes()
    text, encoding = detect_and_decode(raw)
    cleaned = clean_text(text)
    return cleaned, encoding


# === Parse ===


@router.get("/parse-preview", response_model=ParsePreviewResponse)
async def parse_preview(doc_id: str, session: DB):
    """Preview how the document will be split into chapters (without saving)."""
    doc = await _get_document(doc_id, session)
    if not doc.storage_path:
        raise HTTPException(status_code=400, detail="Document has no stored file")

    try:
        cleaned, encoding = _read_and_clean(doc)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    preview = preview_split(cleaned)
    return ParsePreviewResponse(
        encoding_detected=encoding,
        total_chapters=len(preview),
        chapters=[ParsePreviewItem(**p) for p in preview],
    )


@router.post("/parse", response_model=list[ChapterOut])
async def parse_document(doc_id: str, session: DB, _req: ParseExecuteRequest | None = None):
    """Parse document into chapters. Uses transaction: deletes old chapters, creates new ones.

    If parsing fails, old data is preserved.
    """
    doc = await _get_document(doc_id, session)
    if not doc.storage_path:
        raise HTTPException(status_code=400, detail="Document has no stored file")

    try:
        cleaned, encoding = _read_and_clean(doc)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    chapters_data = split_text(cleaned)

    # Begin transactional replace
    # Delete existing chapters for this document
    existing = await session.execute(select(Chapter).where(Chapter.document_id == doc_id))
    for ch in existing.scalars().all():
        await session.delete(ch)

    # Create new chapters
    new_chapters = []
    for sc in chapters_data:
        content_hash = hashlib.sha256(sc.content.encode()).hexdigest()
        ch = Chapter(
            document_id=doc_id,
            chapter_index=sc.index,
            volume_name=sc.volume_name,
            title=sc.title,
            content=sc.content,
            content_hash=content_hash,
            word_count=len(sc.content),
            parse_source="auto",
        )
        session.add(ch)
        new_chapters.append(ch)

    await session.flush()
    for ch in new_chapters:
        await session.refresh(ch)

    return new_chapters


# === CRUD ===


@router.get("", response_model=list[ChapterOut])
async def list_chapters(doc_id: str, session: DB):
    await _get_document(doc_id, session)
    result = await session.execute(select(Chapter).where(Chapter.document_id == doc_id).order_by(Chapter.chapter_index))
    return result.scalars().all()


@router.get("/{chapter_id}", response_model=ChapterDetail)
async def get_chapter(doc_id: str, chapter_id: str, session: DB):
    ch = await session.get(Chapter, chapter_id)
    if not ch or ch.document_id != doc_id:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return ch


@router.patch("/{chapter_id}", response_model=ChapterOut)
async def update_chapter(doc_id: str, chapter_id: str, data: ChapterUpdate, session: DB):
    """Update chapter metadata (rename, reorder, change volume, mark source)."""
    ch = await session.get(Chapter, chapter_id)
    if not ch or ch.document_id != doc_id:
        raise HTTPException(status_code=404, detail="Chapter not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(ch, key, value)
    await session.flush()
    return _ch_to_dict(ch)


# === Merge ===


@router.post("/merge", response_model=ChapterOut)
async def merge_chapters(doc_id: str, req: ChapterMergeRequest, session: DB):
    """Merge multiple chapters into one. Content is concatenated in the order of chapter_ids."""
    await _get_document(doc_id, session)

    # Fetch all chapters in order
    chapters = []
    for cid in req.chapter_ids:
        ch = await session.get(Chapter, cid)
        if not ch or ch.document_id != doc_id:
            raise HTTPException(status_code=404, detail=f"Chapter not found: {cid}")
        chapters.append(ch)

    # Sort by current index to maintain order
    chapters.sort(key=lambda c: c.chapter_index)

    # Merge content
    merged_content = "\n\n".join(ch.content for ch in chapters)
    merged_title = req.new_title or chapters[0].title
    merged_volume = chapters[0].volume_name
    merged_hash = hashlib.sha256(merged_content.encode()).hexdigest()
    min_index = min(ch.chapter_index for ch in chapters)

    # Keep the first chapter, delete the rest
    primary = chapters[0]
    primary.title = merged_title
    primary.content = merged_content
    primary.content_hash = merged_hash
    primary.word_count = len(merged_content)
    primary.chapter_index = min_index
    primary.volume_name = merged_volume
    primary.parse_source = "manual"

    for ch in chapters[1:]:
        await session.delete(ch)

    # Reindex remaining chapters
    all_chapters = (
        (await session.execute(select(Chapter).where(Chapter.document_id == doc_id).order_by(Chapter.chapter_index)))
        .scalars()
        .all()
    )
    for i, ch in enumerate(all_chapters):
        ch.chapter_index = i

    await session.flush()
    return _ch_to_dict(primary)


# === Split ===


@router.post("/{chapter_id}/split", response_model=list[ChapterOut])
async def split_chapter(doc_id: str, chapter_id: str, req: ChapterSplitRequest, session: DB):
    """Split a chapter at the given character position into two chapters."""
    ch = await session.get(Chapter, chapter_id)
    if not ch or ch.document_id != doc_id:
        raise HTTPException(status_code=404, detail="Chapter not found")

    if req.split_position >= len(ch.content) or req.split_position < 1:
        raise HTTPException(status_code=400, detail="Invalid split position")

    # Split content
    first_content = ch.content[: req.split_position].strip()
    second_content = ch.content[req.split_position :].strip()

    if not first_content or not second_content:
        raise HTTPException(status_code=400, detail="Split would create an empty chapter")

    # Update original chapter (first half)
    ch.content = first_content
    ch.content_hash = hashlib.sha256(first_content.encode()).hexdigest()
    ch.word_count = len(first_content)
    ch.parse_source = "manual"

    # Create new chapter (second half) right after original
    new_ch = Chapter(
        document_id=doc_id,
        chapter_index=ch.chapter_index + 1,
        volume_name=ch.volume_name,
        title=req.new_title,
        content=second_content,
        content_hash=hashlib.sha256(second_content.encode()).hexdigest(),
        word_count=len(second_content),
        parse_source="manual",
    )
    session.add(new_ch)

    # Reindex all chapters after the split
    later = await session.execute(
        select(Chapter)
        .where(Chapter.document_id == doc_id, Chapter.chapter_index > ch.chapter_index, Chapter.id != ch.id)
        .order_by(Chapter.chapter_index)
    )
    for i, c in enumerate(later.scalars().all(), start=ch.chapter_index + 2):
        c.chapter_index = i

    await session.flush()
    return [_ch_to_dict(ch), _ch_to_dict(new_ch)]


# === Delete ===


@router.delete("/{chapter_id}", status_code=204)
async def delete_chapter(doc_id: str, chapter_id: str, session: DB):
    ch = await session.get(Chapter, chapter_id)
    if not ch or ch.document_id != doc_id:
        raise HTTPException(status_code=404, detail="Chapter not found")
    await session.delete(ch)

    # Reindex remaining
    remaining = await session.execute(
        select(Chapter).where(Chapter.document_id == doc_id).order_by(Chapter.chapter_index)
    )
    for i, c in enumerate(remaining.scalars().all()):
        c.chapter_index = i
