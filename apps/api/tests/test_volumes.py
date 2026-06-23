"""Tests for volume outline generation, editing, adoption, regeneration, reorder."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


async def _setup_with_synopsis(client: AsyncClient) -> tuple[str, str]:
    """Setup: project + adopted direction + adopted synopsis."""
    pid = (await client.post("/api/v1/projects", json={"name": "Volume Test"})).json()["id"]
    dirs = (
        await client.post(
            f"/api/v1/projects/{pid}/creative/generate",
            json={"one_line_idea": "一个炼器师在末法时代重建文明的故事"},
        )
    ).json()
    did = dirs[0]["id"]
    await client.post(f"/api/v1/projects/{pid}/creative/directions/{did}/accept")
    syn = (await client.post(f"/api/v1/projects/{pid}/synopses/generate", json={"direction_id": did})).json()
    sid = syn["id"]
    await client.post(f"/api/v1/projects/{pid}/synopses/{sid}/adopt")
    return pid, sid


# === Generate ===


@pytest.mark.asyncio
async def test_generate_all_volumes(client):
    pid, sid = await _setup_with_synopsis(client)
    resp = await client.post(f"/api/v1/projects/{pid}/volumes/generate", json={"synopsis_id": sid})
    assert resp.status_code == 200
    volumes = resp.json()
    assert len(volumes) == 3
    assert volumes[0]["volume_name"] != ""
    assert volumes[0]["volume_index"] == 0
    assert volumes[1]["volume_index"] == 1
    assert volumes[2]["volume_index"] == 2


@pytest.mark.asyncio
async def test_volumes_have_required_fields(client):
    pid, sid = await _setup_with_synopsis(client)
    volumes = (await client.post(f"/api/v1/projects/{pid}/volumes/generate", json={"synopsis_id": sid})).json()
    for v in volumes:
        assert v["volume_goal"] != ""
        assert v["core_conflict"] != ""
        assert v["start_state"] != ""
        assert v["end_state"] != ""
        assert v["estimated_chapters"] > 0
        assert v["estimated_words"] > 0
        assert v["synopsis_id"] == sid
        assert v["status"] == "draft"


@pytest.mark.asyncio
async def test_generate_requires_adopted_synopsis(client):
    pid = (await client.post("/api/v1/projects", json={"name": "X"})).json()["id"]
    # Generate synopsis but don't adopt
    dirs = (
        await client.post(
            f"/api/v1/projects/{pid}/creative/generate",
            json={"one_line_idea": "一个炼器师的故事"},
        )
    ).json()
    await client.post(f"/api/v1/projects/{pid}/creative/directions/{dirs[0]['id']}/accept")
    syn = (await client.post(f"/api/v1/projects/{pid}/synopses/generate", json={"direction_id": dirs[0]["id"]})).json()
    resp = await client.post(f"/api/v1/projects/{pid}/volumes/generate", json={"synopsis_id": syn["id"]})
    assert resp.status_code == 400


# === List ===


@pytest.mark.asyncio
async def test_list_volumes(client):
    pid, sid = await _setup_with_synopsis(client)
    await client.post(f"/api/v1/projects/{pid}/volumes/generate", json={"synopsis_id": sid})
    resp = await client.get(f"/api/v1/projects/{pid}/volumes")
    assert resp.status_code == 200
    assert len(resp.json()) == 3


@pytest.mark.asyncio
async def test_list_filter_by_synopsis(client):
    pid, sid = await _setup_with_synopsis(client)
    await client.post(f"/api/v1/projects/{pid}/volumes/generate", json={"synopsis_id": sid})
    resp = await client.get(f"/api/v1/projects/{pid}/volumes?synopsis_id={sid}")
    assert len(resp.json()) == 3


# === Edit ===


@pytest.mark.asyncio
async def test_edit_volume(client):
    pid, sid = await _setup_with_synopsis(client)
    volumes = (await client.post(f"/api/v1/projects/{pid}/volumes/generate", json={"synopsis_id": sid})).json()
    vid = volumes[0]["id"]
    resp = await client.patch(
        f"/api/v1/projects/{pid}/volumes/{vid}",
        json={"volume_name": "自定义卷名", "volume_goal": "自定义目标"},
    )
    assert resp.status_code == 200
    assert resp.json()["volume_name"] == "自定义卷名"
    assert resp.json()["volume_goal"] == "自定义目标"


@pytest.mark.asyncio
async def test_edit_preserves_ai_original(client):
    pid, sid = await _setup_with_synopsis(client)
    volumes = (await client.post(f"/api/v1/projects/{pid}/volumes/generate", json={"synopsis_id": sid})).json()
    original_name = volumes[0]["volume_name"]
    vid = volumes[0]["id"]
    await client.patch(f"/api/v1/projects/{pid}/volumes/{vid}", json={"volume_name": "新名字"})
    import json

    updated = (await client.get(f"/api/v1/projects/{pid}/volumes/{vid}")).json()
    ai_original = json.loads(updated["ai_original_json"])
    assert ai_original["volume_name"] == original_name


# === Adopt ===


@pytest.mark.asyncio
async def test_adopt_volume(client):
    pid, sid = await _setup_with_synopsis(client)
    volumes = (await client.post(f"/api/v1/projects/{pid}/volumes/generate", json={"synopsis_id": sid})).json()
    vid = volumes[0]["id"]
    resp = await client.post(f"/api/v1/projects/{pid}/volumes/{vid}/adopt")
    assert resp.status_code == 200
    assert resp.json()["status"] == "adopted"
    assert resp.json()["is_current"] is True


# === Regenerate Single Volume ===


@pytest.mark.asyncio
async def test_regenerate_single_volume(client):
    pid, sid = await _setup_with_synopsis(client)
    volumes = (await client.post(f"/api/v1/projects/{pid}/volumes/generate", json={"synopsis_id": sid})).json()
    assert len(volumes) == 3

    # Edit volume 2
    v2_id = volumes[1]["id"]
    await client.patch(f"/api/v1/projects/{pid}/volumes/{v2_id}", json={"volume_name": "自定义"})

    # Regenerate volume 1
    v1_id = volumes[0]["id"]
    resp = await client.post(f"/api/v1/projects/{pid}/volumes/{v1_id}/regenerate")
    assert resp.status_code == 200

    # Volume 2 should still have custom name
    v2 = (await client.get(f"/api/v1/projects/{pid}/volumes/{v2_id}")).json()
    assert v2["volume_name"] == "自定义"

    # Volume 1 should have been regenerated (status reset to draft)
    v1 = resp.json()
    assert v1["status"] == "draft"


@pytest.mark.asyncio
async def test_regenerate_does_not_affect_others(client):
    pid, sid = await _setup_with_synopsis(client)
    volumes = (await client.post(f"/api/v1/projects/{pid}/volumes/generate", json={"synopsis_id": sid})).json()
    # Adopt all
    for v in volumes:
        await client.post(f"/api/v1/projects/{pid}/volumes/{v['id']}/adopt")

    # Regenerate first
    await client.post(f"/api/v1/projects/{pid}/volumes/{volumes[0]['id']}/regenerate")

    # Others should still be adopted
    v2 = (await client.get(f"/api/v1/projects/{pid}/volumes/{volumes[1]['id']}")).json()
    assert v2["status"] == "adopted"


# === Reorder ===


@pytest.mark.asyncio
async def test_reorder_volumes(client):
    pid, sid = await _setup_with_synopsis(client)
    volumes = (await client.post(f"/api/v1/projects/{pid}/volumes/generate", json={"synopsis_id": sid})).json()
    assert len(volumes) == 3

    # Reverse order
    ids = [v["id"] for v in reversed(volumes)]
    resp = await client.post(f"/api/v1/projects/{pid}/volumes/reorder", json={"volume_ids": ids})
    assert resp.status_code == 200
    reordered = resp.json()
    assert reordered[0]["id"] == ids[0]
    assert reordered[1]["id"] == ids[1]
    assert reordered[2]["id"] == ids[2]
    assert reordered[0]["volume_index"] == 0
    assert reordered[1]["volume_index"] == 1
    assert reordered[2]["volume_index"] == 2


@pytest.mark.asyncio
async def test_reorder_persists(client):
    pid, sid = await _setup_with_synopsis(client)
    volumes = (await client.post(f"/api/v1/projects/{pid}/volumes/generate", json={"synopsis_id": sid})).json()
    ids = [v["id"] for v in reversed(volumes)]
    await client.post(f"/api/v1/projects/{pid}/volumes/reorder", json={"volume_ids": ids})
    # Re-list
    listed = (await client.get(f"/api/v1/projects/{pid}/volumes")).json()
    assert listed[0]["volume_index"] == 0
    assert listed[0]["id"] == ids[0]


# === Synopsis link ===


@pytest.mark.asyncio
async def test_volumes_linked_to_synopsis(client):
    pid, sid = await _setup_with_synopsis(client)
    volumes = (await client.post(f"/api/v1/projects/{pid}/volumes/generate", json={"synopsis_id": sid})).json()
    for v in volumes:
        assert v["synopsis_id"] == sid


# === Error cases ===


@pytest.mark.asyncio
async def test_volume_not_found(client):
    pid, _ = await _setup_with_synopsis(client)
    resp = await client.get(f"/api/v1/projects/{pid}/volumes/nonexistent")
    assert resp.status_code == 404
