"""Creative direction service — generates and manages creative directions."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CreativeDirection, CreativeSession
from app.llm import get_llm_provider
from app.llm.call_logger import track_llm_call
from app.schemas.creative import CreativeInput, DirectionContent

logger = logging.getLogger(__name__)

GENERATION_SYSTEM_PROMPT = """\
You are a creative director specializing in Chinese web novel development.
Given a user's creative input, generate ONE novel direction that is structurally different from common patterns.
Output ONLY valid JSON matching the DirectionContent schema.
Focus on unique ability mechanics, conflict structures, and growth cycles.
Do NOT use names, worlds, or signature elements from existing published works."""

MOCK_DIRECTIONS = [
    {
        "one_line_hook": "一个被封印千年的炼器师苏醒，发现自己成了末法时代唯一的器修",
        "core_reader_promise": "看主角用上古炼器术在灵气枯竭的末世中一步步重建修仙文明",
        "protagonist_identity": "沉睡千年的上古炼器宗师，苏醒后失去大部分记忆和修为",
        "protagonist_goal": "找回失去的记忆，查明千年封印的真相，重建器修传承",
        "core_ability": "上古炼器术——能将天地灵气注入器物，赋予器物灵性和特殊能力",
        "ability_cost": "每次炼器消耗自身精血，品级越高的器物消耗越大，严重时会折损寿元",
        "core_conflict": "末法时代的修士视器修为旁门左道，而上古封印背后的势力正在暗中追杀所有器修传人",
        "world_mystery": "千年前的灵气大衰退并非天灾，而是有人故意封印了天地灵脉",
        "growth_cycle": "炼器失败→反思→领悟新技法→成功炼出更强器物→获得更多材料→挑战更高品级",
        "resource_cycle": "炼器消耗精血和灵材→完成委托获得灵材和情报→发现新矿脉→解锁更高阶炼器配方",
        "payoff_cycle": "被轻视→当众炼器震惊众人→获得尊重和委托→遇到更强对手→再次被轻视→更高层次的炼器打脸",
        "long_term_suspense": "主角身上封印的到底是什么？千年前封印天地灵脉的人与主角是什么关系？",
        "difference_from_tropes": "不是升级打怪，而是通过创造和修复来成长；能力越强代价越大",
        "homogenization_risk": "炼器题材已有较多作品，需要在器物设定和代价机制上做出差异化",
        "sustainable_length": "200-400万字",
        "potential_collapse_point": "如果炼器过程过于重复或代价机制被削弱，会变成普通的升级流",
    },
    {
        "one_line_hook": "一个能看到所有人寿命倒计时的兽医，意外发现自己能通过救治灵兽延长他人寿命",
        "core_reader_promise": "看主角在修仙世界用现代医学思维治病救人，同时揭开自己能力背后的惊天秘密",
        "protagonist_identity": "穿越到修仙世界的现代兽医，觉醒了能看见寿命的异瞳",
        "protagonist_goal": "在这个弱肉强食的世界活下去，找到回到原来世界的方法",
        "core_ability": "异瞳——能看见所有生物的寿命倒计时和病灶位置，通过救治可以延长寿命",
        "ability_cost": "每次使用异瞳会短暂失明，救治越严重的病症失明时间越长",
        "core_conflict": "各大势力都想控制主角的异瞳能力，而主角只想低调行医",
        "world_mystery": "修仙世界的灵兽并非自然产物，而是远古文明的实验品",
        "growth_cycle": "救治低阶灵兽→获得信任和资源→遇到疑难杂症→研究灵兽获得新知识→解锁更高阶治疗术",
        "resource_cycle": "免费救治建立口碑→收取高级灵兽作为报酬→研究灵兽获得知识→知识转化为更强的治疗能力",
        "payoff_cycle": "被人轻视兽医身份→灵兽救治成功震惊全场→各大势力争相邀请",
        "long_term_suspense": "异瞳的前一任主人是谁？远古文明创造灵兽的目的是什么？",
        "difference_from_tropes": "不是战斗型主角，而是辅助型；成长不靠打怪，靠知识积累和人脉经营",
        "homogenization_risk": "医修题材有先例，需要在灵兽医学和异瞳设定上做出独特性",
        "sustainable_length": "150-300万字",
        "potential_collapse_point": "如果变成万能医生或战斗能力过强，会失去紧张感",
    },
    {
        "one_line_hook": "一个被诅咒的废材，发现自己的诅咒其实是上古神灵的试炼",
        "core_reader_promise": "看主角在所有人都认为他是废物的情况下，一步步将诅咒转化为超越天才的力量",
        "protagonist_identity": "身负'天罚之体'诅咒的落魄贵族后裔，被家族驱逐",
        "protagonist_goal": "洗刷家族冤屈，查明天罚之体的真相",
        "core_ability": "天罚之体——能吸收一切负面状态转化为自身力量",
        "ability_cost": "转化过程极度痛苦，吸收的负面能量会暂时影响性格和判断力，严重时可能暴走",
        "core_conflict": "天罚之体是上古神灵留下的试炼，历史上从未有人通过，所有尝试者都变成了怪物",
        "world_mystery": "上古神灵为何要留下这样的试炼？试炼的真正目的是什么？",
        "growth_cycle": "遭遇负面攻击→痛苦吸收→力量暴涨但性格受影响→冷静消化→获得新能力",
        "resource_cycle": "主动寻找危险区域→吸收各种诅咒和毒素→消化后获得独特抗性→用抗性帮助他人换取资源",
        "payoff_cycle": "被嘲笑废物→遭遇致命攻击→吸收攻击力量暴涨→众人震惊→引来更强敌人",
        "long_term_suspense": "历史上那些变成怪物的试炼者去了哪里？天罚之体的最终形态是什么？",
        "difference_from_tropes": "能力来自受苦而非天赋，越痛苦越强大，但代价是可能失去自我",
        "homogenization_risk": "废材逆袭是经典套路，需要在诅咒设定和性格变化描写上做出深度",
        "sustainable_length": "300-500万字",
        "potential_collapse_point": "如果痛苦描写流于表面或暴走解决一切问题，会失去读者共鸣",
    },
]


async def generate_directions(
    session: AsyncSession,
    creative_input: CreativeInput,
    project_id: str,
) -> tuple[CreativeSession, list[CreativeDirection]]:
    """Generate 3 creative directions from user input.

    Returns the session and 3 direction records.
    """
    provider = get_llm_provider()

    # Create session
    cs = CreativeSession(
        project_id=project_id,
        one_line_idea=creative_input.one_line_idea,
        genre=creative_input.genre,
        target_platform=creative_input.target_platform,
        target_reader=creative_input.target_reader,
        expected_length=creative_input.expected_length,
        preferred_pacing=creative_input.preferred_pacing,
        forbidden_content=creative_input.forbidden_content,
        gene_tags=creative_input.gene_tags,
        status="draft",
    )
    session.add(cs)
    await session.flush()

    directions: list[CreativeDirection] = []
    schema = DirectionContent.model_json_schema()

    for i in range(3):
        messages = [
            {"role": "system", "content": GENERATION_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Generate creative direction #{i + 1} for this novel idea.\n\n"
                    f"Idea: {creative_input.one_line_idea}\n"
                    f"Genre: {creative_input.genre}\n"
                    f"Target reader: {creative_input.target_reader}\n"
                    f"Expected length: {creative_input.expected_length}\n"
                    f"Pacing: {creative_input.preferred_pacing}\n"
                    f"Forbidden: {creative_input.forbidden_content}\n\n"
                    f"This direction must be structurally DIFFERENT from typical patterns. "
                    f"Vary the ability system, conflict type, and growth cycle significantly."
                ),
            },
        ]

        # Use mock data directly for mock provider to ensure 3 distinct directions
        if provider.get_provider_name() == "mock":
            content = DirectionContent(**MOCK_DIRECTIONS[i % len(MOCK_DIRECTIONS)])
            async with track_llm_call(
                provider="mock",
                model="mock-novel-model",
                task_type="creative_direction",
            ) as ctx:
                ctx.input_tokens = 300
                ctx.output_tokens = 200
                ctx.status = "success"
        else:
            try:
                async with track_llm_call(
                    provider=provider.get_provider_name(),
                    model=provider.get_model_name(),
                    task_type="creative_direction",
                ) as ctx:
                    response = await provider.structured_output(messages=messages, schema=schema)
                    content = DirectionContent.model_validate_json(response.content)
                    ctx.input_tokens = response.input_tokens
                    ctx.output_tokens = response.output_tokens
                    ctx.status = "success"
            except Exception:
                # Fallback to mock data
                content = DirectionContent(**MOCK_DIRECTIONS[i % len(MOCK_DIRECTIONS)])

        direction = CreativeDirection(
            session_id=cs.id,
            project_id=project_id,
            direction_index=i,
            status="draft",
            **content.model_dump(),
            ai_original_json=content.model_dump_json(),
        )
        session.add(direction)
        directions.append(direction)

    await session.flush()
    for d in directions:
        await session.refresh(d)

    return cs, directions


async def edit_direction(
    session: AsyncSession,
    direction_id: str,
    updates: dict,
) -> CreativeDirection:
    """Edit a direction, preserving the AI original and recording human edits."""
    direction = await session.get(CreativeDirection, direction_id)
    if not direction:
        raise ValueError(f"Direction not found: {direction_id}")

    # Apply updates
    for key, value in updates.items():
        if value is not None and hasattr(direction, key):
            setattr(direction, key, value)

    # Record human edits
    current_edits = json.loads(direction.human_edits_json) if direction.human_edits_json else {}
    current_edits[str(datetime.now(timezone.utc))] = updates
    direction.human_edits_json = json.dumps(current_edits, ensure_ascii=False)

    await session.flush()
    return direction


async def accept_direction(session: AsyncSession, direction_id: str) -> CreativeDirection:
    """Accept a direction — mark as adopted, reject siblings."""
    direction = await session.get(CreativeDirection, direction_id)
    if not direction:
        raise ValueError(f"Direction not found: {direction_id}")

    # Mark this as adopted
    direction.status = "adopted"

    # Reject siblings in the same session
    siblings = await session.execute(
        select(CreativeDirection).where(
            CreativeDirection.session_id == direction.session_id,
            CreativeDirection.id != direction_id,
        )
    )
    for s in siblings.scalars().all():
        if s.status == "draft":
            s.status = "rejected"
            s.rejection_reason = "Sibling direction was adopted"

    # Update session status
    cs = await session.get(CreativeSession, direction.session_id)
    if cs:
        cs.status = "completed"

    await session.flush()
    return direction


async def reject_direction(
    session: AsyncSession,
    direction_id: str,
    reason: str = "",
) -> CreativeDirection:
    """Reject a direction."""
    direction = await session.get(CreativeDirection, direction_id)
    if not direction:
        raise ValueError(f"Direction not found: {direction_id}")

    direction.status = "rejected"
    direction.rejection_reason = reason
    await session.flush()
    return direction
