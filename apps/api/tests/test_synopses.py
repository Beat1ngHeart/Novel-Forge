"""Tests for synopsis generation, editing, versioning, adopt, restore, diff."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


async def _setup_adopted_direction(client: AsyncClient) -> tuple[str, str]:
    pid = (await client.post("/api/v1/projects", json={"name": "Synopsis Test"})).json()["id"]
    dirs = (
        await client.post(
            f"/api/v1/projects/{pid}/creative/generate",
            json={"one_line_idea": "一个炼器师在末法时代重建文明的故事"},
        )
    ).json()
    did = dirs[0]["id"]
    await client.post(f"/api/v1/projects/{pid}/creative/directions/{did}/accept")
    return pid, did


# === Generate ===


@pytest.mark.asyncio
async def test_generate_synopsis(client):
    pid, did = await _setup_adopted_direction(client)
    resp = await client.post(
        f"/api/v1/projects/{pid}/synopses/generate",
        json={"direction_id": did},
    )
    assert resp.status_code == 200
    synopsis = resp.json()
    assert synopsis["version"] == 1
    assert synopsis["status"] == "draft"
    assert synopsis["is_current"] is False
    assert synopsis["one_liner"] != ""
    assert synopsis["core_conflict"] != ""
    assert synopsis["story_phases"] != ""
    assert synopsis["ending"] != ""
    assert synopsis["risk_warnings"] != ""


@pytest.mark.asyncio
async def test_generate_requires_adopted_direction(client):
    pid = (await client.post("/api/v1/projects", json={"name": "X"})).json()["id"]
    dirs = (
        await client.post(
            f"/api/v1/projects/{pid}/creative/generate",
            json={"one_line_idea": "一个炼器师的故事"},
        )
    ).json()
    resp = await client.post(
        f"/api/v1/projects/{pid}/synopses/generate",
        json={"direction_id": dirs[0]["id"]},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_generate_version_increments(client):
    pid, did = await _setup_adopted_direction(client)
    s1 = (await client.post(f"/api/v1/projects/{pid}/synopses/generate", json={"direction_id": did})).json()
    s2 = (await client.post(f"/api/v1/projects/{pid}/synopses/generate", json={"direction_id": did})).json()
    assert s1["version"] == 1
    assert s2["version"] == 2


# === List ===


@pytest.mark.asyncio
async def test_list_synopses(client):
    pid, did = await _setup_adopted_direction(client)
    await client.post(f"/api/v1/projects/{pid}/synopses/generate", json={"direction_id": did})
    await client.post(f"/api/v1/projects/{pid}/synopses/generate", json={"direction_id": did})
    resp = await client.get(f"/api/v1/projects/{pid}/synopses")
    assert resp.status_code == 200
    synopses = resp.json()
    assert len(synopses) == 2
    assert synopses[0]["version"] > synopses[1]["version"]  # newest first


# === Get ===


@pytest.mark.asyncio
async def test_get_synopsis(client):
    pid, did = await _setup_adopted_direction(client)
    s = (await client.post(f"/api/v1/projects/{pid}/synopses/generate", json={"direction_id": did})).json()
    resp = await client.get(f"/api/v1/projects/{pid}/synopses/{s['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == s["id"]


@pytest.mark.asyncio
async def test_get_current_empty(client):
    pid, _ = await _setup_adopted_direction(client)
    resp = await client.get(f"/api/v1/projects/{pid}/synopses/current")
    assert resp.status_code == 200
    assert resp.json() is None


# === Edit ===


@pytest.mark.asyncio
async def test_edit_synopsis(client):
    pid, did = await _setup_adopted_direction(client)
    s = (await client.post(f"/api/v1/projects/{pid}/synopses/generate", json={"direction_id": did})).json()
    resp = await client.patch(
        f"/api/v1/projects/{pid}/synopses/{s['id']}",
        json={"one_liner": "修改后的一句话故事", "ending": "新的结局"},
    )
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["one_liner"] == "修改后的一句话故事"
    assert updated["ending"] == "新的结局"


@pytest.mark.asyncio
async def test_edit_preserves_ai_original(client):
    pid, did = await _setup_adopted_direction(client)
    s = (await client.post(f"/api/v1/projects/{pid}/synopses/generate", json={"direction_id": did})).json()
    original_liner = s["one_liner"]
    await client.patch(f"/api/v1/projects/{pid}/synopses/{s['id']}", json={"one_liner": "完全不同的故事"})
    updated = (await client.get(f"/api/v1/projects/{pid}/synopses/{s['id']}")).json()
    # AI original should still be in ai_original_json
    import json

    ai_original = json.loads(updated["ai_original_json"])
    assert ai_original["one_liner"] == original_liner
    # But the current value should be changed
    assert updated["one_liner"] == "完全不同的故事"


@pytest.mark.asyncio
async def test_edit_records_human_edits(client):
    pid, did = await _setup_adopted_direction(client)
    s = (await client.post(f"/api/v1/projects/{pid}/synopses/generate", json={"direction_id": did})).json()
    await client.patch(f"/api/v1/projects/{pid}/synopses/{s['id']}", json={"one_liner": "v1"})
    await client.patch(f"/api/v1/projects/{pid}/synopses/{s['id']}", json={"one_liner": "v2"})
    updated = (await client.get(f"/api/v1/projects/{pid}/synopses/{s['id']}")).json()
    import json

    edits = json.loads(updated["human_edits_json"])
    assert len(edits) >= 2  # at least 2 edit records


# === Adopt ===


@pytest.mark.asyncio
async def test_adopt_synopsis(client):
    pid, did = await _setup_adopted_direction(client)
    s = (await client.post(f"/api/v1/projects/{pid}/synopses/generate", json={"direction_id": did})).json()
    assert s["status"] == "draft"
    assert s["is_current"] is False

    resp = await client.post(f"/api/v1/projects/{pid}/synopses/{s['id']}/adopt")
    assert resp.status_code == 200
    adopted = resp.json()
    assert adopted["status"] == "adopted"
    assert adopted["is_current"] is True

    # Should now be the current synopsis
    current = (await client.get(f"/api/v1/projects/{pid}/synopses/current")).json()
    assert current["id"] == s["id"]


@pytest.mark.asyncio
async def test_adopt_supersedes_previous(client):
    pid, did = await _setup_adopted_direction(client)
    s1 = (await client.post(f"/api/v1/projects/{pid}/synopses/generate", json={"direction_id": did})).json()
    s2 = (await client.post(f"/api/v1/projects/{pid}/synopses/generate", json={"direction_id": did})).json()

    await client.post(f"/api/v1/projects/{pid}/synopses/{s1['id']}/adopt")
    await client.post(f"/api/v1/projects/{pid}/synopses/{s2['id']}/adopt")

    current = (await client.get(f"/api/v1/projects/{pid}/synopses/current")).json()
    assert current["id"] == s2["id"]

    # s1 should be superseded
    s1_updated = (await client.get(f"/api/v1/projects/{pid}/synopses/{s1['id']}")).json()
    assert s1_updated["status"] == "superseded"
    assert s1_updated["is_current"] is False


# === Restore ===


@pytest.mark.asyncio
async def test_restore_synopsis(client):
    pid, did = await _setup_adopted_direction(client)
    s1 = (await client.post(f"/api/v1/projects/{pid}/synopses/generate", json={"direction_id": did})).json()
    s2 = (await client.post(f"/api/v1/projects/{pid}/synopses/generate", json={"direction_id": did})).json()

    await client.post(f"/api/v1/projects/{pid}/synopses/{s1['id']}/adopt")
    await client.post(f"/api/v1/projects/{pid}/synopses/{s2['id']}/adopt")

    # Restore s1
    resp = await client.post(f"/api/v1/projects/{pid}/synopses/{s1['id']}/restore")
    assert resp.status_code == 200
    restored = resp.json()
    assert restored["status"] == "adopted"
    assert restored["is_current"] is True

    # s2 should be superseded now
    s2_updated = (await client.get(f"/api/v1/projects/{pid}/synopses/{s2['id']}")).json()
    assert s2_updated["status"] == "superseded"


# === Diff ===


@pytest.mark.asyncio
async def test_diff_synopses(client):
    pid, did = await _setup_adopted_direction(client)
    s1 = (await client.post(f"/api/v1/projects/{pid}/synopses/generate", json={"direction_id": did})).json()
    s2_id = (await client.post(f"/api/v1/projects/{pid}/synopses/generate", json={"direction_id": did})).json()["id"]

    # Edit s2
    await client.patch(f"/api/v1/projects/{pid}/synopses/{s2_id}", json={"one_liner": "different"})

    resp = await client.get(
        f"/api/v1/projects/{pid}/synopses/{s1['id']}/diff",
        params={"compare_with": s2_id},
    )
    assert resp.status_code == 200
    diff = resp.json()
    assert diff["total_changes"] >= 1
    assert any(c["field"] == "one_liner" for c in diff["changed_fields"])


# === Only one current ===


@pytest.mark.asyncio
async def test_only_one_current_synopsis(client):
    pid, did = await _setup_adopted_direction(client)
    s1 = (await client.post(f"/api/v1/projects/{pid}/synopses/generate", json={"direction_id": did})).json()
    s2 = (await client.post(f"/api/v1/projects/{pid}/synopses/generate", json={"direction_id": did})).json()

    await client.post(f"/api/v1/projects/{pid}/synopses/{s1['id']}/adopt")
    await client.post(f"/api/v1/projects/{pid}/synopses/{s2['id']}/adopt")

    all_synopses = (await client.get(f"/api/v1/projects/{pid}/synopses")).json()
    current_count = sum(1 for s in all_synopses if s["is_current"])
    assert current_count == 1
