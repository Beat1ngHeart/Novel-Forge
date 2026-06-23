"""Draft service — generates chapter drafts from adopted plans."""

from __future__ import annotations

import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ChapterDraft, ChapterPlan
from app.llm import get_llm_provider
from app.llm.call_logger import track_llm_call
from app.schemas.draft import DraftParameters

logger = logging.getLogger(__name__)

MOCK_DRAFT_BODY = """清晨的阳光从破旧的窗棂间洒入，林辰缓缓睁开双眼。

又是那个梦。梦中有一片无边无际的火海，火海中央悬浮着一柄古剑，剑身上的纹路与他怀中玉佩上的图案一模一样。

"又是这个梦。"他低声自语，抬手按住胸口的玉佩。温热的触感传来，让他安心了几分。

门外传来急促的脚步声。

"林师弟！林师弟！"

是苏晴的声音。

林辰翻身坐起，推开门。苏晴站在院中，脸色有些苍白，显然是一路跑来的。

"怎么了？"

"师父让你立刻去大殿。"苏晴压低声音，"赵无极来了，带了很多人。"

林辰的瞳孔微缩。自从上次在炼器坊一战，赵无极已经消失了三个月。这次突然出现，而且带着人来，恐怕不是善了的架势。

"走。"他没有多问，转身取了那柄自己炼制的灵剑。

大殿之上，气氛凝重。

青云宗宗主端坐主位，两侧是各峰长老。赵无极站在殿中，身后站着十几个黑衣修士，每一个都散发着筑基期以上的气息。

"林辰。"赵无极看到他进来，嘴角浮现一丝笑意，"好久不见。"

"赵长老。"林辰平静回应，目光扫过他身后的人马，心中快速评估着局势。

"我这次来，是替一位前辈传话。"赵无极从袖中取出一封信，递给宗主，"当年之事，该有个了断了。"

宗主看完信，脸色骤变。

林辰注意到，师父的手微微颤抖。
"""

MOCK_CHAPTER_SUMMARY = "林辰被打乱平静。赵无极来传话。宗主反应暗示身世有关。"

MOCK_CANDIDATES = {
    "new_characters": [
        {"name": "黑衣修士首领", "identity": "赵无极的手下，筑基后期", "suggestion": "可发展为常驻小反派"}
    ],
    "new_settings": [{"name": "传话信件", "description": "来自幕后势力的正式通牒", "suggestion": "后续可展开信件内容"}],
    "state_changes": [
        {"entity": "林辰", "before": "平静修炼", "after": "面临新的威胁", "suggestion": "需确认是否正式记录"}
    ],
    "foreshadows": [{"content": "宗主看完信后脸色骤变", "suggestion": "伏笔：信中内容与林辰身世有关"}],
    "facts_to_confirm": ["赵无极提到的'前辈'是谁", "'当年之事'具体指什么", "师父的手为何颤抖"],
}


async def generate_draft(
    session: AsyncSession,
    project_id: str,
    plan_id: str,
    params: DraftParameters,
) -> ChapterDraft:
    """Generate a chapter draft from an adopted plan."""
    plan = await session.get(ChapterPlan, plan_id)
    if not plan:
        raise ValueError(f"Plan not found: {plan_id}")
    if plan.project_id != project_id:
        raise ValueError("Plan does not belong to this project")
    if plan.status != "adopted":
        raise ValueError(f"Plan must be adopted to generate draft (current: {plan.status})")

    provider = get_llm_provider()

    if provider.get_provider_name() == "mock":
        body = MOCK_DRAFT_BODY
        summary = MOCK_CHAPTER_SUMMARY
        async with track_llm_call(
            provider="mock",
            model="mock-novel-model",
            task_type="draft_generation",
        ) as ctx:
            ctx.input_tokens = 800
            ctx.output_tokens = 2000
            ctx.status = "success"
        llm_call_id = ctx.log_id
    else:
        # Real LLM call would go here
        body = MOCK_DRAFT_BODY
        summary = MOCK_CHAPTER_SUMMARY
        llm_call_id = ""

    draft = ChapterDraft(
        project_id=project_id,
        plan_id=plan_id,
        draft_type="ai_draft",
        target_words=params.target_words,
        person=params.person,
        pov=params.pov,
        dialogue_density=params.dialogue_density,
        description_density=params.description_density,
        pacing=params.pacing,
        emotion_intensity=params.emotion_intensity,
        paragraph_length=params.paragraph_length,
        language_strictness=params.language_strictness,
        hook_strength=params.hook_strength,
        body_text=body,
        chapter_summary=summary,
        actual_word_count=len(body),
        new_character_candidates_json=json.dumps(MOCK_CANDIDATES["new_characters"], ensure_ascii=False),
        new_setting_candidates_json=json.dumps(MOCK_CANDIDATES["new_settings"], ensure_ascii=False),
        state_change_candidates_json=json.dumps(MOCK_CANDIDATES["state_changes"], ensure_ascii=False),
        foreshadow_candidates_json=json.dumps(MOCK_CANDIDATES["foreshadows"], ensure_ascii=False),
        facts_to_confirm_json=json.dumps(MOCK_CANDIDATES["facts_to_confirm"], ensure_ascii=False),
        status="ai_draft",
        llm_call_id=llm_call_id,
    )
    session.add(draft)
    await session.flush()
    await session.refresh(draft)
    return draft


async def update_draft_text(
    session: AsyncSession,
    draft_id: str,
    new_text: str,
) -> ChapterDraft:
    """Update draft body text (human revision)."""
    draft = await session.get(ChapterDraft, draft_id)
    if not draft:
        raise ValueError(f"Draft not found: {draft_id}")
    draft.body_text = new_text
    draft.actual_word_count = len(new_text)
    draft.status = "human_revision"
    await session.flush()
    return draft


async def rewrite_paragraph(
    session: AsyncSession,
    draft_id: str,
    paragraph_index: int,
    instruction: str,
) -> ChapterDraft:
    """Rewrite a specific paragraph of the draft."""
    draft = await session.get(ChapterDraft, draft_id)
    if not draft:
        raise ValueError(f"Draft not found: {draft_id}")

    paragraphs = draft.body_text.split("\n\n")
    if paragraph_index >= len(paragraphs):
        raise ValueError(f"Paragraph index {paragraph_index} out of range (total: {len(paragraphs)})")

    provider = get_llm_provider()
    if provider.get_provider_name() == "mock":
        old_text = paragraphs[paragraph_index]
        paragraphs[paragraph_index] = f"[改写] {old_text}"
    else:
        # Real LLM rewrite would go here
        pass

    draft.body_text = "\n\n".join(paragraphs)
    draft.actual_word_count = len(draft.body_text)
    draft.status = "human_revision"
    await session.flush()
    return draft
