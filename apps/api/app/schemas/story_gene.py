"""Story Gene Schema — versioned, validated structure for chapter narrative analysis.

Schema version: 1
This schema captures the narrative DNA of a chapter without storing raw text.
All fields allow empty/null values for cases where analysis is uncertain.
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Any

from pydantic import BaseModel, Field

SCHEMA_VERSION = 1


# === Enums ===


class Genre(str, Enum):
    FANTASY = "fantasy"
    XIANXIA = "xianxia"
    XUANHUAN = "xuanhuan"
    URBAN = "urban"
    SCIFI = "scifi"
    HISTORY = "history"
    ROMANCE = "romance"
    MYSTERY = "mystery"
    HORROR = "horror"
    GAME = "game"
    MILITARY = "military"
    SPORTS = "sports"
    OTHER = "other"


class ChapterFunction(str, Enum):
    OPENING = "opening"  # 开场铺垫
    SETUP = "setup"  # 世界观/人物建立
    RISING = "rising"  # 冲突升级
    CLIMAX = "climax"  # 高潮
    FALLING = "falling"  # 冲突消退
    TRANSITION = "transition"  # 过渡
    TWIST = "twist"  # 转折
    FORESHADOW_PLANT = "foreshadow_plant"  # 伏笔埋设
    FORESHADOW_PAYOFF = "foreshadow_payoff"  # 伏笔回收
    CHARACTER_DEV = "character_development"  # 角色塑造
    WORLD_BUILDING = "world_building"  # 世界观展开
    CLIFFHANGER = "cliffhanger"  # 悬念章
    EPILOGUE = "epilogue"  # 尾声
    FILLER = "filler"  # 过渡/日常
    OTHER = "other"


class PointOfView(str, Enum):
    FIRST = "first_person"
    SECOND = "second_person"
    THIRD_LIMITED = "third_limited"
    THIRD_OMNISCIENT = "third_omniscient"
    MULTIPLE = "multiple"
    OTHER = "other"


class NarrativePerson(str, Enum):
    PROTAGONIST = "protagonist"
    ANTAGONIST = "antagonist"
    SUPPORTING = "supporting"
    OBSERVER = "observer"
    MULTIPLE = "multiple"


class Pacing(str, Enum):
    VERY_SLOW = "very_slow"
    SLOW = "slow"
    MEDIUM = "medium"
    FAST = "fast"
    VERY_FAST = "very_fast"


class ConflictType(str, Enum):
    PERSON_VS_PERSON = "person_vs_person"
    PERSON_VS_NATURE = "person_vs_nature"
    PERSON_VS_SOCIETY = "person_vs_society"
    PERSON_VS_SELF = "person_vs_self"
    PERSON_VS_FATE = "person_vs_fate"
    PERSON_VS_RULE = "person_vs_rule"
    PERSON_VS_TECHNOLOGY = "person_vs_technology"
    INTERNAL = "internal"
    MIXED = "mixed"
    NONE = "none"


class Emotion(str, Enum):
    CALM = "calm"
    ANTICIPATION = "anticipation"
    TENSION = "tension"
    EXCITEMENT = "excitement"
    FEAR = "fear"
    ANGER = "anger"
    SADNESS = "sadness"
    DESPAIR = "despair"
    JOY = "joy"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    HOPE = "hope"
    DETERMINATION = "determination"
    RELIEF = "relief"
    BETRAYAL = "betrayal"


class PayoffType(str, Enum):
    POWER_DISPLAY = "power_display"
    FACE_SLAPPING = "face_slapping"
    REVERSAL = "reversal"
    TREASURE_GAIN = "treasure_gain"
    RECOGNITION = "recognition"
    REVELATION = "revelation"
    LEVEL_UP = "level_up"
    ADVANTAGE = "advantage"
    JUSTICE = "justice"
    ROMANCE = "romance"
    NONE = "none"


class ReversalType(str, Enum):
    NONE = "none"
    IDENTITY = "identity"
    STANCE = "stance"
    INFORMATION = "information"
    POWER = "power"
    RELATIONSHIP = "relationship"
    FORTUNE = "fortune"


class SuspenseType(str, Enum):
    NONE = "none"
    INFORMATION = "information"  # 信息悬念
    CRISIS = "crisis"  # 危机悬念
    IDENTITY = "identity"  # 身份悬念
    CHOICE = "choice"  # 选择悬念
    COUNTDOWN = "countdown"  # 倒计时悬念
    PROMISE = "promise"  # 承诺悬念


class HookType(str, Enum):
    NONE = "none"
    CLIFFHANGER = "cliffhanger"  # 悬念钩子
    CRISIS = "crisis"  # 危机钩子
    REVERSAL = "reversal"  # 反转钩子
    INFORMATION = "information"  # 信息钩子
    EMOTIONAL = "emotional"  # 情感钩子
    DESIRE = "desire"  # 欲望钩子
    PROMISE = "promise"  # 承诺钩子


# === Sub-models ===


Intensity = Annotated[int, Field(ge=0, le=10)]
Ratio = Annotated[float, Field(ge=0.0, le=1.0)]


class ConflictInfo(BaseModel):
    protagonist_goal: str = ""
    obstacle: str = ""
    conflict_initiator: str = ""
    conflict_target: str = ""
    conflict_type: ConflictType = ConflictType.NONE
    resolution: str = ""
    conflict_result: str = ""


class EmotionInfo(BaseModel):
    emotional_start: Emotion = Emotion.CALM
    emotional_curve: str = ""  # e.g. "calm→tension→excitement→relief"
    emotional_end: Emotion = Emotion.CALM
    suppression_intensity: Intensity = 0
    payoff_type: PayoffType = PayoffType.NONE
    payoff_intensity: Intensity = 0
    reversal_type: ReversalType = ReversalType.NONE
    reversal_intensity: Intensity = 0


class SuspenseInfo(BaseModel):
    information_gains: list[str] = Field(default_factory=list)
    new_settings: list[str] = Field(default_factory=list)
    new_characters: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    suspense_type: SuspenseType = SuspenseType.NONE
    ending_hook: str = ""
    hook_type: HookType = HookType.NONE
    hook_intensity: Intensity = 0


class StateChange(BaseModel):
    entity: str = ""  # character/object name
    before: str = ""
    after: str = ""
    reason: str = ""


class RelationshipChange(BaseModel):
    character_a: str = ""
    character_b: str = ""
    before: str = ""
    after: str = ""
    reason: str = ""


class StateChanges(BaseModel):
    relationship_changes: list[RelationshipChange] = Field(default_factory=list)
    power_changes: list[StateChange] = Field(default_factory=list)
    resource_changes: list[StateChange] = Field(default_factory=list)
    health_changes: list[StateChange] = Field(default_factory=list)
    location_changes: list[StateChange] = Field(default_factory=list)
    knowledge_changes: list[StateChange] = Field(default_factory=list)


class Foreshadowing(BaseModel):
    foreshadow_id: str = ""
    description: str = ""
    planted_in_chapter: int | None = None
    expected_payoff_range: str = ""  # e.g. "chapter 10-20" or "volume 2"


class ForeshadowInfo(BaseModel):
    planted: list[Foreshadowing] = Field(default_factory=list)
    fulfilled: list[Foreshadowing] = Field(default_factory=list)


class TextStats(BaseModel):
    dialogue_ratio: Ratio = 0.0
    psychological_description_ratio: Ratio = 0.0
    environment_description_ratio: Ratio = 0.0
    average_sentence_length: Annotated[float, Field(ge=0)] = 0.0
    average_paragraph_length: Annotated[float, Field(ge=0)] = 0.0
    action_density: Ratio = 0.0


# === Main Schema ===


class StoryGeneV1(BaseModel):
    """Story Gene Schema v1 — the narrative DNA of a single chapter."""

    # Metadata
    schema_version: int = Field(default=SCHEMA_VERSION, frozen=True)
    chapter_id: str = ""
    confidence: Annotated[float, Field(ge=0.0, le=1.0)] = 0.8
    ambiguities: list[str] = Field(default_factory=list)

    # Basic info
    genre: Genre = Genre.OTHER
    subgenre: str = ""
    chapter_function: ChapterFunction = ChapterFunction.OTHER
    point_of_view: PointOfView = PointOfView.THIRD_LIMITED
    narrative_person: NarrativePerson = NarrativePerson.PROTAGONIST
    scene_count: Annotated[int, Field(ge=0)] = 1
    pacing: Pacing = Pacing.MEDIUM

    # Conflict
    conflict: ConflictInfo = Field(default_factory=ConflictInfo)

    # Emotion & payoff
    emotion: EmotionInfo = Field(default_factory=EmotionInfo)

    # Suspense & information
    suspense: SuspenseInfo = Field(default_factory=SuspenseInfo)

    # State changes
    state_changes: StateChanges = Field(default_factory=StateChanges)

    # Foreshadowing
    foreshadowing: ForeshadowInfo = Field(default_factory=ForeshadowInfo)

    # Text statistics
    text_stats: TextStats = Field(default_factory=TextStats)

    # Summary
    chapter_summary: str = ""

    model_config = {"json_schema_extra": {"title": "StoryGene", "version": 1}}


# === Schema registry for version upgrade support ===

SCHEMA_VERSIONS: dict[int, type[BaseModel]] = {
    1: StoryGeneV1,
}

# Current schema alias
StoryGene = StoryGeneV1


def get_schema_class(version: int = SCHEMA_VERSION) -> type[BaseModel]:
    """Get schema class by version. Raises ValueError for unknown versions."""
    cls = SCHEMA_VERSIONS.get(version)
    if cls is None:
        raise ValueError(f"Unknown StoryGene schema version: {version}. Available: {list(SCHEMA_VERSIONS)}")
    return cls


def get_json_schema(version: int = SCHEMA_VERSION) -> dict[str, Any]:
    """Export JSON Schema for the given version."""
    return get_schema_class(version).model_json_schema()
