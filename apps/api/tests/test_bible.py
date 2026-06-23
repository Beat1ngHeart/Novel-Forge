"""Tests for bible CRUD — characters, world rules, plot threads, foreshadowings."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


async def _create_project(client: AsyncClient, name: str = "Bible Test") -> str:
    resp = await client.post("/api/v1/projects", json={"name": name})
    assert resp.status_code == 201
    return resp.json()["id"]


# === Characters ===


@pytest.mark.asyncio
async def test_create_character(client):
    pid = await _create_project(client)
    resp = await client.post(
        f"/api/v1/projects/{pid}/characters",
        json={
            "name": "林辰",
            "aliases": "小林",
            "age": "18",
            "identity": "青云派弟子",
            "personality": "坚毅勇敢",
            "desire": "找到灭门真相",
            "source_status": "user_confirmed",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "林辰"
    assert data["source_status"] == "user_confirmed"


@pytest.mark.asyncio
async def test_list_characters(client):
    pid = await _create_project(client)
    await client.post(f"/api/v1/projects/{pid}/characters", json={"name": "A"})
    await client.post(f"/api/v1/projects/{pid}/characters", json={"name": "B"})
    resp = await client.get(f"/api/v1/projects/{pid}/characters")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_update_character(client):
    pid = await _create_project(client)
    cid = (await client.post(f"/api/v1/projects/{pid}/characters", json={"name": "X"})).json()["id"]
    resp = await client.patch(f"/api/v1/projects/{pid}/characters/{cid}", json={"name": "Y", "age": "20"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Y"


@pytest.mark.asyncio
async def test_delete_character(client):
    pid = await _create_project(client)
    cid = (await client.post(f"/api/v1/projects/{pid}/characters", json={"name": "Z"})).json()["id"]
    resp = await client.delete(f"/api/v1/projects/{pid}/characters/{cid}")
    assert resp.status_code == 204
    assert (await client.get(f"/api/v1/projects/{pid}/characters/{cid}")).status_code == 404


@pytest.mark.asyncio
async def test_character_source_status(client):
    pid = await _create_project(client)
    for status in ("ai_suggestion", "user_confirmed", "text_fact", "deprecated"):
        resp = await client.post(
            f"/api/v1/projects/{pid}/characters",
            json={"name": f"char_{status}", "source_status": status},
        )
        assert resp.status_code == 201
        assert resp.json()["source_status"] == status


@pytest.mark.asyncio
async def test_filter_characters_by_source(client):
    pid = await _create_project(client)
    await client.post(f"/api/v1/projects/{pid}/characters", json={"name": "A", "source_status": "ai_suggestion"})
    await client.post(f"/api/v1/projects/{pid}/characters", json={"name": "B", "source_status": "user_confirmed"})
    resp = await client.get(f"/api/v1/projects/{pid}/characters?source_status=ai_suggestion")
    assert len(resp.json()) == 1
    assert resp.json()[0]["source_status"] == "ai_suggestion"


@pytest.mark.asyncio
async def test_deprecated_character(client):
    pid = await _create_project(client)
    cid = (
        await client.post(
            f"/api/v1/projects/{pid}/characters",
            json={"name": "Old", "source_status": "user_confirmed"},
        )
    ).json()["id"]
    resp = await client.patch(
        f"/api/v1/projects/{pid}/characters/{cid}",
        json={"source_status": "deprecated"},
    )
    assert resp.json()["source_status"] == "deprecated"


# === World Rules ===


@pytest.mark.asyncio
async def test_create_world_rule(client):
    pid = await _create_project(client)
    resp = await client.post(
        f"/api/v1/projects/{pid}/world-rules",
        json={"name": "灵气等级", "category": "修炼体系", "description": "炼气→筑基→金丹→元婴"},
    )
    assert resp.status_code == 201
    assert resp.json()["category"] == "修炼体系"


@pytest.mark.asyncio
async def test_list_world_rules(client):
    pid = await _create_project(client)
    await client.post(f"/api/v1/projects/{pid}/world-rules", json={"name": "R1"})
    await client.post(f"/api/v1/projects/{pid}/world-rules", json={"name": "R2"})
    assert len((await client.get(f"/api/v1/projects/{pid}/world-rules")).json()) == 2


@pytest.mark.asyncio
async def test_update_world_rule(client):
    pid = await _create_project(client)
    rid = (await client.post(f"/api/v1/projects/{pid}/world-rules", json={"name": "R"})).json()["id"]
    resp = await client.patch(f"/api/v1/projects/{pid}/world-rules/{rid}", json={"name": "R2"})
    assert resp.json()["name"] == "R2"


@pytest.mark.asyncio
async def test_delete_world_rule(client):
    pid = await _create_project(client)
    rid = (await client.post(f"/api/v1/projects/{pid}/world-rules", json={"name": "R"})).json()["id"]
    assert (await client.delete(f"/api/v1/projects/{pid}/world-rules/{rid}")).status_code == 204


# === Plot Threads ===


@pytest.mark.asyncio
async def test_create_plot_thread(client):
    pid = await _create_project(client)
    resp = await client.post(
        f"/api/v1/projects/{pid}/plot-threads",
        json={"title": "灭门真相", "thread_type": "main", "description": "林辰追查灭门真相"},
    )
    assert resp.status_code == 201
    assert resp.json()["thread_type"] == "main"


@pytest.mark.asyncio
async def test_plot_thread_statuses(client):
    pid = await _create_project(client)
    for status in ("active", "resolved", "abandoned"):
        resp = await client.post(
            f"/api/v1/projects/{pid}/plot-threads",
            json={"title": f"t_{status}", "current_status": status},
        )
        assert resp.json()["current_status"] == status


@pytest.mark.asyncio
async def test_update_plot_thread(client):
    pid = await _create_project(client)
    tid = (await client.post(f"/api/v1/projects/{pid}/plot-threads", json={"title": "T"})).json()["id"]
    resp = await client.patch(
        f"/api/v1/projects/{pid}/plot-threads/{tid}",
        json={"current_status": "resolved", "resolution": "真相大白"},
    )
    assert resp.json()["current_status"] == "resolved"


@pytest.mark.asyncio
async def test_delete_plot_thread(client):
    pid = await _create_project(client)
    tid = (await client.post(f"/api/v1/projects/{pid}/plot-threads", json={"title": "T"})).json()["id"]
    assert (await client.delete(f"/api/v1/projects/{pid}/plot-threads/{tid}")).status_code == 204


# === Foreshadowings ===


@pytest.mark.asyncio
async def test_create_foreshadowing(client):
    pid = await _create_project(client)
    resp = await client.post(
        f"/api/v1/projects/{pid}/foreshadowings",
        json={
            "content": "林辰体内的远古血脉异动",
            "planted_chapter": "第一章",
            "expected_payoff_range": "第10-20章",
            "status": "planted",
            "related_characters": "林辰",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "planted"


@pytest.mark.asyncio
async def test_foreshadowing_statuses(client):
    pid = await _create_project(client)
    for status in ("planted", "progressing", "paid_off", "abandoned"):
        resp = await client.post(
            f"/api/v1/projects/{pid}/foreshadowings",
            json={"content": f"fs_{status}", "status": status},
        )
        assert resp.json()["status"] == status


@pytest.mark.asyncio
async def test_update_foreshadowing(client):
    pid = await _create_project(client)
    fid = (
        await client.post(
            f"/api/v1/projects/{pid}/foreshadowings",
            json={"content": "伏笔A", "status": "planted"},
        )
    ).json()["id"]
    resp = await client.patch(
        f"/api/v1/projects/{pid}/foreshadowings/{fid}",
        json={"status": "paid_off", "actual_payoff_chapter": "第15章"},
    )
    assert resp.json()["status"] == "paid_off"
    assert resp.json()["actual_payoff_chapter"] == "第15章"


@pytest.mark.asyncio
async def test_delete_foreshadowing(client):
    pid = await _create_project(client)
    fid = (
        await client.post(
            f"/api/v1/projects/{pid}/foreshadowings",
            json={"content": "X"},
        )
    ).json()["id"]
    assert (await client.delete(f"/api/v1/projects/{pid}/foreshadowings/{fid}")).status_code == 204


# === Cross-entity isolation ===


@pytest.mark.asyncio
async def test_bible_data_isolated_by_project(client):
    p1 = await _create_project(client, "P1")
    p2 = await _create_project(client, "P2")
    await client.post(f"/api/v1/projects/{p1}/characters", json={"name": "A"})
    await client.post(f"/api/v1/projects/{p2}/characters", json={"name": "B"})
    r1 = (await client.get(f"/api/v1/projects/{p1}/characters")).json()
    r2 = (await client.get(f"/api/v1/projects/{p2}/characters")).json()
    assert len(r1) == 1 and r1[0]["name"] == "A"
    assert len(r2) == 1 and r2[0]["name"] == "B"


@pytest.mark.asyncio
async def test_delete_project_cascades_bible(client):
    pid = await _create_project(client)
    await client.post(f"/api/v1/projects/{pid}/characters", json={"name": "X"})
    await client.post(f"/api/v1/projects/{pid}/world-rules", json={"name": "R"})
    await client.post(f"/api/v1/projects/{pid}/foreshadowings", json={"content": "F"})
    await client.delete(f"/api/v1/projects/{pid}")
    # Verify project gone
    assert (await client.get(f"/api/v1/projects/{pid}")).status_code == 404


# === Error cases ===


@pytest.mark.asyncio
async def test_character_not_found(client):
    pid = await _create_project(client)
    assert (await client.get(f"/api/v1/projects/{pid}/characters/nonexistent")).status_code == 404


@pytest.mark.asyncio
async def test_character_project_mismatch(client):
    p1 = await _create_project(client, "P1")
    p2 = await _create_project(client, "P2")
    cid = (await client.post(f"/api/v1/projects/{p1}/characters", json={"name": "X"})).json()["id"]
    assert (await client.get(f"/api/v1/projects/{p2}/characters/{cid}")).status_code == 404
