"""Bible generator service — generates bible candidates from adopted creative direction."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    BibleCandidate,
    Character,
    CreativeDirection,
    Foreshadowing,
    PlotThread,
    WorldRule,
)
from app.llm import get_llm_provider
from app.llm.call_logger import track_llm_call

logger = logging.getLogger(__name__)

MOCK_BIBLE = {
    "world_rules": [
        {
            "name": "灵气等级体系",
            "category": "修炼体系",
            "description": "修炼分八大境界，每境九层。突破需灵气积累和心境感悟，强行突破会走火入魔。",
            "scope": "全大陆通用",
            "exceptions": "特殊体质可跳级，但代价更大",
        },
        {
            "name": "天地灵脉规则",
            "category": "世界规则",
            "description": "灵脉是天地灵气的源头，灵脉枯竭则灵气消散。千年前有人封印了大部分灵脉，导致末法时代来临。",
            "scope": "全球",
            "exceptions": "封印核心区域灵气仍浓",
        },
        {
            "name": "器物灵性规则",
            "category": "能力体系",
            "description": "器物可以注入灵性成为灵器，灵器会认主并随主人成长。灵器品级从凡器到仙器共九阶。",
            "scope": "器修体系",
            "exceptions": "上古仙器不在此列",
        },
    ],
    "characters": [
        {
            "name": "林辰",
            "identity": "沉睡千年的上古炼器宗师转世",
            "personality": "沉稳内敛，重情重义，面对困难绝不退缩",
            "desire": "找回失去的记忆，重建器修传承",
            "fear": "失去重要的人",
            "current_goal": "突破筑基期，找到灵脉封印的线索",
            "abilities": "上古炼器术、雷属性灵根、器灵感应",
            "weaknesses": "记忆残缺，炼器消耗精血",
            "source_status": "ai_suggestion",
        },
        {
            "name": "苏晴",
            "identity": "青云宗长老之女，天才剑修",
            "personality": "外冷内热，正义感强，对不公绝不妥协",
            "desire": "查明父亲失踪的真相",
            "fear": "被利用",
            "current_goal": "保护林辰，同时追查父亲下落",
            "abilities": "青云剑法、冰属性灵力",
            "weaknesses": "容易轻信他人",
            "source_status": "ai_suggestion",
        },
        {
            "name": "赵无极",
            "identity": "黑风寨寨主，灭门林家的主谋之一",
            "personality": "阴险狡诈，野心勃勃，表面儒雅实则狠辣",
            "desire": "获取上古炼器秘法，称霸修仙界",
            "fear": "真相败露",
            "current_goal": "追杀林辰，夺取其记忆碎片",
            "abilities": "暗属性功法、傀儡术",
            "weaknesses": "过度自信",
            "source_status": "ai_suggestion",
        },
    ],
    "plot_threads": [
        {
            "title": "灭门真相",
            "thread_type": "main",
            "description": "林辰追查家族被灭的真相，发现背后涉及灵脉封印和上古势力的阴谋",
            "characters_involved": "林辰、赵无极、神秘幕后人",
            "start_chapter": "第一章",
            "current_status": "active",
        },
        {
            "title": "器修复兴",
            "thread_type": "main",
            "description": "林辰重建器修传承，对抗修仙界对器修的偏见和打压",
            "characters_involved": "林辰、苏晴、器修前辈残魂",
            "start_chapter": "第三章",
            "current_status": "active",
        },
        {
            "title": "灵脉封印",
            "thread_type": "mystery",
            "description": "揭开千年前灵脉被封印的真相，以及封印者的真正目的",
            "characters_involved": "林辰、上古遗迹守护者",
            "start_chapter": "第五章",
            "current_status": "active",
        },
    ],
    "foreshadowings": [
        {
            "content": "林辰体内的远古血脉在雷劫中出现异动",
            "planted_chapter": "第一章",
            "evidence": "雷劫时林辰体内涌出金色光芒，击退赵无极",
            "expected_payoff_range": "第15-25章",
            "status": "planted",
            "related_characters": "林辰",
        },
        {
            "content": "赵无极提到'那个人'会很高兴",
            "planted_chapter": "第三章",
            "evidence": "赵无极逃走前自言自语",
            "expected_payoff_range": "第30-50章",
            "status": "planted",
            "related_characters": "赵无极、神秘幕后人",
        },
        {
            "content": "灵脉封印处传出微弱的器鸣声",
            "planted_chapter": "第五章",
            "evidence": "林辰在后山感应到与炼器术共鸣的声音",
            "expected_payoff_range": "第20-40章",
            "status": "planted",
            "related_characters": "林辰",
        },
    ],
    "secrets": [
        {
            "title": "灵脉封印的真相",
            "description": "灵脉并非天灾被封，而是上古修士为了阻止某件灾难性事件而主动封印，但封印本身正在被侵蚀",
            "known_by": "无（AI 初始设定）",
        },
        {
            "title": "林辰身世",
            "description": "林辰并非普通转世，而是上古炼器宗师以自身为器灵封印了一条主灵脉，千年后以人形苏醒",
            "known_by": "无（AI 初始设定）",
        },
    ],
    "limitations": [
        {
            "title": "炼器代价",
            "description": "每次炼器消耗精血，品级越高消耗越大，连续炼器会导致虚弱甚至折寿",
        },
        {
            "title": "记忆碎片",
            "description": "林辰的记忆以碎片形式恢复，每次突破一个大境界才能解锁一段记忆，强行回忆会神魂受损",
        },
    ],
    "reader_promises": [
        {
            "title": "炼器打脸",
            "description": "被轻视的器修主角当众炼出超越常规的灵器，震惊全场",
        },
        {
            "title": "真相大白",
            "description": "灭门真相逐步揭开，每一步都伴随着更大的阴谋",
        },
    ],
}


async def generate_bible_candidates(
    session: AsyncSession,
    direction_id: str,
    project_id: str,
) -> list[BibleCandidate]:
    """Generate bible candidates from an adopted creative direction."""
    direction = await session.get(CreativeDirection, direction_id)
    if not direction:
        raise ValueError(f"Direction not found: {direction_id}")
    if direction.status != "adopted":
        raise ValueError(f"Direction must be adopted (current: {direction.status})")
    if direction.project_id != project_id:
        raise ValueError("Direction does not belong to this project")

    provider = get_llm_provider()
    candidates: list[BibleCandidate] = []

    categories = [
        ("world_rule", "world_rules"),
        ("character", "characters"),
        ("plot_thread", "plot_threads"),
        ("foreshadowing", "foreshadowings"),
        ("secret", "secrets"),
        ("limitation", "limitations"),
        ("reader_promise", "reader_promises"),
    ]

    for category, mock_key in categories:
        mock_items = MOCK_BIBLE.get(mock_key, [])

        if provider.get_provider_name() == "mock":
            items = mock_items
            async with track_llm_call(
                provider="mock",
                model="mock-novel-model",
                task_type=f"bible_{category}",
            ) as ctx:
                ctx.input_tokens = 500
                ctx.output_tokens = 800
                ctx.status = "success"
        else:
            # Real LLM call would go here
            items = mock_items

        for item_data in items:
            title = item_data.get("name") or item_data.get("title") or item_data.get("content", "")[:50]
            candidate = BibleCandidate(
                project_id=project_id,
                direction_id=direction_id,
                category=category,
                title=title,
                content_json=json.dumps(item_data, ensure_ascii=False),
                source_status="ai_suggestion",
                status="pending",
            )
            session.add(candidate)
            candidates.append(candidate)

    await session.flush()
    for c in candidates:
        await session.refresh(c)

    return candidates


async def approve_candidate(session: AsyncSession, candidate_id: str) -> BibleCandidate:
    """Approve a candidate (mark as approved, do not yet apply to bible)."""
    candidate = await session.get(BibleCandidate, candidate_id)
    if not candidate:
        raise ValueError(f"Candidate not found: {candidate_id}")
    if candidate.status != "pending":
        raise ValueError(f"Candidate is not pending (current: {candidate.status})")
    candidate.status = "approved"
    candidate.confirmed_at = datetime.now(timezone.utc)
    await session.flush()
    return candidate


async def reject_candidate(session: AsyncSession, candidate_id: str, reason: str = "") -> BibleCandidate:
    """Reject a candidate."""
    candidate = await session.get(BibleCandidate, candidate_id)
    if not candidate:
        raise ValueError(f"Candidate not found: {candidate_id}")
    candidate.status = "rejected"
    candidate.rejection_reason = reason
    await session.flush()
    return candidate


async def apply_candidates(session: AsyncSession, project_id: str, candidate_ids: list[str]) -> dict:
    """Apply approved candidates to the actual bible tables. Uses transaction."""
    results = {"applied": 0, "errors": []}

    for cid in candidate_ids:
        candidate = await session.get(BibleCandidate, cid)
        if not candidate or candidate.project_id != project_id:
            results["errors"].append(f"Candidate not found: {cid}")
            continue
        if candidate.status != "approved":
            results["errors"].append(f"Candidate {cid} not approved (status: {candidate.status})")
            continue

        content = json.loads(candidate.content_json)
        bible_id = ""

        try:
            if candidate.category == "world_rule":
                obj = WorldRule(
                    project_id=project_id,
                    name=content.get("name", candidate.title),
                    category=content.get("category", ""),
                    description=content.get("description", ""),
                    scope=content.get("scope", ""),
                    exceptions=content.get("exceptions", ""),
                    source_status="ai_suggestion",
                )
                session.add(obj)
                await session.flush()
                bible_id = obj.id

            elif candidate.category == "character":
                obj = Character(
                    project_id=project_id,
                    name=content.get("name", candidate.title),
                    identity=content.get("identity", ""),
                    personality=content.get("personality", ""),
                    desire=content.get("desire", ""),
                    fear=content.get("fear", ""),
                    current_goal=content.get("current_goal", ""),
                    abilities=content.get("abilities", ""),
                    weaknesses=content.get("weaknesses", ""),
                    source_status="ai_suggestion",
                )
                session.add(obj)
                await session.flush()
                bible_id = obj.id

            elif candidate.category == "plot_thread":
                obj = PlotThread(
                    project_id=project_id,
                    title=content.get("title", candidate.title),
                    thread_type=content.get("thread_type", "main"),
                    description=content.get("description", ""),
                    characters_involved=content.get("characters_involved", ""),
                    start_chapter=content.get("start_chapter", ""),
                    current_status=content.get("current_status", "active"),
                    source_status="ai_suggestion",
                )
                session.add(obj)
                await session.flush()
                bible_id = obj.id

            elif candidate.category == "foreshadowing":
                obj = Foreshadowing(
                    project_id=project_id,
                    content=content.get("content", candidate.title),
                    planted_chapter=content.get("planted_chapter", ""),
                    evidence=content.get("evidence", ""),
                    expected_payoff_range=content.get("expected_payoff_range", ""),
                    status=content.get("status", "planted"),
                    related_characters=content.get("related_characters", ""),
                    source_status="ai_suggestion",
                )
                session.add(obj)
                await session.flush()
                bible_id = obj.id

            else:
                # For secrets/limitations/reader_promises, store as world rules
                obj = WorldRule(
                    project_id=project_id,
                    name=content.get("title") or content.get("name", candidate.title),
                    category=candidate.category,
                    description=content.get("description", ""),
                    source_status="ai_suggestion",
                )
                session.add(obj)
                await session.flush()
                bible_id = obj.id

            candidate.status = "applied"
            candidate.applied_bible_id = bible_id
            results["applied"] += 1

        except Exception as e:
            logger.exception("Failed to apply candidate %s", cid)
            results["errors"].append(f"Failed to apply {cid}: {e}")
            raise  # Transaction rollback

    return results


async def undo_apply(session: AsyncSession, candidate_id: str) -> BibleCandidate:
    """Undo an applied candidate — delete from bible and reset to pending."""
    candidate = await session.get(BibleCandidate, candidate_id)
    if not candidate:
        raise ValueError(f"Candidate not found: {candidate_id}")
    if candidate.status != "applied":
        raise ValueError(f"Candidate not applied (status: {candidate.status})")

    # Delete from bible table
    if candidate.applied_bible_id:
        if candidate.category in ("world_rule", "secret", "limitation", "reader_promise"):
            obj = await session.get(WorldRule, candidate.applied_bible_id)
        elif candidate.category == "character":
            obj = await session.get(Character, candidate.applied_bible_id)
        elif candidate.category == "plot_thread":
            obj = await session.get(PlotThread, candidate.applied_bible_id)
        elif candidate.category == "foreshadowing":
            obj = await session.get(Foreshadowing, candidate.applied_bible_id)
        else:
            obj = None
        if obj:
            await session.delete(obj)

    candidate.status = "pending"
    candidate.applied_bible_id = ""
    candidate.confirmed_at = None
    await session.flush()
    return candidate
