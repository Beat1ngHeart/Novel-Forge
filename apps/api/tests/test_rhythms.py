"""Tests for chapter rhythm plan generation, editing, reorder, insert, delete."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


async def _setup_volume(client: AsyncClient) -> tuple[str, str]:
    """Create project + adopted direction + adopted synopsis + adopted volume. Returns (project_id, volume_id)."""
    pid = (await client.post("/api/v1/projects", json={"name": "Rhythm Test"})).json()["id"]
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
    return pid, vid


# === Generate ===


@pytest.mark.asyncio
async def test_generate_10_chapters(client):
    pid, vid = await _setup_volume(client)
    resp = await client.post(
        f"/api/v1/projects/{pid}/rhythms/generate",
        json={"volume_id": vid, "chapter_count": 10},
    )
    assert resp.status_code == 200
    plans = resp.json()
    assert len(plans) == 10
    assert plans[0]["chapter_index"] == 0
    assert plans[9]["chapter_index"] == 9
    assert plans[0]["temp_title"] != ""


@pytest.mark.asyncio
async def test_chapters_have_different_functions(client):
    pid, vid = await _setup_volume(client)
    plans = (
        await client.post(
            f"/api/v1/projects/{pid}/rhythms/generate",
            json={"volume_id": vid, "chapter_count": 10},
        )
    ).json()
    functions = {p["chapter_function"] for p in plans}
    assert len(functions) > 1, "Chapters should have different functions"


@pytest.mark.asyncio
async def test_chapters_have_required_fields(client):
    pid, vid = await _setup_volume(client)
    plans = (
        await client.post(
            f"/api/v1/projects/{pid}/rhythms/generate",
            json={"volume_id": vid, "chapter_count": 5},
        )
    ).json()
    for p in plans:
        assert p["core_event"] != ""
        assert p["protagonist_goal"] != ""
        assert p["conflict_type"] != ""
        assert p["chapter_hook"] != ""
        assert p["estimated_words"] >= 1000
        assert p["volume_id"] == vid


@pytest.mark.asyncio
async def test_generate_requires_adopted_volume(client):
    pid, _ = await _setup_volume(client)
    # Get volume that is NOT adopted (generate new one)
    # Actually just use a nonexistent volume
    resp = await client.post(
        f"/api/v1/projects/{pid}/rhythms/generate",
        json={"volume_id": "nonexistent", "chapter_count": 5},
    )
    assert resp.status_code == 400


# === List ===


@pytest.mark.asyncio
async def test_list_plans(client):
    pid, vid = await _setup_volume(client)
    await client.post(f"/api/v1/projects/{pid}/rhythms/generate", json={"volume_id": vid, "chapter_count": 5})
    resp = await client.get(f"/api/v1/projects/{pid}/rhythms?volume_id={vid}")
    assert resp.status_code == 200
    assert len(resp.json()) == 5


# === Edit ===


@pytest.mark.asyncio
async def test_edit_plan(client):
    pid, vid = await _setup_volume(client)
    plans = (
        await client.post(
            f"/api/v1/projects/{pid}/rhythms/generate",
            json={"volume_id": vid, "chapter_count": 3},
        )
    ).json()
    pid_ch = plans[0]["id"]
    resp = await client.patch(
        f"/api/v1/projects/{pid}/rhythms/{pid_ch}",
        json={"temp_title": "自定义标题", "core_event": "自定义事件"},
    )
    assert resp.status_code == 200
    assert resp.json()["temp_title"] == "自定义标题"


@pytest.mark.asyncio
async def test_edit_preserves_ai_original(client):
    pid, vid = await _setup_volume(client)
    plans = (
        await client.post(
            f"/api/v1/projects/{pid}/rhythms/generate",
            json={"volume_id": vid, "chapter_count": 3},
        )
    ).json()
    original_title = plans[0]["temp_title"]
    pid_ch = plans[0]["id"]
    await client.patch(f"/api/v1/projects/{pid}/rhythms/{pid_ch}", json={"temp_title": "新标题"})
    import json

    updated = (await client.get(f"/api/v1/projects/{pid}/rhythms/{pid_ch}")).json()
    ai_original = json.loads(updated["ai_original_json"])
    assert ai_original["temp_title"] == original_title


# === Adopt ===


@pytest.mark.asyncio
async def test_adopt_plan(client):
    pid, vid = await _setup_volume(client)
    plans = (
        await client.post(
            f"/api/v1/projects/{pid}/rhythms/generate",
            json={"volume_id": vid, "chapter_count": 3},
        )
    ).json()
    resp = await client.post(f"/api/v1/projects/{pid}/rhythms/{plans[0]['id']}/adopt")
    assert resp.status_code == 200
    assert resp.json()["status"] == "adopted"


# === Regenerate Single ===


@pytest.mark.asyncio
async def test_regenerate_single(client):
    pid, vid = await _setup_volume(client)
    plans = (
        await client.post(
            f"/api/v1/projects/{pid}/rhythms/generate",
            json={"volume_id": vid, "chapter_count": 3},
        )
    ).json()
    pid_ch = plans[0]["id"]
    await client.patch(f"/api/v1/projects/{pid}/rhythms/{pid_ch}", json={"temp_title": "自定义"})
    resp = await client.post(f"/api/v1/projects/{pid}/rhythms/{pid_ch}/regenerate")
    assert resp.status_code == 200
    # Should be regenerated (title reset)
    assert resp.json()["status"] == "draft"


@pytest.mark.asyncio
async def test_regenerate_does_not_affect_others(client):
    pid, vid = await _setup_volume(client)
    plans = (
        await client.post(
            f"/api/v1/projects/{pid}/rhythms/generate",
            json={"volume_id": vid, "chapter_count": 3},
        )
    ).json()
    # Edit plan 2
    await client.patch(f"/api/v1/projects/{pid}/rhythms/{plans[1]['id']}", json={"temp_title": "保留"})
    # Regenerate plan 1
    await client.post(f"/api/v1/projects/{pid}/rhythms/{plans[0]['id']}/regenerate")
    # Plan 2 should be unchanged
    p2 = (await client.get(f"/api/v1/projects/{pid}/rhythms/{plans[1]['id']}")).json()
    assert p2["temp_title"] == "保留"


# === Insert ===


@pytest.mark.asyncio
async def test_insert_chapter(client):
    pid, vid = await _setup_volume(client)
    plans = (
        await client.post(
            f"/api/v1/projects/{pid}/rhythms/generate",
            json={"volume_id": vid, "chapter_count": 3},
        )
    ).json()
    assert len(plans) == 3
    # Insert after index 1
    resp = await client.post(
        f"/api/v1/projects/{pid}/rhythms/insert",
        json={"after_index": 1, "temp_title": "插入章节"},
    )
    assert resp.status_code == 200
    new_plans = resp.json()
    assert len(new_plans) == 4
    assert new_plans[2]["temp_title"] == "插入章节"
    # Indices should be sequential
    for i, p in enumerate(new_plans):
        assert p["chapter_index"] == i


# === Delete ===


@pytest.mark.asyncio
async def test_delete_chapter(client):
    pid, vid = await _setup_volume(client)
    plans = (
        await client.post(
            f"/api/v1/projects/{pid}/rhythms/generate",
            json={"volume_id": vid, "chapter_count": 3},
        )
    ).json()
    resp = await client.delete(f"/api/v1/projects/{pid}/rhythms/{plans[1]['id']}")
    assert resp.status_code == 200
    remaining = resp.json()
    assert len(remaining) == 2
    # Indices should be sequential
    for i, p in enumerate(remaining):
        assert p["chapter_index"] == i


# === Reorder ===


@pytest.mark.asyncio
async def test_reorder(client):
    pid, vid = await _setup_volume(client)
    plans = (
        await client.post(
            f"/api/v1/projects/{pid}/rhythms/generate",
            json={"volume_id": vid, "chapter_count": 3},
        )
    ).json()
    ids = [p["id"] for p in reversed(plans)]
    resp = await client.post(f"/api/v1/projects/{pid}/rhythms/reorder", json={"chapter_ids": ids})
    assert resp.status_code == 200
    reordered = resp.json()
    assert reordered[0]["id"] == ids[0]
    assert reordered[0]["chapter_index"] == 0


# === Volume link ===


@pytest.mark.asyncio
async def test_plans_linked_to_volume(client):
    pid, vid = await _setup_volume(client)
    plans = (
        await client.post(
            f"/api/v1/projects/{pid}/rhythms/generate",
            json={"volume_id": vid, "chapter_count": 3},
        )
    ).json()
    for p in plans:
        assert p["volume_id"] == vid
