"""Tests for StoryGene schema validation, Mock Provider, and JSON Schema export."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from app.llm.mock_provider import MOCK_STORY_GENE, MockLLMProvider
from app.schemas.story_gene import (
    SCHEMA_VERSION,
    ChapterFunction,
    ConflictType,
    Emotion,
    Genre,
    HookType,
    Pacing,
    PayoffType,
    PointOfView,
    ReversalType,
    StoryGene,
    StoryGeneV1,
    get_json_schema,
    get_schema_class,
)

# === Schema Validation: Valid Data ===


def test_valid_minimal_gene():
    """Minimal valid StoryGene with all defaults."""
    gene = StoryGene()
    assert gene.schema_version == SCHEMA_VERSION
    assert gene.genre == Genre.OTHER
    assert gene.confidence == 0.8
    assert gene.pacing == Pacing.MEDIUM


def test_valid_full_gene():
    """Full valid StoryGene with all fields populated."""
    gene = StoryGene.model_validate(MOCK_STORY_GENE)
    assert gene.schema_version == 1
    assert gene.genre == Genre.XUANHUAN
    assert gene.chapter_function == ChapterFunction.RISING
    assert gene.conflict.conflict_type == ConflictType.PERSON_VS_PERSON
    assert gene.emotion.emotional_start == Emotion.ANTICIPATION
    assert gene.emotion.payoff_type == PayoffType.POWER_DISPLAY
    assert gene.emotion.reversal_type == ReversalType.POWER
    assert gene.suspense.hook_type == HookType.CLIFFHANGER
    assert gene.suspense.hook_intensity == 9
    assert len(gene.state_changes.power_changes) == 1
    assert len(gene.state_changes.relationship_changes) == 1
    assert len(gene.foreshadowing.planted) == 1
    assert gene.text_stats.dialogue_ratio == 0.35
    assert gene.confidence == 0.85
    assert "升级流" in gene.subgenre


def test_valid_opening_chapter():
    """Opening chapter with low action."""
    gene = StoryGene(
        genre=Genre.FANTASY,
        chapter_function=ChapterFunction.OPENING,
        point_of_view=PointOfView.FIRST,
        pacing=Pacing.SLOW,
        scene_count=1,
        emotion={"emotional_start": "calm", "emotional_end": "anticipation"},
        text_stats={"dialogue_ratio": 0.5, "action_density": 0.1},
    )
    assert gene.chapter_function == ChapterFunction.OPENING
    assert gene.pacing == Pacing.SLOW


def test_valid_climax_chapter():
    """Climax chapter with high intensity."""
    gene = StoryGene(
        genre=Genre.XIANXIA,
        chapter_function=ChapterFunction.CLIMAX,
        pacing=Pacing.VERY_FAST,
        scene_count=5,
        emotion={
            "emotional_start": "tension",
            "emotional_end": "joy",
            "suppression_intensity": 10,
            "payoff_type": "face_slapping",
            "payoff_intensity": 10,
            "reversal_type": "power",
            "reversal_intensity": 9,
        },
        suspense={"hook_type": "cliffhanger", "hook_intensity": 10},
    )
    assert gene.emotion.suppression_intensity == 10
    assert gene.emotion.payoff_intensity == 10


def test_valid_transition_chapter():
    """Transition chapter with no conflict."""
    gene = StoryGene(
        chapter_function=ChapterFunction.TRANSITION,
        pacing=Pacing.VERY_SLOW,
        conflict={"conflict_type": "none"},
        emotion={"payoff_type": "none", "reversal_type": "none"},
        suspense={"suspense_type": "none", "hook_type": "none"},
    )
    assert gene.conflict.conflict_type == ConflictType.NONE


# === Schema Validation: Invalid Data ===


def test_invalid_intensity_too_high():
    """Intensity > 10 should be rejected."""
    with pytest.raises(ValidationError) as exc_info:
        StoryGene(emotion={"payoff_intensity": 11})
    errors = exc_info.value.errors()
    assert any("payoff_intensity" in str(e) for e in errors)


def test_invalid_intensity_negative():
    """Negative intensity should be rejected."""
    with pytest.raises(ValidationError) as exc_info:
        StoryGene(emotion={"suppression_intensity": -1})
    errors = exc_info.value.errors()
    assert any("suppression_intensity" in str(e) for e in errors)


def test_invalid_ratio_above_one():
    """Ratio > 1.0 should be rejected."""
    with pytest.raises(ValidationError) as exc_info:
        StoryGene(text_stats={"dialogue_ratio": 1.5})
    errors = exc_info.value.errors()
    assert any("dialogue_ratio" in str(e) for e in errors)


def test_invalid_ratio_negative():
    """Negative ratio should be rejected."""
    with pytest.raises(ValidationError) as exc_info:
        StoryGene(text_stats={"action_density": -0.1})
    errors = exc_info.value.errors()
    assert any("action_density" in str(e) for e in errors)


def test_invalid_enum_genre():
    """Invalid genre enum value should be rejected."""
    with pytest.raises(ValidationError) as exc_info:
        StoryGene(genre="nonexistent_genre")
    errors = exc_info.value.errors()
    assert any("genre" in str(e) for e in errors)


def test_invalid_enum_pacing():
    """Invalid pacing value should be rejected."""
    with pytest.raises(ValidationError) as exc_info:
        StoryGene(pacing="ultra_fast")
    errors = exc_info.value.errors()
    assert any("pacing" in str(e) for e in errors)


def test_invalid_enum_conflict_type():
    """Invalid conflict type should be rejected."""
    with pytest.raises(ValidationError) as exc_info:
        StoryGene(conflict={"conflict_type": "person_vs_dragon"})
    errors = exc_info.value.errors()
    assert any("conflict_type" in str(e) for e in errors)


def test_invalid_confidence_above_one():
    """Confidence > 1.0 should be rejected."""
    with pytest.raises(ValidationError):
        StoryGene(confidence=1.5)


def test_invalid_confidence_negative():
    """Negative confidence should be rejected."""
    with pytest.raises(ValidationError):
        StoryGene(confidence=-0.1)


def test_invalid_scene_count_negative():
    """Negative scene count should be rejected."""
    with pytest.raises(ValidationError):
        StoryGene(scene_count=-1)


# === Enum Completeness ===


def test_all_genres_valid():
    """All genre enum values should be accepted."""
    for g in Genre:
        gene = StoryGene(genre=g)
        assert gene.genre == g


def test_all_chapter_functions_valid():
    """All chapter function enum values should be accepted."""
    for cf in ChapterFunction:
        gene = StoryGene(chapter_function=cf)
        assert gene.chapter_function == cf


def test_all_pacings_valid():
    """All pacing enum values should be accepted."""
    for p in Pacing:
        gene = StoryGene(pacing=p)
        assert gene.pacing == p


def test_all_emotions_valid():
    """All emotion enum values should be accepted."""
    for e in Emotion:
        gene = StoryGene(emotion={"emotional_start": e, "emotional_end": e})
        assert gene.emotion.emotional_start == e


# === Mock Provider ===


@pytest.mark.asyncio
async def test_mock_returns_valid_story_gene():
    """Mock Provider should return a valid StoryGene when asked for structured output."""
    provider = MockLLMProvider(simulate_latency_ms=0)
    schema = StoryGene.model_json_schema()

    response = await provider.structured_output(
        messages=[{"role": "user", "content": "分析这个章节"}],
        schema=schema,
    )

    gene = StoryGene.model_validate_json(response.content)
    assert gene.schema_version == 1
    assert gene.genre in Genre
    assert 0 <= gene.confidence <= 1


@pytest.mark.asyncio
async def test_mock_story_gene_has_required_sections():
    """Mock StoryGene should have all major sections populated."""
    provider = MockLLMProvider(simulate_latency_ms=0)
    schema = StoryGene.model_json_schema()
    response = await provider.structured_output(messages=[{"role": "user", "content": "test"}], schema=schema)
    gene = StoryGene.model_validate_json(response.content)

    assert gene.conflict.protagonist_goal != ""
    assert gene.emotion.emotional_curve != ""
    assert gene.chapter_summary != ""
    assert gene.text_stats.dialogue_ratio > 0
    assert len(gene.state_changes.power_changes) > 0 or len(gene.state_changes.relationship_changes) > 0


# === JSON Schema Export ===


def test_json_schema_export():
    """get_json_schema should return valid JSON Schema."""
    schema = get_json_schema()
    assert schema["title"] == "StoryGene"
    assert schema["version"] == 1
    assert "properties" in schema
    assert "conflict" in schema["properties"]
    assert "emotion" in schema["properties"]
    assert "suspense" in schema["properties"]
    assert "state_changes" in schema["properties"]
    assert "foreshadowing" in schema["properties"]
    assert "text_stats" in schema["properties"]


def test_json_schema_has_enum_constraints():
    """JSON Schema should include enum constraints for constrained fields."""
    schema = get_json_schema()
    # Check genre enum
    genre_prop = schema["properties"]["genre"]
    assert "enum" in genre_prop or "$ref" in genre_prop


def test_json_schema_roundtrip():
    """Data validated through schema should produce valid JSON."""
    gene = StoryGene.model_validate(MOCK_STORY_GENE)
    json_str = gene.model_dump_json()
    restored = StoryGene.model_validate_json(json_str)
    assert restored.schema_version == gene.schema_version
    assert restored.genre == gene.genre
    assert restored.conflict.conflict_type == gene.conflict.conflict_type


# === Schema Version Registry ===


def test_get_schema_class_v1():
    """Should return StoryGeneV1 for version 1."""
    cls = get_schema_class(1)
    assert cls is StoryGeneV1


def test_get_schema_class_unknown():
    """Should raise ValueError for unknown version."""
    with pytest.raises(ValueError, match="Unknown"):
        get_schema_class(999)


def test_schema_version_default():
    """schema_version should default to SCHEMA_VERSION."""
    gene = StoryGene()
    assert gene.schema_version == SCHEMA_VERSION
    gene2 = StoryGene(schema_version=1)
    assert gene2.schema_version == 1


# === Serialization ===


def test_model_dump_json():
    """model_dump_json should produce valid JSON."""
    gene = StoryGene.model_validate(MOCK_STORY_GENE)
    json_str = gene.model_dump_json()
    data = json.loads(json_str)
    assert data["schema_version"] == 1
    assert isinstance(data["conflict"], dict)
    assert isinstance(data["state_changes"]["power_changes"], list)


def test_model_dump_exclude_defaults():
    """model_dump with exclude_defaults should omit unset fields."""
    gene = StoryGene()
    data = gene.model_dump(exclude_defaults=True)
    # Minimal gene should have very few top-level keys
    assert "genre" not in data  # default is "other"
    # All top-level keys should be from explicitly set fields or required
    # schema_version has a default so it's also excluded
    assert len(data) <= 2  # at most schema_version and maybe one other
