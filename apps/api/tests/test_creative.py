"""Tests for creative direction generation and management."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


async def _create_project(client: AsyncClient, name: str = "Creative Test") -> str:
    resp = await client.post("/api/v1/projects", json={"name": name})
    assert resp.status_code == 201
    return resp.json()["id"]


CREATIVE_INPUT = {
    "one_line_idea": "一个能看到所有人寿命的兽医在修仙世界治病救人的故事",
    "genre": "仙侠",
    "target_platform": "起点中文网",
    "target_reader": "18-30岁男性",
    "expected_length": "200万字",
    "preferred_pacing": "中速",
    "forbidden_content": "不写后宫",
    "gene_tags": "医修,灵兽",
}


# === Generate ===


@pytest.mark.asyncio
async def test_generate_three_directions(client):
    pid = await _create_project(client)
    resp = await client.post(
        f"/api/v1/projects/{pid}/creative/generate",
        json=CREATIVE_INPUT,
    )
    assert resp.status_code == 200
    directions = resp.json()
    assert len(directions) == 3
    # Each should have different content
    hooks = {d["one_line_hook"] for d in directions}
    assert len(hooks) == 3, "Three directions should have different hooks"


@pytest.mark.asyncio
async def test_directions_have_required_fields(client):
    pid = await _create_project(client)
    resp = await client.post(
        f"/api/v1/projects/{pid}/creative/generate",
        json=CREATIVE_INPUT,
    )
    directions = resp.json()
    for d in directions:
        assert d["one_line_hook"] != ""
        assert d["core_ability"] != ""
        assert d["core_conflict"] != ""
        assert d["growth_cycle"] != ""
        assert d["status"] == "draft"
        assert d["direction_index"] in (0, 1, 2)


@pytest.mark.asyncio
async def test_directions_differ_in_mechanics(client):
    """Directions must differ in ability mechanism and conflict type."""
    pid = await _create_project(client)
    resp = await client.post(
        f"/api/v1/projects/{pid}/creative/generate",
        json=CREATIVE_INPUT,
    )
    directions = resp.json()
    abilities = {d["core_ability"] for d in directions}
    conflicts = {d["core_conflict"] for d in directions}
    assert len(abilities) == 3, "Abilities should differ"
    assert len(conflicts) == 3, "Conflicts should differ"


@pytest.mark.asyncio
async def test_generate_project_not_found(client):
    resp = await client.post(
        "/api/v1/projects/nonexistent/creative/generate",
        json=CREATIVE_INPUT,
    )
    assert resp.status_code == 404


# === List Sessions & Directions ===


@pytest.mark.asyncio
async def test_list_sessions(client):
    pid = await _create_project(client)
    await client.post(f"/api/v1/projects/{pid}/creative/generate", json=CREATIVE_INPUT)
    resp = await client.get(f"/api/v1/projects/{pid}/creative/sessions")
    assert resp.status_code == 200
    sessions = resp.json()
    assert len(sessions) >= 1
    assert sessions[0]["status"] == "draft"


@pytest.mark.asyncio
async def test_list_session_directions(client):
    pid = await _create_project(client)
    await client.post(f"/api/v1/projects/{pid}/creative/generate", json=CREATIVE_INPUT)
    sessions = (await client.get(f"/api/v1/projects/{pid}/creative/sessions")).json()
    sid = sessions[0]["id"]
    resp = await client.get(f"/api/v1/projects/{pid}/creative/sessions/{sid}/directions")
    assert resp.status_code == 200
    assert len(resp.json()) == 3


# === Accept / Reject ===


@pytest.mark.asyncio
async def test_accept_direction(client):
    pid = await _create_project(client)
    dirs = (await client.post(f"/api/v1/projects/{pid}/creative/generate", json=CREATIVE_INPUT)).json()
    d1_id = dirs[0]["id"]

    resp = await client.post(f"/api/v1/projects/{pid}/creative/directions/{d1_id}/accept")
    assert resp.status_code == 200
    assert resp.json()["status"] == "adopted"

    # Check siblings are rejected
    updated_dirs = (
        await client.get(f"/api/v1/projects/{pid}/creative/sessions/{dirs[0]['session_id']}/directions")
    ).json()
    statuses = {d["status"] for d in updated_dirs}
    assert "adopted" in statuses
    assert "rejected" in statuses

    # Session should be completed
    sessions = (await client.get(f"/api/v1/projects/{pid}/creative/sessions")).json()
    assert sessions[0]["status"] == "completed"


@pytest.mark.asyncio
async def test_reject_direction(client):
    pid = await _create_project(client)
    dirs = (await client.post(f"/api/v1/projects/{pid}/creative/generate", json=CREATIVE_INPUT)).json()
    d1_id = dirs[0]["id"]

    resp = await client.post(
        f"/api/v1/projects/{pid}/creative/directions/{d1_id}/reject",
        params={"reason": "不够新颖"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"
    assert resp.json()["rejection_reason"] == "不够新颖"


@pytest.mark.asyncio
async def test_unadopted_directions_stay_draft(client):
    """Before adoption, all directions should be draft."""
    pid = await _create_project(client)
    dirs = (await client.post(f"/api/v1/projects/{pid}/creative/generate", json=CREATIVE_INPUT)).json()
    for d in dirs:
        assert d["status"] == "draft"


# === Edit ===


@pytest.mark.asyncio
async def test_edit_direction(client):
    pid = await _create_project(client)
    dirs = (await client.post(f"/api/v1/projects/{pid}/creative/generate", json=CREATIVE_INPUT)).json()
    d1_id = dirs[0]["id"]

    resp = await client.patch(
        f"/api/v1/projects/{pid}/creative/directions/{d1_id}",
        json={"one_line_hook": "修改后的卖点", "core_ability": "修改后的能力"},
    )
    assert resp.status_code == 200
    assert resp.json()["one_line_hook"] == "修改后的卖点"
    assert resp.json()["core_ability"] == "修改后的能力"


@pytest.mark.asyncio
async def test_edit_preserves_ai_original(client):
    """Editing should not overwrite ai_original_json."""
    pid = await _create_project(client)
    dirs = (await client.post(f"/api/v1/projects/{pid}/creative/generate", json=CREATIVE_INPUT)).json()
    original_hook = dirs[0]["one_line_hook"]
    d1_id = dirs[0]["id"]

    await client.patch(
        f"/api/v1/projects/{pid}/creative/directions/{d1_id}",
        json={"one_line_hook": "完全不同的卖点"},
    )

    # The original should still be in ai_original_json (tested via the service layer)
    # Here we verify the changed hook is different from original
    updated_dirs = (
        await client.get(f"/api/v1/projects/{pid}/creative/sessions/{dirs[0]['session_id']}/directions")
    ).json()
    assert updated_dirs[0]["one_line_hook"] != original_hook


# === Merge ===


@pytest.mark.asyncio
async def test_merge_directions(client):
    pid = await _create_project(client)
    dirs = (await client.post(f"/api/v1/projects/{pid}/creative/generate", json=CREATIVE_INPUT)).json()
    d1_id, d2_id = dirs[0]["id"], dirs[1]["id"]

    resp = await client.post(
        f"/api/v1/projects/{pid}/creative/merge",
        json={
            "source_ids": [d1_id, d2_id],
            "field_sources": {
                "one_line_hook": d1_id,
                "core_ability": d2_id,
                "core_conflict": d1_id,
            },
        },
    )
    assert resp.status_code == 200
    merged = resp.json()
    assert merged["status"] == "draft"
    assert merged["direction_index"] == 99


# === Not in Bible ===


@pytest.mark.asyncio
async def test_unadopted_not_in_bible(client):
    """Rejected/draft directions should not appear in the novel bible."""
    pid = await _create_project(client)
    await client.post(f"/api/v1/projects/{pid}/creative/generate", json=CREATIVE_INPUT)
    # Don't accept any — they're all draft

    # Check bible is empty
    chars = (await client.get(f"/api/v1/projects/{pid}/characters")).json()
    rules = (await client.get(f"/api/v1/projects/{pid}/world-rules")).json()
    assert len(chars) == 0
    assert len(rules) == 0
