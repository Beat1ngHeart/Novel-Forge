"""Chapter plan service — generates 3 distinct chapter plan variants."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ChapterPlan, ChapterRhythmPlan
from app.llm import get_llm_provider
from app.llm.call_logger import track_llm_call
from app.schemas.chapter_plan import ChapterPlanContent

logger = logging.getLogger(__name__)

MOCK_PLANS = [
    # Plan A: Focus on action and confrontation
    ChapterPlanContent(
        chapter_goal="通过正面冲突展示主角炼器实力的提升，同时埋下敌人背后势力的线索",
        characters="林辰（主角）、赵无极（反派）、苏晴（盟友）、围观修士若干",
        scenes="1. 炼器坊遇赵无极挑衅\n2. 赵质疑器修价值\n3. 林提出炼器比试\n4. 比试过程\n5. 林意外获胜，赵露出破绽",
        obstacle="赵无极修为高于林辰，且暗中携带了克制器修的特殊法器",
        turning_point="林辰发现赵无极的法器有千年前的炼器纹路，意识到对方背后有上古势力",
        information_gain="赵无极背后的势力与千年前的灵脉封印有关",
        emotion_curve="紧张→愤怒→坚定→震惊（发现线索）",
        payoff="当众击败挑衅者，展示器修实力",
        foreshadow_action="赵无极法器上的上古炼器纹路",
        foreshadow_resolved="无",
        relationship_changes="林辰与赵无极：敌对升级\n林辰与苏晴：并肩作战，信任加深",
        end_state="林辰获胜但受伤，赵无极逃走，获得关键线索",
        chapter_hook="赵无极临走前低声说：'你以为打败我就安全了？那个人已经注意到你了'",
        repetition_risk="与之前的炼器打脸模式相似，需要在细节上有差异化",
        logic_issues="赵无极为何在公开场合暴露自己，需要合理动机",
    ),
    # Plan B: Focus on mystery and investigation
    ChapterPlanContent(
        chapter_goal="通过调查线索揭示世界观新层面，推动悬疑主线",
        characters="林辰（主角）、苏晴（协助调查）、神秘老者（线索提供者）",
        scenes="1. 藏书阁异常古籍\n2. 被抹去的历史\n3. 苏晴解读暗语\n4. 潜入禁地\n5. 千年前阵法残留",
        obstacle="古籍被人故意损毁，关键内容缺失；禁地有守卫巡逻",
        turning_point="阵法残留与林辰的炼器手法产生共鸣，触发一段记忆碎片",
        information_gain="千年前有一群器修参与了灵脉封印，但他们的功绩被故意抹去",
        emotion_curve="好奇→紧张（潜入）→震惊（发现真相）→愤怒（历史被抹去）",
        payoff="解锁世界观新层面，读者获得信息快感",
        foreshadow_action="禁地阵法与林辰炼器术的共鸣",
        foreshadow_resolved="古籍中提到的'被遗忘的器修'与林辰的前世关联",
        relationship_changes="林辰与苏晴：从战友到共同探索真相的伙伴",
        end_state="获得关键历史线索，但也被人发现潜入禁地",
        chapter_hook="回程路上，林辰发现有人在暗中跟踪他们",
        repetition_risk="调查类章节容易节奏过慢，需要保持紧张感",
        logic_issues="禁地守卫的巡逻路线需要合理设计，不能太容易也不能无法进入",
    ),
    # Plan C: Focus on character growth and emotional depth
    ChapterPlanContent(
        chapter_goal="通过内心考验推动主角性格成长，同时展现能力代价",
        characters="林辰（主角）、器灵残影（内心试炼对手）、师父（精神指引）",
        scenes="1. 进入器灵空间\n2. 遇上古器修残影\n3. 心性考验\n4. 面对恐惧欲望\n5. 获认可和传承",
        obstacle="心性考验要求林辰放弃执念，但他放不下灭门仇恨",
        turning_point="林辰意识到执着于仇恨会阻碍炼器之道，选择放下但保留责任",
        information_gain="上古器修的炼器理念：与器物共鸣而非强行驱使",
        emotion_curve="平静→紧张→挣扎→释然→获得力量",
        payoff="内心成长 + 获得新炼器理念",
        foreshadow_action="残影提到'灵脉之心正在苏醒'",
        foreshadow_resolved="无",
        relationship_changes="林辰与自己：放下仇恨执念\n林辰与师父：更深的理解",
        end_state="心性提升，获得新炼器理念，但也意识到更大的危机",
        chapter_hook="残影消失前说：'下一次苏醒的，不只是灵脉'",
        repetition_risk="内心戏章节容易沉闷，需要通过视觉化描写保持吸引力",
        logic_issues="器灵空间的设定需要有合理边界，不能成为万能工具",
    ),
]


async def generate_plans(
    session: AsyncSession,
    project_id: str,
    rhythm_id: str,
) -> list[ChapterPlan]:
    """Generate 3 distinct chapter plan variants from a rhythm record."""
    rhythm = await session.get(ChapterRhythmPlan, rhythm_id)
    if not rhythm:
        raise ValueError(f"Rhythm plan not found: {rhythm_id}")
    if rhythm.project_id != project_id:
        raise ValueError("Rhythm plan does not belong to this project")

    provider = get_llm_provider()
    plans: list[ChapterPlan] = []

    for i, plan_data in enumerate(MOCK_PLANS):
        if provider.get_provider_name() == "mock":
            content = plan_data
            async with track_llm_call(
                provider="mock",
                model="mock-novel-model",
                task_type="chapter_plan",
            ) as ctx:
                ctx.input_tokens = 400
                ctx.output_tokens = 600
                ctx.status = "success"
        else:
            content = plan_data

        plan = ChapterPlan(
            project_id=project_id,
            rhythm_id=rhythm_id,
            plan_index=i,
            status="draft",
            is_adopted=False,
            **content.model_dump(),
            ai_original_json=content.model_dump_json(),
        )
        session.add(plan)
        plans.append(plan)

    await session.flush()
    for p in plans:
        await session.refresh(p)
    return plans


async def edit_plan(
    session: AsyncSession,
    plan_id: str,
    updates: dict,
    locked_fields: list[str] | None = None,
) -> ChapterPlan:
    """Edit a chapter plan, preserving AI original and recording human edits."""
    plan = await session.get(ChapterPlan, plan_id)
    if not plan:
        raise ValueError(f"Plan not found: {plan_id}")

    # Check locked fields
    current_locked = json.loads(plan.locked_fields_json) if plan.locked_fields_json else []
    for key in updates:
        if key in current_locked:
            raise ValueError(f"Field '{key}' is locked and cannot be edited")

    for key, value in updates.items():
        if value is not None and hasattr(plan, key):
            setattr(plan, key, value)

    if locked_fields is not None:
        plan.locked_fields_json = json.dumps(locked_fields)

    current_edits = json.loads(plan.human_edits_json) if plan.human_edits_json else {}
    current_edits[str(datetime.now(timezone.utc))] = updates
    plan.human_edits_json = json.dumps(current_edits, ensure_ascii=False)

    await session.flush()
    return plan


async def adopt_plan(session: AsyncSession, plan_id: str) -> ChapterPlan:
    """Adopt a plan. Rejects siblings."""
    plan = await session.get(ChapterPlan, plan_id)
    if not plan:
        raise ValueError(f"Plan not found: {plan_id}")

    plan.status = "adopted"
    plan.is_adopted = True

    # Reject siblings
    siblings = await session.execute(
        select(ChapterPlan).where(
            ChapterPlan.rhythm_id == plan.rhythm_id,
            ChapterPlan.id != plan_id,
        )
    )
    for s in siblings.scalars().all():
        if s.status == "draft":
            s.status = "rejected"

    await session.flush()
    return plan


async def reject_plan(session: AsyncSession, plan_id: str) -> ChapterPlan:
    plan = await session.get(ChapterPlan, plan_id)
    if not plan:
        raise ValueError(f"Plan not found: {plan_id}")
    plan.status = "rejected"
    await session.flush()
    return plan


async def regenerate_plan(
    session: AsyncSession,
    project_id: str,
    plan_id: str,
) -> ChapterPlan:
    """Regenerate a single plan variant."""
    plan = await session.get(ChapterPlan, plan_id)
    if not plan or plan.project_id != project_id:
        raise ValueError(f"Plan not found: {plan_id}")

    mock_idx = plan.plan_index % len(MOCK_PLANS)
    content = MOCK_PLANS[mock_idx]

    for key, value in content.model_dump().items():
        if hasattr(plan, key):
            setattr(plan, key, value)

    plan.ai_original_json = content.model_dump_json()
    plan.status = "draft"
    plan.is_adopted = False
    plan.locked_fields_json = "[]"

    await session.flush()
    await session.refresh(plan)
    return plan


async def merge_plans(
    session: AsyncSession,
    project_id: str,
    source_ids: list[str],
    field_sources: dict[str, str],
) -> ChapterPlan:
    """Merge fields from multiple plans into a new one."""
    sources: dict[str, ChapterPlan] = {}
    for sid in source_ids:
        p = await session.get(ChapterPlan, sid)
        if not p or p.project_id != project_id:
            raise ValueError(f"Plan not found: {sid}")
        sources[sid] = p

    fields = [
        "chapter_goal",
        "characters",
        "scenes",
        "obstacle",
        "turning_point",
        "information_gain",
        "emotion_curve",
        "payoff",
        "foreshadow_action",
        "foreshadow_resolved",
        "relationship_changes",
        "end_state",
        "chapter_hook",
        "repetition_risk",
        "logic_issues",
    ]
    merged: dict[str, str] = {}
    for f in fields:
        src_id = field_sources.get(f, source_ids[0])
        src = sources.get(src_id)
        if src:
            merged[f] = getattr(src, f, "")

    new_plan = ChapterPlan(
        project_id=project_id,
        rhythm_id=sources[source_ids[0]].rhythm_id,
        plan_index=99,
        status="draft",
        is_adopted=False,
        **merged,
        ai_original_json=json.dumps(merged, ensure_ascii=False),
    )
    session.add(new_plan)
    await session.flush()
    await session.refresh(new_plan)
    return new_plan
