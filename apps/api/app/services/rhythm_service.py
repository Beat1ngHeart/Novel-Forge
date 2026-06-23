"""Rhythm service — generates and manages chapter rhythm plans."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ChapterRhythmPlan, VolumeOutline
from app.llm import get_llm_provider
from app.llm.call_logger import track_llm_call
from app.schemas.rhythm import ChapterRhythmContent

logger = logging.getLogger(__name__)

MOCK_CHAPTERS = [
    {
        "temp_title": "废物苏醒",
        "chapter_function": "开场铺垫",
        "core_event": "主角在废弃矿洞中苏醒，发现自己失去所有记忆和修为，被路过散修发现并嘲笑为废物",
        "protagonist_goal": "搞清楚自己是谁、在哪里",
        "main_obstacle": "失去记忆、毫无修为、身无分文",
        "conflict_type": "人vs自我",
        "information_gain": "发现怀中有一块破碎的玉佩，上面隐约有炼器纹路",
        "character_change": "从迷茫到产生求生本能",
        "payoff_or_emotion": "悬念——读者好奇主角身份",
        "foreshadow_action": "埋设：破碎玉佩的炼器纹路",
        "chapter_hook": "玉佩突然发出微弱光芒，主角眼前闪过一个模糊画面",
        "volume_goal_connection": "建立主角起点，引入核心道具",
        "estimated_words": 3000,
        "risk_notes": "注意不要信息倾倒，保持悬念",
    },
    {
        "temp_title": "末法小镇",
        "chapter_function": "世界观建立",
        "core_event": "主角进入最近的修仙小镇，发现这是一个灵脉枯竭的末法时代，修士稀少且地位低下",
        "protagonist_goal": "找到食物和落脚点",
        "main_obstacle": "被人当作乞丐驱赶，没有灵石",
        "conflict_type": "人vs社会",
        "information_gain": "了解末法时代的背景，知道灵脉枯竭已有千年",
        "character_change": "从单纯求生到开始观察这个世界",
        "payoff_or_emotion": "压抑——弱者被欺凌",
        "foreshadow_action": "无",
        "chapter_hook": "一个神秘老者盯着主角的玉佩，眼神闪烁",
        "volume_goal_connection": "建立世界观，为器修被歧视埋伏笔",
        "estimated_words": 3000,
        "risk_notes": "世界观信息通过对话自然传递，避免设定堆砌",
    },
    {
        "temp_title": "器修废物",
        "chapter_function": "冲突升级",
        "core_event": "主角试图通过炼器换取灵石，却被当地修士嘲笑器修是废物之道，还被地痞勒索",
        "protagonist_goal": "证明炼器的价值",
        "main_obstacle": "众人偏见、地痞威胁、缺乏材料",
        "conflict_type": "人vs社会",
        "information_gain": "器修在末法时代被视为旁门左道，但灵器需求真实存在",
        "character_change": "从忍受到产生逆反心理",
        "payoff_or_emotion": "压抑加深——读者期待逆袭",
        "foreshadow_action": "无",
        "chapter_hook": "主角在垃圾堆中发现一块别人不要的废铁，眼中闪过精光",
        "volume_goal_connection": "建立核心矛盾：器修被歧视",
        "estimated_words": 3000,
        "risk_notes": "压抑要适度，给读者希望感",
    },
    {
        "temp_title": "废铁炼器",
        "chapter_function": "伏笔埋设",
        "core_event": "主角在废弃仓库中用废铁尝试炼器，意外发现自己拥有某种直觉性的炼器天赋，但代价是消耗精血",
        "protagonist_goal": "炼出一件能卖钱的灵器",
        "main_obstacle": "材料极差、缺乏工具、炼器消耗精血导致虚弱",
        "conflict_type": "人vs自我",
        "information_gain": "发现炼器代价机制——消耗精血，品级越高代价越大",
        "character_change": "从被动求生到主动尝试",
        "payoff_or_emotion": "希望——第一次看到成功的可能",
        "foreshadow_action": "埋设：炼器时玉佩产生微弱共鸣",
        "chapter_hook": "灵器炼成的瞬间，方圆百米的灵气产生微弱波动",
        "volume_goal_connection": "建立核心能力体系和代价机制",
        "estimated_words": 3500,
        "risk_notes": "炼器过程要有细节感，避免一笔带过",
    },
    {
        "temp_title": "第一次打脸",
        "chapter_function": "高潮",
        "core_event": "主角带着炼成的灵器去交易，被地痞再次阻拦。在众人面前展示灵器，震惊全场，地痞仓皇逃走",
        "protagonist_goal": "卖出灵器获得灵石",
        "main_obstacle": "地痞当众刁难",
        "conflict_type": "人vs人",
        "information_gain": "灵器品质远超当地修士预期",
        "character_change": "从被动到第一次掌握主动权",
        "payoff_or_emotion": "爽点：废物逆袭、当众打脸",
        "foreshadow_action": "兑现：废铁炼器的成果",
        "chapter_hook": "青云宗一位外门弟子在人群中默默注视",
        "volume_goal_connection": "第一次爽点高潮，废物逆袭展示",
        "estimated_words": 3500,
        "risk_notes": "打脸要有力但不过度，保持后续可信度",
    },
    {
        "temp_title": "青云宗邀请",
        "chapter_function": "过渡",
        "core_event": "青云宗外门弟子邀请主角前往青云宗，透露宗门正在寻找有特殊天赋的弟子",
        "protagonist_goal": "了解更多关于修仙界的信息",
        "main_obstacle": "不确定邀请是否真诚",
        "conflict_type": "人vs人",
        "information_gain": "青云宗是末法时代少数仍存的大宗门，有完整的修炼体系",
        "character_change": "从独行到考虑加入组织",
        "payoff_or_emotion": "希望——更大的舞台",
        "foreshadow_action": "埋设：外门弟子似乎知道更多内情",
        "chapter_hook": "上山途中，主角感应到一股熟悉又陌生的气息",
        "volume_goal_connection": "主角进入主流修炼体系",
        "estimated_words": 3000,
        "risk_notes": "过渡章也要有新信息，不能纯粹移动",
    },
    {
        "temp_title": "入门考验",
        "chapter_function": "冲突升级",
        "core_event": "青云宗入门考验，主角面对其他新弟子的挑战，对方明显有敌意，似乎受人指使",
        "protagonist_goal": "通过考验进入青云宗",
        "main_obstacle": "对手实力明显高于主角，且有针对性的攻击",
        "conflict_type": "人vs人",
        "information_gain": "有人在暗中针对主角，可能是赵无极的眼线",
        "character_change": "从被动防守到主动应对",
        "payoff_or_emotion": "紧张——以弱敌强",
        "foreshadow_action": "埋设：对手提到'上面的人交代过'",
        "chapter_hook": "考验结果揭晓，主角的名字出现在一个意料之外的名单上",
        "volume_goal_connection": "建立与反派的早期接触",
        "estimated_words": 3500,
        "risk_notes": "战斗描写要有策略性，不能只靠硬拼",
    },
    {
        "temp_title": "外门弟子",
        "chapter_function": "过渡",
        "core_event": "主角正式成为青云宗外门弟子，分配到一间简陋的住所，开始了解宗门的等级体系",
        "protagonist_goal": "适应新环境",
        "main_obstacle": "外门弟子资源极少，竞争激烈",
        "conflict_type": "人vs社会",
        "information_gain": "宗门等级体系：外门→内门→核心→长老，器修在外门也是被边缘化的",
        "character_change": "从目标模糊到有了清晰的短期目标",
        "payoff_or_emotion": "平静——新的开始",
        "foreshadow_action": "无",
        "chapter_hook": "在住所角落发现一本残破的炼器手记",
        "volume_goal_connection": "建立宗门日常，为后续冲突铺垫",
        "estimated_words": 3000,
        "risk_notes": "保持节奏，不要陷入日常描写",
    },
    {
        "temp_title": "残破手记",
        "chapter_function": "伏笔埋设",
        "core_event": "主角研读残破手记，发现这是一位上古器修的笔记，其中提到一种被遗忘的炼器手法",
        "protagonist_goal": "学会手记中的炼器手法",
        "main_obstacle": "手记残缺不全，需要自行推断",
        "conflict_type": "人vs自我",
        "information_gain": "发现上古器修的炼器理念与现代完全不同，更注重与材料的共鸣",
        "character_change": "从模仿到开始形成自己的炼器理念",
        "payoff_or_emotion": "发现感——新的可能性",
        "foreshadow_action": "埋设：手记最后一页提到'灵脉之心'",
        "chapter_hook": "主角尝试新手法时，玉佩再次发光，似乎在回应",
        "volume_goal_connection": "建立主角独特的成长路径",
        "estimated_words": 3000,
        "risk_notes": "手记内容要有具体性，不能太抽象",
    },
    {
        "temp_title": "新的突破",
        "chapter_function": "高潮",
        "core_event": "主角运用新手法成功炼制出一柄品质远超预期的灵剑，引起宗门注意，但也引来嫉妒",
        "protagonist_goal": "验证新手法的可行性",
        "main_obstacle": "新手法不稳定，有失败风险",
        "conflict_type": "人vs自我",
        "information_gain": "新手法确实有效，但需要更精纯的材料才能发挥全部潜力",
        "character_change": "从试探到建立信心",
        "payoff_or_emotion": "爽点：再次证明器修的价值",
        "foreshadow_action": "兑现：手记中的炼器手法",
        "chapter_hook": "灵剑出炉时引发小规模灵气波动，被路过的内门弟子注意到",
        "volume_goal_connection": "第二次爽点高潮，巩固器修路线",
        "estimated_words": 3500,
        "risk_notes": "突破要有铺垫，不能突然变强",
    },
]


async def generate_rhythm_plans(
    session: AsyncSession,
    project_id: str,
    volume_id: str,
    chapter_count: int = 10,
) -> list[ChapterRhythmPlan]:
    """Generate chapter rhythm plans for a volume."""
    volume = await session.get(VolumeOutline, volume_id)
    if not volume:
        raise ValueError(f"Volume not found: {volume_id}")
    if volume.project_id != project_id:
        raise ValueError("Volume does not belong to this project")
    if volume.status != "adopted":
        raise ValueError(f"Volume must be adopted (current: {volume.status})")

    provider = get_llm_provider()
    plans: list[ChapterRhythmPlan] = []

    for i in range(chapter_count):
        mock_idx = i % len(MOCK_CHAPTERS)
        mock_data = MOCK_CHAPTERS[mock_idx].copy()
        mock_data["temp_title"] = f"第{i + 1}章 {mock_data['temp_title']}"

        if provider.get_provider_name() == "mock":
            content = ChapterRhythmContent(**mock_data)
            async with track_llm_call(
                provider="mock",
                model="mock-novel-model",
                task_type="rhythm_plan",
            ) as ctx:
                ctx.input_tokens = 300
                ctx.output_tokens = 500
                ctx.status = "success"
        else:
            content = ChapterRhythmContent(**mock_data)

        plan = ChapterRhythmPlan(
            project_id=project_id,
            volume_id=volume_id,
            chapter_index=i,
            status="draft",
            is_current=False,
            **content.model_dump(),
            ai_original_json=content.model_dump_json(),
        )
        session.add(plan)
        plans.append(plan)

    await session.flush()
    for p in plans:
        await session.refresh(p)
    return plans


async def regenerate_single(
    session: AsyncSession,
    project_id: str,
    plan_id: str,
) -> ChapterRhythmPlan:
    """Regenerate a single chapter plan without affecting others."""
    plan = await session.get(ChapterRhythmPlan, plan_id)
    if not plan or plan.project_id != project_id:
        raise ValueError(f"Plan not found: {plan_id}")

    mock_data = MOCK_CHAPTERS[plan.chapter_index % len(MOCK_CHAPTERS)].copy()
    mock_data["temp_title"] = f"第{plan.chapter_index + 1}章 {mock_data['temp_title']}"
    content = ChapterRhythmContent(**mock_data)

    plan.temp_title = content.temp_title
    plan.chapter_function = content.chapter_function
    plan.core_event = content.core_event
    plan.protagonist_goal = content.protagonist_goal
    plan.main_obstacle = content.main_obstacle
    plan.conflict_type = content.conflict_type
    plan.information_gain = content.information_gain
    plan.character_change = content.character_change
    plan.payoff_or_emotion = content.payoff_or_emotion
    plan.foreshadow_action = content.foreshadow_action
    plan.chapter_hook = content.chapter_hook
    plan.volume_goal_connection = content.volume_goal_connection
    plan.estimated_words = content.estimated_words
    plan.risk_notes = content.risk_notes
    plan.ai_original_json = content.model_dump_json()
    plan.status = "draft"
    plan.is_current = False

    await session.flush()
    await session.refresh(plan)
    return plan


async def edit_plan(
    session: AsyncSession,
    plan_id: str,
    updates: dict,
) -> ChapterRhythmPlan:
    """Edit a chapter plan, preserving AI original and recording human edits."""
    plan = await session.get(ChapterRhythmPlan, plan_id)
    if not plan:
        raise ValueError(f"Plan not found: {plan_id}")

    for key, value in updates.items():
        if value is not None and hasattr(plan, key):
            setattr(plan, key, value)

    current_edits = json.loads(plan.human_edits_json) if plan.human_edits_json else {}
    current_edits[str(datetime.now(timezone.utc))] = updates
    plan.human_edits_json = json.dumps(current_edits, ensure_ascii=False)

    await session.flush()
    return plan


async def adopt_plan(session: AsyncSession, plan_id: str) -> ChapterRhythmPlan:
    plan = await session.get(ChapterRhythmPlan, plan_id)
    if not plan:
        raise ValueError(f"Plan not found: {plan_id}")
    plan.status = "adopted"
    plan.is_current = True
    await session.flush()
    return plan


async def insert_chapter(
    session: AsyncSession,
    project_id: str,
    volume_id: str,
    after_index: int,
    temp_title: str = "新章节",
    chapter_function: str = "",
) -> list[ChapterRhythmPlan]:
    """Insert a new chapter after the given index, reindexing subsequent chapters."""
    # Reindex subsequent chapters
    later = await session.execute(
        select(ChapterRhythmPlan)
        .where(
            ChapterRhythmPlan.volume_id == volume_id,
            ChapterRhythmPlan.chapter_index > after_index,
        )
        .order_by(ChapterRhythmPlan.chapter_index.desc())
    )
    for ch in later.scalars().all():
        ch.chapter_index += 1

    new_plan = ChapterRhythmPlan(
        project_id=project_id,
        volume_id=volume_id,
        chapter_index=after_index + 1,
        status="draft",
        temp_title=temp_title,
        chapter_function=chapter_function,
    )
    session.add(new_plan)
    await session.flush()
    await session.refresh(new_plan)

    # Return all plans in order
    all_plans = (
        (
            await session.execute(
                select(ChapterRhythmPlan)
                .where(ChapterRhythmPlan.volume_id == volume_id)
                .order_by(ChapterRhythmPlan.chapter_index)
            )
        )
        .scalars()
        .all()
    )
    return list(all_plans)


async def delete_chapter(
    session: AsyncSession,
    project_id: str,
    plan_id: str,
) -> list[ChapterRhythmPlan]:
    """Delete a chapter plan and reindex remaining."""
    plan = await session.get(ChapterRhythmPlan, plan_id)
    if not plan or plan.project_id != project_id:
        raise ValueError(f"Plan not found: {plan_id}")
    volume_id = plan.volume_id
    await session.delete(plan)

    # Reindex
    remaining = (
        (
            await session.execute(
                select(ChapterRhythmPlan)
                .where(ChapterRhythmPlan.volume_id == volume_id)
                .order_by(ChapterRhythmPlan.chapter_index)
            )
        )
        .scalars()
        .all()
    )
    for i, p in enumerate(remaining):
        p.chapter_index = i

    await session.flush()
    return remaining


async def reorder_plans(
    session: AsyncSession,
    project_id: str,
    plan_ids: list[str],
) -> list[ChapterRhythmPlan]:
    """Reorder chapter plans by setting chapter_index."""
    for new_idx, pid in enumerate(plan_ids):
        plan = await session.get(ChapterRhythmPlan, pid)
        if not plan or plan.project_id != project_id:
            raise ValueError(f"Plan not found: {pid}")
        plan.chapter_index = new_idx

    await session.flush()
    # Get volume_id from first plan
    first = await session.get(ChapterRhythmPlan, plan_ids[0])
    result = await session.execute(
        select(ChapterRhythmPlan)
        .where(ChapterRhythmPlan.volume_id == first.volume_id)
        .order_by(ChapterRhythmPlan.chapter_index)
    )
    return list(result.scalars().all())
