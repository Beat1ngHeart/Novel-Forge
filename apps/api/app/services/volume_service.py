"""Volume service — generates and manages volume outlines."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import NovelSynopsis, VolumeOutline
from app.llm import get_llm_provider
from app.llm.call_logger import track_llm_call
from app.schemas.volume import VolumeContent

logger = logging.getLogger(__name__)

MOCK_VOLUMES = [
    {
        "volume_name": "第一卷：觉醒",
        "volume_goal": "建立主角身份、世界观和核心冲突，完成第一次成长蜕变",
        "core_conflict": "主角苏醒后被视为废物，必须在末法时代证明器修的价值，同时对抗黑风寨的追杀",
        "start_state": "主角沉睡苏醒，失去记忆和修为，身无分文，被视为不祥之人",
        "end_state": "主角突破筑基期，初步恢复器修能力，获得青云宗认可，发现灵脉异常线索",
        "main_enemy": "赵无极（黑风寨长老）——直接追杀主角的执行者",
        "character_changes": "林辰：废物→初显器修天赋\n苏晴：旁观者→主动保护\n赵无极：隐藏监视→公开追杀",
        "new_world_settings": "灵气等级体系、器物品级体系、末法时代的灵脉分布",
        "growth_milestone": "第一次成功炼器（从凡器到灵器的跨越）",
        "payoff_climax": "当众炼出超越预期的灵器，震惊质疑者",
        "volume_twist": "发现赵无极追杀自己并非私人恩怨，而是受人指使",
        "foreshadow_planted": "主角体内异常的雷属性灵脉\n灵脉封印处的器鸣声\n赵无极口中的'那个人'",
        "foreshadow_resolved": "主角的炼器天赋来源（部分揭示）",
        "reader_promise_fulfilled": "废物逆袭第一次展现实力",
        "estimated_chapters": 50,
        "estimated_words": 150000,
    },
    {
        "volume_name": "第二卷：崛起",
        "volume_goal": "主角在修仙界站稳脚跟，建立核心团队，发现更大的阴谋",
        "core_conflict": "器修复兴遭遇保守势力打压，主角必须在政治博弈中找到生存空间",
        "start_state": "主角已获青云宗认可，但修仙界对器修的偏见依然根深蒂固",
        "end_state": "主角名声初显，组建核心团队，发现灵脉封印的更多线索，与幕后势力首次交锋",
        "main_enemy": "修仙界保守派长老——打压器修的幕后推手",
        "character_changes": "林辰：初出茅庐→小有名气\n苏晴：保护者→并肩战友\n新角色：器修同伴加入",
        "new_world_settings": "各门派势力分布、灵脉地图、上古遗迹传说",
        "growth_milestone": "解锁第二阶炼器术",
        "payoff_climax": "用炼器术解决门派危机，获得长老席位",
        "volume_twist": "发现打压器修的势力与千年前的灵脉封印有关",
        "foreshadow_planted": "主角记忆碎片中的神秘女子\n灵脉深处的古老阵法",
        "foreshadow_resolved": "赵无极的幕后指使者身份（部分）",
        "reader_promise_fulfilled": "更大规模的炼器打脸 + 门派政治博弈",
        "estimated_chapters": 70,
        "estimated_words": 210000,
    },
    {
        "volume_name": "第三卷：真相",
        "volume_goal": "揭开灵脉封印的真相，主角身世大揭秘，迎来全书最大转折",
        "core_conflict": "主角发现自己的前世与灵脉封印直接相关，必须在拯救世界和保全自我之间做出选择",
        "start_state": "主角已是修仙界新星，但记忆碎片越来越频繁",
        "end_state": "主角知晓前世真相，解封第一条主灵脉，但代价是失去部分修为",
        "main_enemy": "幕后势力首领——与主角前世有直接关联",
        "character_changes": "林辰：追求力量→理解责任\n苏晴：并肩→面临信任考验",
        "new_world_settings": "上古文明遗迹、远古种族、灵脉封印的真正目的",
        "growth_milestone": "解锁完整上古炼器术",
        "payoff_climax": "解封灵脉的壮举",
        "volume_twist": "主角前世是封印的执行者，解封可能释放远古威胁",
        "foreshadow_planted": "远古种族的微弱信号",
        "foreshadow_resolved": "主角身世之谜、灵脉封印真相",
        "reader_promise_fulfilled": "终极真相大揭秘",
        "estimated_chapters": 80,
        "estimated_words": 240000,
    },
]


async def generate_all_volumes(
    session: AsyncSession,
    project_id: str,
    synopsis_id: str,
) -> list[VolumeOutline]:
    """Generate all volume outlines from an adopted synopsis."""
    synopsis = await session.get(NovelSynopsis, synopsis_id)
    if not synopsis:
        raise ValueError(f"Synopsis not found: {synopsis_id}")
    if synopsis.project_id != project_id:
        raise ValueError("Synopsis does not belong to this project")
    if synopsis.status != "adopted":
        raise ValueError(f"Synopsis must be adopted (current: {synopsis.status})")

    provider = get_llm_provider()
    volumes: list[VolumeOutline] = []

    for i, vol_data in enumerate(MOCK_VOLUMES):
        if provider.get_provider_name() == "mock":
            content = VolumeContent(**vol_data)
            async with track_llm_call(
                provider="mock",
                model="mock-novel-model",
                task_type="volume_outline",
            ) as ctx:
                ctx.input_tokens = 500
                ctx.output_tokens = 800
                ctx.status = "success"
        else:
            content = VolumeContent(**vol_data)

        vol = VolumeOutline(
            project_id=project_id,
            synopsis_id=synopsis_id,
            volume_index=i,
            volume_name=content.volume_name,
            status="draft",
            is_current=False,
            **content.model_dump(exclude={"volume_name"}),
            ai_original_json=content.model_dump_json(),
        )
        session.add(vol)
        volumes.append(vol)

    await session.flush()
    for v in volumes:
        await session.refresh(v)
    return volumes


async def regenerate_volume(
    session: AsyncSession,
    project_id: str,
    volume_id: str,
) -> VolumeOutline:
    """Regenerate a single volume. Other volumes are not affected."""
    vol = await session.get(VolumeOutline, volume_id)
    if not vol or vol.project_id != project_id:
        raise ValueError(f"Volume not found: {volume_id}")

    # Generate new content (mock)
    mock_idx = vol.volume_index % len(MOCK_VOLUMES)
    content = VolumeContent(**MOCK_VOLUMES[mock_idx])

    vol.volume_name = content.volume_name
    vol.volume_goal = content.volume_goal
    vol.core_conflict = content.core_conflict
    vol.start_state = content.start_state
    vol.end_state = content.end_state
    vol.main_enemy = content.main_enemy
    vol.character_changes = content.character_changes
    vol.new_world_settings = content.new_world_settings
    vol.growth_milestone = content.growth_milestone
    vol.payoff_climax = content.payoff_climax
    vol.volume_twist = content.volume_twist
    vol.foreshadow_planted = content.foreshadow_planted
    vol.foreshadow_resolved = content.foreshadow_resolved
    vol.reader_promise_fulfilled = content.reader_promise_fulfilled
    vol.estimated_chapters = content.estimated_chapters
    vol.estimated_words = content.estimated_words
    vol.ai_original_json = content.model_dump_json()
    vol.status = "draft"
    vol.is_current = False

    await session.flush()
    await session.refresh(vol)
    return vol


async def edit_volume(
    session: AsyncSession,
    volume_id: str,
    updates: dict,
) -> VolumeOutline:
    """Edit a volume, preserving AI original and recording human edits."""
    vol = await session.get(VolumeOutline, volume_id)
    if not vol:
        raise ValueError(f"Volume not found: {volume_id}")

    for key, value in updates.items():
        if value is not None and hasattr(vol, key):
            setattr(vol, key, value)

    current_edits = json.loads(vol.human_edits_json) if vol.human_edits_json else {}
    current_edits[str(datetime.now(timezone.utc))] = updates
    vol.human_edits_json = json.dumps(current_edits, ensure_ascii=False)

    await session.flush()
    return vol


async def adopt_volume(session: AsyncSession, volume_id: str) -> VolumeOutline:
    """Adopt a volume."""
    vol = await session.get(VolumeOutline, volume_id)
    if not vol:
        raise ValueError(f"Volume not found: {volume_id}")
    vol.status = "adopted"
    vol.is_current = True
    await session.flush()
    return vol


async def reorder_volumes(
    session: AsyncSession,
    project_id: str,
    volume_ids: list[str],
) -> list[VolumeOutline]:
    """Reorder volumes by setting volume_index."""
    for new_idx, vid in enumerate(volume_ids):
        vol = await session.get(VolumeOutline, vid)
        if not vol or vol.project_id != project_id:
            raise ValueError(f"Volume not found: {vid}")
        vol.volume_index = new_idx

    await session.flush()
    result = await session.execute(
        select(VolumeOutline).where(VolumeOutline.project_id == project_id).order_by(VolumeOutline.volume_index)
    )
    return list(result.scalars().all())
