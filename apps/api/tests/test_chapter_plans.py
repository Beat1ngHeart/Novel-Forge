"""Tests for chapter plan generation, editing, adoption, merge."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


async def _setup_rhythm(client: AsyncClient) -> tuple[str, str]:
    """Setup: project + direction + synopsis + volume + rhythm."""
    pid = (await client.post("/api/v1/projects", json={"name": "Plan Test"})).json()["id"]
    dirs = (
        await client.post(
            f"/api/v1/projects/{pid}/creative/generate",
            json={"one_line_idea": "一个炼器师在末法时代重建文明的故事"},
        )
    ).json()
    did = dirs[0]["id"]
    await client.post(f"/api/v1/projects/{pid}/creative/directions/{did}/accept")
    syn = (await client.post(f"/api/v1/projects/{pid}/synopses/generate", json={"direction_id": did})).json()
    await client.post(f"/api/v1/projects/{pid}/synopses/{syn['id']}/adopt")
    vols = (await client.post(f"/api/v1/projects/{pid}/volumes/generate", json={"synopsis_id": syn["id"]})).json()
    vid = vols[0]["id"]
    await client.post(f"/api/v1/projects/{pid}/volumes/{vid}/adopt")
    rhythms = (
        await client.post(
            f"/api/v1/projects/{pid}/rhythms/generate",
            json={"volume_id": vid, "chapter_count": 3},
        )
    ).json()
    rid = rhythms[0]["id"]
    return pid, rid


# === Generate ===


@pytest.mark.asyncio
async def test_generate_three_plans(client):
    pid, rid = await _setup_rhythm(client)
    resp = await client.post(
        f"/api/v1/projects/{pid}/chapter-plans/generate",
        json={"rhythm_id": rid},
    )
    assert resp.status_code == 200
    plans = resp.json()
    assert len(plans) == 3
    # Each plan should have different focus
    goals = {p["chapter_goal"] for p in plans}
    assert len(goals) == 3
    scenes = {p["scenes"] for p in plans}
    assert len(scenes) == 3


@pytest.mark.asyncio
async def test_plans_have_required_fields(client):
    pid, rid = await _setup_rhythm(client)
    plans = (await client.post(f"/api/v1/projects/{pid}/chapter-plans/generate", json={"rhythm_id": rid})).json()
    for p in plans:
        assert p["chapter_goal"] != ""
        assert p["characters"] != ""
        assert p["scenes"] != ""
        assert p["obstacle"] != ""
        assert p["turning_point"] != ""
        assert p["emotion_curve"] != ""
        assert p["chapter_hook"] != ""
        assert p["repetition_risk"] != ""
        assert p["status"] == "draft"
        assert p["rhythm_id"] == rid


@pytest.mark.asyncio
async def test_plans_differ_in_event_structure(client):
    pid, rid = await _setup_rhythm(client)
    plans = (await client.post(f"/api/v1/projects/{pid}/chapter-plans/generate", json={"rhythm_id": rid})).json()
    obstacles = {p["obstacle"] for p in plans}
    turning_points = {p["turning_point"] for p in plans}
    assert len(obstacles) == 3
    assert len(turning_points) == 3


# === List ===


@pytest.mark.asyncio
async def test_list_plans(client):
    pid, rid = await _setup_rhythm(client)
    await client.post(f"/api/v1/projects/{pid}/chapter-plans/generate", json={"rhythm_id": rid})
    resp = await client.get(f"/api/v1/projects/{pid}/chapter-plans?rhythm_id={rid}")
    assert resp.status_code == 200
    assert len(resp.json()) == 3


# === Edit ===


@pytest.mark.asyncio
async def test_edit_plan(client):
    pid, rid = await _setup_rhythm(client)
    plans = (await client.post(f"/api/v1/projects/{pid}/chapter-plans/generate", json={"rhythm_id": rid})).json()
    pid_plan = plans[0]["id"]
    resp = await client.patch(
        f"/api/v1/projects/{pid}/chapter-plans/{pid_plan}",
        json={"chapter_goal": "自定义目标", "obstacle": "自定义阻碍"},
    )
    assert resp.status_code == 200
    assert resp.json()["chapter_goal"] == "自定义目标"


@pytest.mark.asyncio
async def test_edit_preserves_ai_original(client):
    pid, rid = await _setup_rhythm(client)
    plans = (await client.post(f"/api/v1/projects/{pid}/chapter-plans/generate", json={"rhythm_id": rid})).json()
    original_goal = plans[0]["chapter_goal"]
    pid_plan = plans[0]["id"]
    await client.patch(f"/api/v1/projects/{pid}/chapter-plans/{pid_plan}", json={"chapter_goal": "新目标"})
    import json

    updated = (await client.get(f"/api/v1/projects/{pid}/chapter-plans/{pid_plan}")).json()
    ai_original = json.loads(updated["ai_original_json"])
    assert ai_original["chapter_goal"] == original_goal


# === Adopt / Reject ===


@pytest.mark.asyncio
async def test_adopt_rejects_siblings(client):
    pid, rid = await _setup_rhythm(client)
    plans = (await client.post(f"/api/v1/projects/{pid}/chapter-plans/generate", json={"rhythm_id": rid})).json()
    assert len(plans) == 3
    # Adopt first
    await client.post(f"/api/v1/projects/{pid}/chapter-plans/{plans[0]['id']}/adopt")
    # Check siblings are rejected
    all_plans = (await client.get(f"/api/v1/projects/{pid}/chapter-plans?rhythm_id={rid}")).json()
    statuses = {p["status"] for p in all_plans}
    assert "adopted" in statuses
    assert "rejected" in statuses


@pytest.mark.asyncio
async def test_adopted_plan_has_flag(client):
    pid, rid = await _setup_rhythm(client)
    plans = (await client.post(f"/api/v1/projects/{pid}/chapter-plans/generate", json={"rhythm_id": rid})).json()
    resp = await client.post(f"/api/v1/projects/{pid}/chapter-plans/{plans[0]['id']}/adopt")
    assert resp.json()["is_adopted"] is True


# === Regenerate ===


@pytest.mark.asyncio
async def test_regenerate_single(client):
    pid, rid = await _setup_rhythm(client)
    plans = (await client.post(f"/api/v1/projects/{pid}/chapter-plans/generate", json={"rhythm_id": rid})).json()
    pid_plan = plans[0]["id"]
    await client.patch(f"/api/v1/projects/{pid}/chapter-plans/{pid_plan}", json={"chapter_goal": "自定义"})
    resp = await client.post(f"/api/v1/projects/{pid}/chapter-plans/{pid_plan}/regenerate")
    assert resp.status_code == 200
    assert resp.json()["status"] == "draft"


@pytest.mark.asyncio
async def test_regenerate_does_not_affect_others(client):
    pid, rid = await _setup_rhythm(client)
    plans = (await client.post(f"/api/v1/projects/{pid}/chapter-plans/generate", json={"rhythm_id": rid})).json()
    await client.patch(f"/api/v1/projects/{pid}/chapter-plans/{plans[1]['id']}", json={"chapter_goal": "保留"})
    await client.post(f"/api/v1/projects/{pid}/chapter-plans/{plans[0]['id']}/regenerate")
    p2 = (await client.get(f"/api/v1/projects/{pid}/chapter-plans/{plans[1]['id']}")).json()
    assert p2["chapter_goal"] == "保留"


# === Merge ===


@pytest.mark.asyncio
async def test_merge_plans(client):
    pid, rid = await _setup_rhythm(client)
    plans = (await client.post(f"/api/v1/projects/{pid}/chapter-plans/generate", json={"rhythm_id": rid})).json()
    p1, p2 = plans[0]["id"], plans[1]["id"]
    resp = await client.post(
        f"/api/v1/projects/{pid}/chapter-plans/merge",
        json={
            "source_ids": [p1, p2],
            "field_sources": {
                "chapter_goal": p1,
                "scenes": p2,
                "obstacle": p1,
            },
        },
    )
    assert resp.status_code == 200
    merged = resp.json()
    assert merged["status"] == "draft"
    assert merged["chapter_goal"] == plans[0]["chapter_goal"]
    assert merged["scenes"] == plans[1]["scenes"]


# === Error cases ===


@pytest.mark.asyncio
async def test_plan_not_found(client):
    pid, _ = await _setup_rhythm(client)
    resp = await client.get(f"/api/v1/projects/{pid}/chapter-plans/nonexistent")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_reject_plan(client):
    pid, rid = await _setup_rhythm(client)
    plans = (await client.post(f"/api/v1/projects/{pid}/chapter-plans/generate", json={"rhythm_id": rid})).json()
    resp = await client.post(f"/api/v1/projects/{pid}/chapter-plans/{plans[0]['id']}/reject")
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"
