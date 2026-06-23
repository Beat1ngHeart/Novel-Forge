"""Tests for chapter analysis: trigger, result validation, history, rights check."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


SAMPLE_NOVEL = """第一章 初入江湖
青云山上，雾气缭绕。少年林辰背着一把长剑，站在山门前。
"从今日起，你便是青云派的弟子了。"一位白发老者说道。
林辰心中激动，他知道，自己的修炼之路正式开始了。

第二章 拜师学艺
入门三个月，林辰每日勤学苦练。
他发现自己的灵根竟然是罕见的雷属性。
"""


async def _setup(client: AsyncClient, content: str = SAMPLE_NOVEL, rights: str = "owned") -> tuple[str, str, str]:
    """Upload doc, parse chapters, return (doc_id, chapter_id, project_id)."""
    # Create project
    proj_resp = await client.post("/api/v1/projects", json={"name": "Test"})
    project_id = proj_resp.json()["id"]

    # Upload document
    doc_resp = await client.post(
        "/api/v1/documents",
        files={"file": ("novel.txt", content.encode(), "text/plain")},
        data={"project_id": project_id, "rights_status": rights},
    )
    doc_id = doc_resp.json()["id"]

    # Parse chapters
    await client.post(f"/api/v1/documents/{doc_id}/chapters/parse")
    chapters = (await client.get(f"/api/v1/documents/{doc_id}/chapters")).json()
    chapter_id = chapters[0]["id"]

    return doc_id, chapter_id, project_id


# === Trigger Analysis ===


@pytest.mark.asyncio
async def test_trigger_analysis(client):
    _doc_id, chapter_id, _proj_id = await _setup(client)
    resp = await client.post(f"/api/v1/chapters/{chapter_id}/analyses")
    assert resp.status_code == 201
    analysis = resp.json()
    assert analysis["status"] == "completed"
    assert analysis["chapter_id"] == chapter_id
    assert analysis["confidence"] > 0
    assert analysis["chapter_function"] != ""
    assert analysis["chapter_summary"] != ""
    assert analysis["provider"] == "mock"


@pytest.mark.asyncio
async def test_analysis_result_valid_schema(client):
    """The stored result_json must be valid StoryGene."""
    _doc_id, chapter_id, _proj_id = await _setup(client)

    # Trigger analysis
    resp = await client.post(f"/api/v1/chapters/{chapter_id}/analyses")
    analysis_id = resp.json()["id"]

    # Get structured result
    result_resp = await client.get(f"/api/v1/chapters/{chapter_id}/analyses/{analysis_id}/result")
    assert result_resp.status_code == 200
    result = result_resp.json()
    assert result["schema_version"] == 1
    assert result["genre"] != ""
    assert result["conflict"] != {}
    assert result["emotion"] != {}
    assert result["chapter_summary"] != ""


@pytest.mark.asyncio
async def test_analysis_with_prompt_version(client):
    _doc_id, chapter_id, _proj_id = await _setup(client)
    resp = await client.post(
        f"/api/v1/chapters/{chapter_id}/analyses",
        json={"prompt_version": "v2"},
    )
    assert resp.status_code == 201
    assert resp.json()["prompt_version"] == "v2"


# === Rights Check ===


@pytest.mark.asyncio
async def test_analysis_blocked_for_prohibited(client):
    _doc_id, chapter_id, _proj_id = await _setup(client, rights="prohibited")
    resp = await client.post(f"/api/v1/chapters/{chapter_id}/analyses")
    assert resp.status_code == 403
    assert "禁止" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_analysis_allowed_for_unknown(client):
    _doc_id, chapter_id, _proj_id = await _setup(client, rights="unknown")
    resp = await client.post(f"/api/v1/chapters/{chapter_id}/analyses")
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_analysis_allowed_for_owned(client):
    _doc_id, chapter_id, _proj_id = await _setup(client, rights="owned")
    resp = await client.post(f"/api/v1/chapters/{chapter_id}/analyses")
    assert resp.status_code == 201


# === History ===


@pytest.mark.asyncio
async def test_analysis_history(client):
    _doc_id, chapter_id, _proj_id = await _setup(client)

    # Run analysis twice
    await client.post(f"/api/v1/chapters/{chapter_id}/analyses")
    await client.post(f"/api/v1/chapters/{chapter_id}/analyses")

    # Check history
    resp = await client.get(f"/api/v1/chapters/{chapter_id}/analyses")
    assert resp.status_code == 200
    analyses = resp.json()
    assert len(analyses) == 2
    # Newest first
    assert analyses[0]["created_at"] >= analyses[1]["created_at"]


@pytest.mark.asyncio
async def test_analysis_history_preserves_old_results(client):
    """Re-analysis should not overwrite old results."""
    _doc_id, chapter_id, _proj_id = await _setup(client)

    resp1 = await client.post(f"/api/v1/chapters/{chapter_id}/analyses")
    id1 = resp1.json()["id"]

    resp2 = await client.post(f"/api/v1/chapters/{chapter_id}/analyses")
    id2 = resp2.json()["id"]

    assert id1 != id2

    # Both should still exist
    r1 = await client.get(f"/api/v1/chapters/{chapter_id}/analyses/{id1}")
    r2 = await client.get(f"/api/v1/chapters/{chapter_id}/analyses/{id2}")
    assert r1.status_code == 200
    assert r2.status_code == 200


@pytest.mark.asyncio
async def test_get_latest_analysis(client):
    _doc_id, chapter_id, _proj_id = await _setup(client)
    await client.post(f"/api/v1/chapters/{chapter_id}/analyses")
    resp = await client.get(f"/api/v1/chapters/{chapter_id}/analyses/latest")
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"


@pytest.mark.asyncio
async def test_get_latest_when_none(client):
    _doc_id, chapter_id, _proj_id = await _setup(client)
    resp = await client.get(f"/api/v1/chapters/{chapter_id}/analyses/latest")
    assert resp.status_code == 200
    assert resp.json() is None


# === Error Handling ===


@pytest.mark.asyncio
async def test_analysis_chapter_not_found(client):
    resp = await client.post("/api/v1/chapters/nonexistent/analyses")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_analysis_detail_not_found(client):
    _doc_id, chapter_id, _proj_id = await _setup(client)
    resp = await client.get(f"/api/v1/chapters/{chapter_id}/analyses/nonexistent")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_analysis_result_not_completed(client):
    """If analysis somehow has no result, result endpoint should fail gracefully."""
    _doc_id, chapter_id, _proj_id = await _setup(client)
    # Create analysis first
    resp = await client.post(f"/api/v1/chapters/{chapter_id}/analyses")
    analysis_id = resp.json()["id"]

    # Result should work since mock always succeeds
    result_resp = await client.get(f"/api/v1/chapters/{chapter_id}/analyses/{analysis_id}/result")
    assert result_resp.status_code == 200


# === LLM Call Logging ===


@pytest.mark.asyncio
async def test_analysis_creates_llm_call_log(client):
    _doc_id, chapter_id, _proj_id = await _setup(client)
    resp = await client.post(f"/api/v1/chapters/{chapter_id}/analyses")
    analysis = resp.json()
    assert analysis["llm_call_id"] != ""

    # Check the call log exists
    logs_resp = await client.get("/api/v1/providers/logs?limit=5")
    logs = logs_resp.json()
    matching = [entry for entry in logs if entry["id"] == analysis["llm_call_id"]]
    assert len(matching) == 1
    assert matching[0]["task_type"] == "story_gene_analysis"
    assert matching[0]["status"] == "success"


# === Chapter Content in Analysis ===


@pytest.mark.asyncio
async def test_analysis_result_has_conflict_info(client):
    _doc_id, chapter_id, _proj_id = await _setup(client)
    resp = await client.post(f"/api/v1/chapters/{chapter_id}/analyses")
    analysis_id = resp.json()["id"]
    result = (await client.get(f"/api/v1/chapters/{chapter_id}/analyses/{analysis_id}/result")).json()
    assert "protagonist_goal" in result["conflict"]
    assert "conflict_type" in result["conflict"]


@pytest.mark.asyncio
async def test_analysis_result_has_emotion_info(client):
    _doc_id, chapter_id, _proj_id = await _setup(client)
    resp = await client.post(f"/api/v1/chapters/{chapter_id}/analyses")
    analysis_id = resp.json()["id"]
    result = (await client.get(f"/api/v1/chapters/{chapter_id}/analyses/{analysis_id}/result")).json()
    assert "emotional_start" in result["emotion"]
    assert "payoff_type" in result["emotion"]


@pytest.mark.asyncio
async def test_analysis_result_has_suspense_info(client):
    _doc_id, chapter_id, _proj_id = await _setup(client)
    resp = await client.post(f"/api/v1/chapters/{chapter_id}/analyses")
    analysis_id = resp.json()["id"]
    result = (await client.get(f"/api/v1/chapters/{chapter_id}/analyses/{analysis_id}/result")).json()
    assert "hook_type" in result["suspense"]
    assert "suspense_type" in result["suspense"]


@pytest.mark.asyncio
async def test_analysis_result_has_state_changes(client):
    _doc_id, chapter_id, _proj_id = await _setup(client)
    resp = await client.post(f"/api/v1/chapters/{chapter_id}/analyses")
    analysis_id = resp.json()["id"]
    result = (await client.get(f"/api/v1/chapters/{chapter_id}/analyses/{analysis_id}/result")).json()
    assert "power_changes" in result["state_changes"]
    assert "relationship_changes" in result["state_changes"]


@pytest.mark.asyncio
async def test_analysis_result_has_foreshadowing(client):
    _doc_id, chapter_id, _proj_id = await _setup(client)
    resp = await client.post(f"/api/v1/chapters/{chapter_id}/analyses")
    analysis_id = resp.json()["id"]
    result = (await client.get(f"/api/v1/chapters/{chapter_id}/analyses/{analysis_id}/result")).json()
    assert "planted" in result["foreshadowing"]
    assert "fulfilled" in result["foreshadowing"]
