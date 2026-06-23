"""Version service — manages draft versions, diff, restore, AI rewrite."""

from __future__ import annotations

import difflib
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ChapterDraft, DraftVersion
from app.llm import get_llm_provider
from app.llm.call_logger import track_llm_call

logger = logging.getLogger(__name__)

MOCK_REWRITE = "[改写] {text}"
MOCK_EXPAND = "{text}\n\n[扩写] 他深吸一口气，目光扫过四周。空气中弥漫灵气波动，回应他内心的悸动。"
MOCK_COMPRESS = "[压缩] {text_short}"
MOCK_TONE = "[语气调整：{tone}] {text}"


async def save_version(
    session: AsyncSession,
    draft_id: str,
    project_id: str,
    body_text: str,
    version_type: str = "user_edit",
    source: str = "",
    model: str = "",
    prompt_version: str = "",
    parent_version_id: str | None = None,
    llm_call_id: str = "",
) -> DraftVersion:
    """Save a new version of a draft."""
    # Get next version index
    result = await session.execute(
        select(DraftVersion.version_index)
        .where(DraftVersion.draft_id == draft_id)
        .order_by(DraftVersion.version_index.desc())
        .limit(1)
    )
    latest_idx = result.scalar()
    next_idx = (latest_idx + 1) if latest_idx is not None else 0

    version = DraftVersion(
        draft_id=draft_id,
        project_id=project_id,
        version_index=next_idx,
        version_type=version_type,
        body_text=body_text,
        source=source,
        model=model,
        prompt_version=prompt_version,
        word_count=len(body_text),
        is_final=False,
        parent_version_id=parent_version_id,
        llm_call_id=llm_call_id,
    )
    session.add(version)
    await session.flush()
    await session.refresh(version)

    # Update draft body_text
    draft = await session.get(ChapterDraft, draft_id)
    if draft:
        draft.body_text = body_text
        draft.actual_word_count = len(body_text)
        draft.status = version_type if version_type != "user_edit" else "human_revision"
        await session.flush()

    return version


async def mark_final(session: AsyncSession, version_id: str) -> DraftVersion:
    """Mark a version as final. Only one version per draft can be final."""
    version = await session.get(DraftVersion, version_id)
    if not version:
        raise ValueError("Version not found")

    # Unmark any existing final versions for this draft
    result = await session.execute(
        select(DraftVersion).where(
            DraftVersion.draft_id == version.draft_id,
            DraftVersion.is_final.is_(True),
        )
    )
    for v in result.scalars().all():
        v.is_final = False

    version.is_final = True
    await session.flush()
    return version


async def restore_version(session: AsyncSession, version_id: str) -> DraftVersion:
    """Restore a version as the current draft body."""
    version = await session.get(DraftVersion, version_id)
    if not version:
        raise ValueError("Version not found")

    draft = await session.get(ChapterDraft, version.draft_id)
    if not draft:
        raise ValueError("Draft not found")

    # Save current as a new version before restoring
    if draft.body_text:
        await save_version(
            session,
            draft.id,
            draft.project_id,
            draft.body_text,
            "user_edit",
            "before_restore",
            parent_version_id=version_id,
        )

    # Restore
    draft.body_text = version.body_text
    draft.actual_word_count = len(version.body_text)
    draft.status = "human_revision"
    await session.flush()
    return version


async def diff_versions(
    session: AsyncSession,
    version_a_id: str,
    version_b_id: str,
) -> dict:
    """Compare two versions and return diff."""
    va = await session.get(DraftVersion, version_a_id)
    vb = await session.get(DraftVersion, version_b_id)
    if not va or not vb:
        raise ValueError("Version not found")

    a_lines = va.body_text.splitlines(keepends=True)
    b_lines = vb.body_text.splitlines(keepends=True)

    diff = list(difflib.unified_diff(a_lines, b_lines, lineterm=""))

    additions = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
    deletions = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))

    changes = []
    for line in diff:
        if line.startswith("+") and not line.startswith("+++"):
            changes.append({"type": "add", "content": line[1:].rstrip()})
        elif line.startswith("-") and not line.startswith("---"):
            changes.append({"type": "delete", "content": line[1:].rstrip()})

    return {
        "version_a_id": version_a_id,
        "version_b_id": version_b_id,
        "additions": additions,
        "deletions": deletions,
        "changes": changes[:200],
    }


async def ai_rewrite(
    session: AsyncSession,
    draft_id: str,
    project_id: str,
    selected_text: str,
    instruction: str,
    mode: str = "rewrite",
    tone: str = "",
) -> DraftVersion:
    """AI rewrite of selected text."""
    provider = get_llm_provider()

    if provider.get_provider_name() == "mock":
        if mode == "expand":
            new_text = MOCK_EXPAND.format(text=selected_text)
        elif mode == "compress":
            new_text = MOCK_COMPRESS.format(text_short=selected_text[: len(selected_text) // 2])
        elif mode == "tone":
            new_text = MOCK_TONE.format(tone=tone or "更生动", text=selected_text)
        else:
            new_text = MOCK_REWRITE.format(text=selected_text)

        async with track_llm_call(
            provider="mock",
            model="mock-novel-model",
            task_type=f"draft_{mode}",
        ) as ctx:
            ctx.input_tokens = 200
            ctx.output_tokens = 300
            ctx.status = "success"
        llm_call_id = ctx.log_id
    else:
        new_text = selected_text
        llm_call_id = ""

    # Get current draft to replace selected text
    draft = await session.get(ChapterDraft, draft_id)
    if not draft:
        raise ValueError("Draft not found")

    if selected_text in draft.body_text:
        new_body = draft.body_text.replace(selected_text, new_text, 1)
    else:
        new_body = draft.body_text + "\n\n" + new_text

    return await save_version(
        session,
        draft_id,
        project_id,
        new_body,
        "ai_rewrite",
        source=f"{mode}: {instruction}",
        model="mock-novel-model",
        parent_version_id=None,
        llm_call_id=llm_call_id,
    )
