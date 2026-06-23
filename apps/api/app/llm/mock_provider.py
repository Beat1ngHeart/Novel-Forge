"""Mock LLM Provider — no API key required, returns preset data for development."""

from __future__ import annotations

import asyncio
import json
import random

from app.llm.base import LLMProvider, LLMResponse, TokenCount

MOCK_HEALTHY_RESPONSE = {
    "status": "healthy",
    "provider": "mock",
    "model": "mock-novel-model",
    "latency_ms": 42,
}

MOCK_STORY_GENE = {
    "schema_version": 1,
    "chapter_id": "",
    "confidence": 0.85,
    "ambiguities": ["部分对话含义不明确"],
    "genre": "xuanhuan",
    "subgenre": "升级流",
    "chapter_function": "rising",
    "point_of_view": "third_limited",
    "narrative_person": "protagonist",
    "scene_count": 3,
    "pacing": "fast",
    "conflict": {
        "protagonist_goal": "突破当前修为瓶颈",
        "obstacle": "黑风寨长老的偷袭",
        "conflict_initiator": "黑风寨长老·赵无极",
        "conflict_target": "主角林辰",
        "conflict_type": "person_vs_person",
        "resolution": "主角激发隐藏血脉击退敌人",
        "conflict_result": "主角重伤，敌人逃走",
    },
    "emotion": {
        "emotional_start": "anticipation",
        "emotional_curve": "anticipation→tension→anger→determination→relief",
        "emotional_end": "determination",
        "suppression_intensity": 8,
        "payoff_type": "power_display",
        "payoff_intensity": 7,
        "reversal_type": "power",
        "reversal_intensity": 8,
    },
    "suspense": {
        "information_gains": [
            "揭示黑风寨与主角家族的旧怨",
            "展示主角隐藏的雷属性血脉",
        ],
        "new_settings": ["九天雷劫的三重考验"],
        "new_characters": ["黑风寨长老·赵无极"],
        "unresolved_questions": [
            "赵无极为何知道林辰的渡劫时间",
            "林辰体内的远古血脉究竟是什么",
        ],
        "suspense_type": "crisis",
        "ending_hook": "林辰昏迷中感应到血脉深处一个古老的声音在呼唤他",
        "hook_type": "cliffhanger",
        "hook_intensity": 9,
    },
    "state_changes": {
        "relationship_changes": [
            {
                "character_a": "林辰",
                "character_b": "赵无极",
                "before": "陌生",
                "after": "死敌",
                "reason": "赵无极偷袭并揭露灭门旧怨",
            }
        ],
        "power_changes": [
            {"entity": "林辰", "before": "筑基巅峰", "after": "短暂金丹期战力", "reason": "激活隐藏雷属性血脉"}
        ],
        "resource_changes": [{"entity": "林辰", "before": "200块中品灵石", "after": "0块", "reason": "布阵消耗"}],
        "health_changes": [{"entity": "林辰", "before": "状态良好", "after": "重伤昏迷", "reason": "强行催动血脉"}],
        "location_changes": [
            {"entity": "林辰", "before": "青云峰渡劫台", "after": "青云峰后山密室", "reason": "被师门转移救治"}
        ],
        "knowledge_changes": [
            {
                "entity": "林辰",
                "before": "不知家族被灭真相",
                "after": "得知黑风寨参与灭门",
                "reason": "赵无极临走前透露",
            }
        ],
    },
    "foreshadowing": {
        "planted": [
            {
                "foreshadow_id": "fs_blood_awaken",
                "description": "林辰体内沉睡的远古血脉在雷劫中出现异动",
                "planted_in_chapter": None,
                "expected_payoff_range": "第10-20章",
            }
        ],
        "fulfilled": [],
    },
    "text_stats": {
        "dialogue_ratio": 0.35,
        "psychological_description_ratio": 0.25,
        "environment_description_ratio": 0.15,
        "average_sentence_length": 28.5,
        "average_paragraph_length": 85.0,
        "action_density": 0.6,
    },
    "chapter_summary": (
        "林辰在青云峰准备突破金丹期，却在雷劫降临时遭到黑风寨长老赵无极偷袭。"
        "赵无极揭露与林家的灭门旧怨。林辰在生死关头激发体内沉睡的远古雷属性血脉，"
        "以远超金丹期的战力击退赵无极，但自己也因强行催动血脉而重伤。"
        "章末，林辰昏迷中感应到血脉深处一个古老的声音在呼唤他。"
    ),
}

# Three structurally different creative directions for the same input
MOCK_CREATIVE_DIRECTIONS = [
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
        "difference_from_tropes": "不是升级打怪，而是通过创造和修复来成长；能力越强代价越大，没有免费的午餐",
        "homogenization_risk": "炼器题材已有较多作品，需要在器物设定和代价机制上做出差异化",
        "sustainable_length": "200-400万字，可通过解锁更高阶器物和发现更多上古秘密来延续",
        "potential_collapse_point": "如果炼器过程过于重复或代价机制被削弱，会变成普通的升级流",
    },
    {
        "one_line_hook": "一个能看到所有人寿命倒计时的兽医，意外发现自己能通过救治灵兽延长他人寿命",
        "core_reader_promise": "看主角在修仙世界用现代医学思维治病救人，同时揭开自己能力背后的惊天秘密",
        "protagonist_identity": "穿越到修仙世界的现代兽医，觉醒了能看见寿命的异瞳",
        "protagonist_goal": "在这个弱肉强食的世界活下去，找到回到原来世界的方法，同时解开异瞳的来历",
        "core_ability": "异瞳——能看见所有生物的寿命倒计时和病灶位置，通过救治可以延长寿命",
        "ability_cost": "每次使用异瞳会短暂失明，救治越严重的病症失明时间越长，过度使用可能导致永久失明",
        "core_conflict": "各大势力都想控制主角的异瞳能力，而主角只想低调行医，同时发现灵兽身上的秘密",
        "world_mystery": "修仙世界的灵兽并非自然产物，而是远古文明的实验品，异瞳的真正功能是读取灵兽体内的远古信息",
        "growth_cycle": "救治低阶灵兽→获得信任和资源→遇到疑难杂症→研究灵兽获得新知识→解锁更高阶治疗术→名声渐起",
        "resource_cycle": "免费救治建立口碑→收取高级灵兽作为报酬→研究灵兽获得知识→知识转化为更强的治疗能力",
        "payoff_cycle": "被人轻视兽医身份→灵兽救治成功震惊全场→各大势力争相邀请→用医术换取修炼资源和保护",
        "long_term_suspense": "异瞳的前一任主人是谁？远古文明创造灵兽的目的是什么？主角为什么会被选中穿越？",
        "difference_from_tropes": "不是战斗型主角，而是辅助型；成长不靠打怪，靠知识积累和人脉经营",
        "homogenization_risk": "医修题材有《大医凌天》等先例，需要在灵兽医学和异瞳设定上做出独特性",
        "sustainable_length": "150-300万字，灵兽种类和疑难杂症的多样性决定了篇幅上限",
        "potential_collapse_point": "如果变成万能医生或战斗能力过强，会失去紧张感和读者代入感",
    },
    {
        "one_line_hook": "一个被诅咒的废材，发现自己的诅咒其实是上古神灵的试炼",
        "core_reader_promise": "看主角在所有人都认为他是废物的情况下，一步步将诅咒转化为超越天才的力量",
        "protagonist_identity": "身负'天罚之体'诅咒的落魄贵族后裔，被家族驱逐，被视为不祥之人",
        "protagonist_goal": "洗刷家族冤屈，查明天罚之体的真相，证明自己不是废物",
        "core_ability": "天罚之体——能吸收一切负面状态（毒、诅咒、精神攻击）转化为自身力量",
        "ability_cost": "转化过程极度痛苦，且吸收的负面能量会暂时影响性格和判断力，严重时可能暴走",
        "core_conflict": "天罚之体是上古神灵的试炼，通过者可获神力，但历史上从未有人成功",
        "world_mystery": "上古神灵为何要留下这样的试炼？试炼的真正目的是什么？通过试炼后会获得什么？",
        "growth_cycle": "遭遇负面攻击→痛苦吸收→力量暴涨但性格受影响→冷静下来消化→获得新能力→遇到更强的负面攻击",
        "resource_cycle": "主动寻找危险区域→吸收各种诅咒和毒素→消化后获得独特抗性→用抗性帮助他人换取资源和情报",
        "payoff_cycle": "被嘲笑废物→遭遇致命攻击→吸收攻击力量暴涨→众人震惊→引来更强敌人→再次被逼入绝境→更强的吸收",
        "long_term_suspense": "历史上那些变成怪物的试炼者去了哪里？天罚之体的最终形态是什么？",
        "difference_from_tropes": "能力来自受苦而非天赋，越痛苦越强大，但代价是可能失去自我",
        "homogenization_risk": "废材逆袭是经典套路，需要在诅咒/试炼设定和性格变化描写上做出深度",
        "sustainable_length": "300-500万字，试炼层级和历史秘密可支撑长篇",
        "potential_collapse_point": "如果痛苦描写流于表面或暴走解决一切问题，会失去读者共鸣",
    },
]


class MockConnectionError(ConnectionError):
    """Simulated connection failure."""


class MockTimeoutError(asyncio.TimeoutError):
    """Simulated timeout."""


class MockRateLimitError(Exception):
    """Simulated rate limit (HTTP 429)."""

    def __init__(self, retry_after: float = 1.0):
        self.retry_after = retry_after
        super().__init__(f"Rate limited. Retry after {retry_after}s")


class MockLLMProvider(LLMProvider):
    """Simulates LLM responses for development and testing.

    Supports simulating normal responses, failures, timeouts, and rate limits.
    """

    def __init__(
        self,
        fail_rate: float = 0.0,
        timeout_rate: float = 0.0,
        rate_limit_rate: float = 0.0,
        simulate_latency_ms: int = 100,
    ):
        self._fail_rate = fail_rate
        self._timeout_rate = timeout_rate
        self._rate_limit_rate = rate_limit_rate
        self._latency_ms = simulate_latency_ms

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        await self._simulate_latency()
        self._maybe_simulate_error()

        return LLMResponse(
            content=json.dumps(
                {"response": "mock chat response", "message_count": len(messages)},
                ensure_ascii=False,
            ),
            input_tokens=200,
            output_tokens=100,
            model="mock-novel-model",
            provider="mock",
        )

    async def structured_output(
        self,
        messages: list[dict[str, str]],
        schema: dict,
        temperature: float = 0.3,
    ) -> LLMResponse:
        await self._simulate_latency()
        self._maybe_simulate_error()

        # Check if this is a StoryGene request
        if schema.get("title") == "StoryGene" or "chapter_function" in schema.get("properties", {}):
            content = json.dumps(MOCK_STORY_GENE, ensure_ascii=False)
        else:
            content = json.dumps(self._generate_from_schema(schema), ensure_ascii=False)

        return LLMResponse(
            content=content,
            input_tokens=300,
            output_tokens=200,
            model="mock-novel-model",
            provider="mock",
        )

    async def embedding(self, texts: list[str]) -> list[list[float]]:
        await self._simulate_latency()
        self._maybe_simulate_error()
        return [[0.1 * (i % 10) for i in range(1536)] for _ in texts]

    async def count_tokens(self, text: str) -> TokenCount:
        # Simple approximation: ~1 token per 2 characters for Chinese
        count = max(1, len(text) // 2)
        return TokenCount(count=count, model="mock-novel-model")

    async def health_check(self) -> dict:
        return MOCK_HEALTHY_RESPONSE

    def get_provider_name(self) -> str:
        return "mock"

    def get_model_name(self) -> str:
        return "mock-novel-model"

    async def _simulate_latency(self) -> None:
        jitter = random.randint(0, self._latency_ms // 2)
        await asyncio.sleep((self._latency_ms + jitter) / 1000)

    def _maybe_simulate_error(self) -> None:
        r = random.random()
        cumulative = 0.0

        cumulative += self._rate_limit_rate
        if r < cumulative:
            raise MockRateLimitError(retry_after=random.uniform(1.0, 5.0))

        cumulative += self._timeout_rate
        if r < cumulative:
            raise MockTimeoutError("Mock LLM: simulated timeout")

        cumulative += self._fail_rate
        if r < cumulative:
            raise MockConnectionError("Mock LLM: simulated connection failure")

    def _generate_from_schema(self, schema: dict) -> dict:
        """Generate a minimal valid object from a JSON Schema."""
        props = schema.get("properties", {})
        result = {}
        for key, prop in props.items():
            t = prop.get("type", "string")
            if t == "string":
                result[key] = f"mock_{key}"
            elif t == "integer":
                result[key] = 1
            elif t == "number":
                result[key] = 0.5
            elif t == "boolean":
                result[key] = True
            elif t == "array":
                result[key] = []
            elif t == "object":
                result[key] = {}
            else:
                result[key] = f"mock_{key}"
        return result
