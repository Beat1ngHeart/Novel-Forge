"""Synopsis service — generates and manages versioned novel synopses."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CreativeDirection, NovelSynopsis
from app.llm import get_llm_provider
from app.llm.call_logger import track_llm_call
from app.schemas.synopsis import SynopsisContent

logger = logging.getLogger(__name__)

MOCK_SYNOPSIS = SynopsisContent(
    one_liner="一个被封印千年的炼器师苏醒，在末法时代重建修仙文明，同时揭开自己身世和灵脉封印的惊天秘密",
    core_selling_point="独特的器修体系 + 创造型成长 + 代价递增机制 + 多层悬疑",
    protagonist_start="沉睡千年后苏醒，失去大部分记忆和修为，被视为废物",
    final_goal="找回全部记忆，解封所有灵脉，查明自己身世的终极真相",
    core_conflict="末法时代的修士打压器修 + 上古封印势力暗中追杀 + 主角自身血脉的秘密",
    story_phases="第一卷：觉醒与适应（第1-50章）\n第二卷：初露锋芒（第51-120章）\n第三卷：灵脉之谜（第121-200章）\n第四卷：上古真相（第201-300章）\n第五卷：终局之战（第301-400章）",
    growth_arc="废物→初显器修天赋→获得认可→遭遇挫折→领悟更强炼器术→揭开真相→成为传说",
    main_antagonist="赵无极（前期直接对手）+ 幕后上古势力首领（终极反派）",
    relationship_changes="林辰与苏晴：陌生→信任→并肩→感情深化\n林辰与赵无极：敌对→了解真相→亦敌亦友\n林辰与师父：师徒→揭秘→理解与和解",
    world_truth="灵脉封印是上古修士为阻止远古种族复苏而设的牺牲之举，林辰的前世正是封印的核心执行者",
    key_foreshadowings="林辰血脉异动→远古血脉觉醒\n赵无极提到'那个人'→幕后势力浮出水面\n灵脉处器鸣声→上古灵器苏醒\n记忆碎片→完整记忆揭示真相",
    reader_promise_plan="前期：炼器打脸（每10章一次）\n中期：真相层层揭开\n后期：史诗对决+感情线高潮",
    ending="林辰成功解封灵脉，击败远古种族首领，与苏晴一起建立新的器修圣地，灵脉复苏，修仙界迎来新纪元",
    risk_warnings="1. 炼器描写重复\n2. 记忆碎片节奏控制\n3. 终极反派出场太晚\n4. 感情线与主线冲突",
)


async def generate_synopsis(
    session: AsyncSession,
    project_id: str,
    direction_id: str,
) -> NovelSynopsis:
    """Generate a new synopsis version from an adopted creative direction."""
    direction = await session.get(CreativeDirection, direction_id)
    if not direction:
        raise ValueError(f"Direction not found: {direction_id}")
    if direction.status != "adopted":
        raise ValueError(f"Direction must be adopted (current: {direction.status})")
    if direction.project_id != project_id:
        raise ValueError("Direction does not belong to this project")

    # Determine next version number
    result = await session.execute(
        select(NovelSynopsis)
        .where(NovelSynopsis.project_id == project_id)
        .order_by(NovelSynopsis.version.desc())
        .limit(1)
    )
    latest = result.scalar_one_or_none()
    next_version = (latest.version + 1) if latest else 1

    # Generate content
    provider = get_llm_provider()
    if provider.get_provider_name() == "mock":
        content = MOCK_SYNOPSIS
        async with track_llm_call(
            provider="mock",
            model="mock-novel-model",
            task_type="synopsis_generation",
        ) as ctx:
            ctx.input_tokens = 500
            ctx.output_tokens = 1000
            ctx.status = "success"
    else:
        # Real LLM call would go here
        content = MOCK_SYNOPSIS

    synopsis = NovelSynopsis(
        project_id=project_id,
        direction_id=direction_id,
        version=next_version,
        is_current=False,
        status="draft",
        **content.model_dump(),
        ai_original_json=content.model_dump_json(),
    )
    session.add(synopsis)
    await session.flush()
    await session.refresh(synopsis)
    return synopsis


async def edit_synopsis(
    session: AsyncSession,
    synopsis_id: str,
    updates: dict,
) -> NovelSynopsis:
    """Edit a synopsis, preserving AI original and recording human edits."""
    synopsis = await session.get(NovelSynopsis, synopsis_id)
    if not synopsis:
        raise ValueError(f"Synopsis not found: {synopsis_id}")

    for key, value in updates.items():
        if value is not None and hasattr(synopsis, key):
            setattr(synopsis, key, value)

    # Record human edits
    current_edits = json.loads(synopsis.human_edits_json) if synopsis.human_edits_json else {}
    current_edits[str(datetime.now(timezone.utc))] = updates
    synopsis.human_edits_json = json.dumps(current_edits, ensure_ascii=False)

    await session.flush()
    return synopsis


async def adopt_synopsis(session: AsyncSession, synopsis_id: str) -> NovelSynopsis:
    """Adopt a synopsis as the current version. Supersedes other versions."""
    synopsis = await session.get(NovelSynopsis, synopsis_id)
    if not synopsis:
        raise ValueError(f"Synopsis not found: {synopsis_id}")

    # Supersede current adopted version
    current = (
        await session.execute(
            select(NovelSynopsis).where(
                NovelSynopsis.project_id == synopsis.project_id,
                NovelSynopsis.is_current.is_(True),
            )
        )
    ).scalar_one_or_none()
    if current:
        current.is_current = False
        current.status = "superseded"

    synopsis.is_current = True
    synopsis.status = "adopted"
    await session.flush()
    return synopsis


async def restore_synopsis(session: AsyncSession, synopsis_id: str) -> NovelSynopsis:
    """Restore a superseded version as current (creates a new version based on it)."""
    old = await session.get(NovelSynopsis, synopsis_id)
    if not old:
        raise ValueError(f"Synopsis not found: {synopsis_id}")

    # Supersede current
    current = (
        await session.execute(
            select(NovelSynopsis).where(
                NovelSynopsis.project_id == old.project_id,
                NovelSynopsis.is_current.is_(True),
            )
        )
    ).scalar_one_or_none()
    if current:
        current.is_current = False
        current.status = "superseded"

    # Make old version current
    old.is_current = True
    old.status = "adopted"
    await session.flush()
    return old
