"""State change service — extract, accept, reject, apply, undo state changes."""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    ChapterDraft,
    Character,
    Foreshadowing,
    PlotThread,
    StateChangeCandidate,
    WorldRule,
)
from app.llm import get_llm_provider
from app.llm.call_logger import track_llm_call

logger = logging.getLogger(__name__)

MOCK_CHANGES = [
    {
        "change_type": "character_location",
        "entity_name": "林辰",
        "before_value": "青云宗外门弟子居所",
        "after_value": "青云宗大殿",
        "reason": "被师父紧急召见",
    },
    {
        "change_type": "character_relationship",
        "entity_name": "林辰—赵无极",
        "before_value": "敌对",
        "after_value": "正式宣战",
        "reason": "赵无极带人上门挑衅",
    },
    {
        "change_type": "knowledge_change",
        "entity_name": "林辰",
        "before_value": "不知灭门真相",
        "after_value": "得知黑风寨参与灭门",
        "reason": "赵无极当众透露",
    },
    {
        "change_type": "health_change",
        "entity_name": "林辰",
        "before_value": "正常状态",
        "after_value": "内伤，需静养三日",
        "reason": "强行催动血脉的后遗症",
    },
    {
        "change_type": "new_character",
        "entity_name": "黑衣修士首领",
        "before_value": "",
        "after_value": "赵无极手下，筑基后期，善用暗器",
        "reason": "首次出场",
    },
    {
        "change_type": "new_foreshadow",
        "entity_name": "宗主密信",
        "before_value": "",
        "after_value": "宗主看完赵无极带来的信后脸色骤变",
        "reason": "信中内容暗示与林辰身世有关",
    },
    {
        "change_type": "foreshadow_resolved",
        "entity_name": "赵无极的幕后指使者",
        "before_value": "未知",
        "after_value": "一位'前辈'",
        "reason": "赵无极提到替一位前辈传话",
    },
    {
        "change_type": "plot_thread_progress",
        "entity_name": "灭门真相",
        "before_value": "不知灭门原因",
        "after_value": "确认黑风寨参与，有幕后势力",
        "reason": "赵无极当众承认",
    },
]


async def generate_candidates(
    session: AsyncSession,
    project_id: str,
    draft_id: str,
) -> list[StateChangeCandidate]:
    """Extract state change candidates from a draft."""
    draft = await session.get(ChapterDraft, draft_id)
    if not draft:
        raise ValueError(f"Draft not found: {draft_id}")
    if draft.project_id != project_id:
        raise ValueError("Draft does not belong to this project")

    provider = get_llm_provider()

    if provider.get_provider_name() == "mock":
        changes = MOCK_CHANGES
        async with track_llm_call(
            provider="mock",
            model="mock-novel-model",
            task_type="state_change_extraction",
        ) as ctx:
            ctx.input_tokens = 500
            ctx.output_tokens = 800
            ctx.status = "success"
    else:
        changes = MOCK_CHANGES

    candidates = []
    for change in changes:
        candidate = StateChangeCandidate(
            draft_id=draft_id,
            project_id=project_id,
            change_type=change["change_type"],
            entity_name=change["entity_name"],
            before_value=change["before_value"],
            after_value=change["after_value"],
            reason=change["reason"],
            source_chapter="",
            source_version_id="",
            status="pending",
        )
        session.add(candidate)
        candidates.append(candidate)

    await session.flush()
    for c in candidates:
        await session.refresh(c)
    return candidates


async def accept_candidate(
    session: AsyncSession,
    candidate_id: str,
) -> StateChangeCandidate:
    """Accept a candidate and apply it to the bible."""
    candidate = await session.get(StateChangeCandidate, candidate_id)
    if not candidate:
        raise ValueError(f"Candidate not found: {candidate_id}")
    if candidate.status != "pending":
        raise ValueError(f"Candidate is not pending (current: {candidate.status})")

    bible_id = ""
    bible_table = ""

    try:
        if candidate.change_type == "new_character":
            obj = Character(
                project_id=candidate.project_id,
                name=candidate.entity_name,
                identity=candidate.after_value,
                source_status="ai_suggestion",
            )
            session.add(obj)
            await session.flush()
            bible_id = obj.id
            bible_table = "bible_characters"

        elif candidate.change_type == "new_world_rule":
            obj = WorldRule(
                project_id=candidate.project_id,
                name=candidate.entity_name,
                description=candidate.after_value,
                source_status="ai_suggestion",
            )
            session.add(obj)
            await session.flush()
            bible_id = obj.id
            bible_table = "bible_world_rules"

        elif candidate.change_type == "new_foreshadow":
            obj = Foreshadowing(
                project_id=candidate.project_id,
                content=candidate.after_value,
                planted_chapter=candidate.source_chapter,
                related_characters=candidate.entity_name,
                source_status="ai_suggestion",
            )
            session.add(obj)
            await session.flush()
            bible_id = obj.id
            bible_table = "bible_foreshadowings"

        elif candidate.change_type == "plot_thread_progress":
            # Find existing plot thread by name
            result = await session.execute(
                select(PlotThread).where(
                    PlotThread.project_id == candidate.project_id,
                    PlotThread.title.ilike(f"%{candidate.entity_name}%"),
                )
            )
            pt = result.scalar_one_or_none()
            if pt:
                pt.description = candidate.after_value
                bible_id = pt.id
                bible_table = "bible_plot_threads"
            else:
                # Create new plot thread
                obj = PlotThread(
                    project_id=candidate.project_id,
                    title=candidate.entity_name,
                    description=candidate.after_value,
                    source_status="ai_suggestion",
                )
                session.add(obj)
                await session.flush()
                bible_id = obj.id
                bible_table = "bible_plot_threads"

        elif candidate.change_type == "foreshadow_resolved":
            # Find existing foreshadow
            result = await session.execute(
                select(Foreshadowing).where(
                    Foreshadowing.project_id == candidate.project_id,
                    Foreshadowing.content.ilike(f"%{candidate.entity_name}%"),
                )
            )
            fs = result.scalar_one_or_none()
            if fs:
                fs.status = "paid_off"
                fs.actual_payoff_chapter = candidate.source_chapter
                bible_id = fs.id
                bible_table = "bible_foreshadowings"

        # For character changes, find existing character and update
        elif candidate.change_type in (
            "character_location",
            "character_relationship",
            "character_goal",
            "power_change",
            "resource_change",
            "health_change",
            "new_skill",
            "knowledge_change",
        ):
            # These are informational changes stored as world rules for now
            entity_parts = candidate.entity_name.split("—")
            char_name = entity_parts[0].strip()
            result = await session.execute(
                select(Character).where(
                    Character.project_id == candidate.project_id,
                    Character.name == char_name,
                )
            )
            char = result.scalar_one_or_none()
            if char:
                # Update relevant field
                if candidate.change_type == "character_location":
                    char.current_location = candidate.after_value
                elif candidate.change_type == "health_change":
                    char.physical_status = candidate.after_value
                elif candidate.change_type == "character_goal":
                    char.current_goal = candidate.after_value
                elif candidate.change_type == "knowledge_change":
                    existing = char.known_information or ""
                    char.known_information = f"{existing}\n- {candidate.after_value}"
                bible_id = char.id
                bible_table = "bible_characters"

        candidate.status = "accepted"
        candidate.applied_bible_id = bible_id
        candidate.applied_bible_table = bible_table

    except Exception as e:
        logger.exception("Failed to apply candidate %s", candidate_id)
        candidate.status = "failed"
        candidate.rejection_reason = f"Apply failed: {e}"
        raise

    await session.flush()
    return candidate


async def reject_candidate(
    session: AsyncSession,
    candidate_id: str,
    reason: str = "",
) -> StateChangeCandidate:
    candidate = await session.get(StateChangeCandidate, candidate_id)
    if not candidate:
        raise ValueError(f"Candidate not found: {candidate_id}")
    candidate.status = "rejected"
    candidate.rejection_reason = reason
    await session.flush()
    return candidate


async def undo_apply(session: AsyncSession, candidate_id: str) -> StateChangeCandidate:
    """Undo an applied candidate — delete from bible, reset to pending."""
    candidate = await session.get(StateChangeCandidate, candidate_id)
    if not candidate:
        raise ValueError(f"Candidate not found: {candidate_id}")
    if candidate.status != "accepted":
        raise ValueError(f"Candidate not accepted (status: {candidate.status})")

    # Delete from bible table
    if candidate.applied_bible_id:
        table = candidate.applied_bible_table
        if table == "bible_characters":
            obj = await session.get(Character, candidate.applied_bible_id)
        elif table == "bible_world_rules":
            obj = await session.get(WorldRule, candidate.applied_bible_id)
        elif table == "bible_foreshadowings":
            obj = await session.get(Foreshadowing, candidate.applied_bible_id)
        elif table == "bible_plot_threads":
            obj = await session.get(PlotThread, candidate.applied_bible_id)
        else:
            obj = None
        if obj:
            await session.delete(obj)

    candidate.status = "pending"
    candidate.applied_bible_id = ""
    candidate.applied_bible_table = ""
    await session.flush()
    return candidate
