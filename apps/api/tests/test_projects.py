"""Tests for project CRUD, archive/restore, search, filter, pagination."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


async def _create_project(client: AsyncClient, name: str = "Test Novel", **kwargs) -> dict:
    data = {"name": name, **kwargs}
    resp = await client.post("/api/v1/projects", json=data)
    assert resp.status_code == 201
    return resp.json()


# === Basic CRUD ===


@pytest.mark.asyncio
async def test_create_project(client):
    project = await _create_project(client, "我的小说", genre="玄幻", audience_type="男频")
    assert project["name"] == "我的小说"
    assert project["genre"] == "玄幻"
    assert project["audience_type"] == "男频"
    assert project["status"] == "drafting"
    assert project["current_volume"] == 0
    assert project["current_chapter"] == 0
    assert project["language"] == "zh-CN"
    assert project["archived_at"] is None
    assert project["document_count"] == 0
    assert project["chapter_count"] == 0


@pytest.mark.asyncio
async def test_create_project_validation(client):
    # Empty name
    resp = await client.post("/api/v1/projects", json={"name": ""})
    assert resp.status_code == 422

    # Name too long
    resp = await client.post("/api/v1/projects", json={"name": "x" * 201})
    assert resp.status_code == 422

    # Negative word count
    resp = await client.post("/api/v1/projects", json={"name": "ok", "target_word_count": -1})
    assert resp.status_code == 422

    # Chapter word count too low
    resp = await client.post("/api/v1/projects", json={"name": "ok", "chapter_word_count": 50})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_project(client):
    created = await _create_project(client, "Detail Test")
    resp = await client.get(f"/api/v1/projects/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Detail Test"


@pytest.mark.asyncio
async def test_get_project_not_found(client):
    resp = await client.get("/api/v1/projects/nonexistent")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_project(client):
    created = await _create_project(client, "Original")
    resp = await client.patch(
        f"/api/v1/projects/{created['id']}",
        json={"name": "Updated", "genre": "科幻"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated"
    assert resp.json()["genre"] == "科幻"


@pytest.mark.asyncio
async def test_delete_project(client):
    created = await _create_project(client, "To Delete")
    resp = await client.delete(f"/api/v1/projects/{created['id']}")
    assert resp.status_code == 204
    resp = await client.get(f"/api/v1/projects/{created['id']}")
    assert resp.status_code == 404


# === Archive / Restore ===


@pytest.mark.asyncio
async def test_archive_and_restore(client):
    created = await _create_project(client, "Archive Me")
    pid = created["id"]

    # Archive
    resp = await client.post(f"/api/v1/projects/{pid}/archive")
    assert resp.status_code == 200
    assert resp.json()["archived_at"] is not None

    # Should not appear in default list
    resp = await client.get("/api/v1/projects")
    assert all(p["id"] != pid for p in resp.json()["items"])

    # Should appear with include_archived
    resp = await client.get("/api/v1/projects?include_archived=true")
    assert any(p["id"] == pid for p in resp.json()["items"])

    # Restore
    resp = await client.post(f"/api/v1/projects/{pid}/restore")
    assert resp.status_code == 200
    assert resp.json()["archived_at"] is None

    # Should appear again
    resp = await client.get("/api/v1/projects")
    assert any(p["id"] == pid for p in resp.json()["items"])


@pytest.mark.asyncio
async def test_archive_already_archived(client):
    created = await _create_project(client, "Already Archived")
    await client.post(f"/api/v1/projects/{created['id']}/archive")
    resp = await client.post(f"/api/v1/projects/{created['id']}/archive")
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_restore_not_archived(client):
    created = await _create_project(client, "Not Archived")
    resp = await client.post(f"/api/v1/projects/{created['id']}/restore")
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_cannot_edit_archived(client):
    created = await _create_project(client, "Edit Archived")
    await client.post(f"/api/v1/projects/{created['id']}/archive")
    resp = await client.patch(f"/api/v1/projects/{created['id']}", json={"name": "Should Fail"})
    assert resp.status_code == 400


# === Search / Filter / Sort / Pagination ===


@pytest.mark.asyncio
async def test_search(client):
    await _create_project(client, "仙侠传奇")
    await _create_project(client, "都市高手")
    await _create_project(client, "星际争霸")

    resp = await client.get("/api/v1/projects?search=仙侠")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert "仙侠" in items[0]["name"]


@pytest.mark.asyncio
async def test_filter_by_genre(client):
    await _create_project(client, "G1", genre="玄幻")
    await _create_project(client, "G2", genre="科幻")
    await _create_project(client, "G3", genre="玄幻")

    resp = await client.get("/api/v1/projects?genre=玄幻")
    items = resp.json()["items"]
    assert all(p["genre"] == "玄幻" for p in items)
    assert len(items) == 2


@pytest.mark.asyncio
async def test_pagination(client):
    for i in range(5):
        await _create_project(client, f"Page Test {i}")

    resp = await client.get("/api/v1/projects?page=1&page_size=2")
    data = resp.json()
    assert len(data["items"]) == 2
    assert data["total"] >= 5
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["total_pages"] >= 3


@pytest.mark.asyncio
async def test_sort(client):
    await _create_project(client, "B Novel")
    await _create_project(client, "A Novel")
    await _create_project(client, "C Novel")

    resp = await client.get("/api/v1/projects?sort_by=name&sort_order=asc")
    names = [p["name"] for p in resp.json()["items"]]
    assert names == sorted(names)


# === Stats ===


@pytest.mark.asyncio
async def test_stats(client):
    await _create_project(client, "S1", genre="玄幻")
    await _create_project(client, "S2", genre="科幻")
    await _create_project(client, "S3", genre="玄幻")
    # Archive one
    created = await _create_project(client, "S4")
    await client.post(f"/api/v1/projects/{created['id']}/archive")

    resp = await client.get("/api/v1/projects/stats")
    assert resp.status_code == 200
    stats = resp.json()
    assert stats["total_projects"] >= 4
    assert stats["active_projects"] >= 3
    assert stats["archived_projects"] >= 1
    assert "玄幻" in stats["by_genre"]
    assert "drafting" in stats["by_status"]


# === Data isolation ===


@pytest.mark.asyncio
async def test_project_data_isolation(client):
    p1 = await _create_project(client, "Project A")
    p2 = await _create_project(client, "Project B")

    # Verify each project only has its own data
    r1 = await client.get(f"/api/v1/projects/{p1['id']}")
    r2 = await client.get(f"/api/v1/projects/{p2['id']}")
    assert r1.json()["name"] == "Project A"
    assert r2.json()["name"] == "Project B"
    assert r1.json()["id"] != r2.json()["id"]
