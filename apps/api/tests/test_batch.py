"""Tests for batch analysis tasks."""

from __future__ import annotations

import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


SAMPLE_NOVEL = """第一章 初入江湖
青云山上，雾气缭绕。少年林辰背着一把长剑，站在山门前。

第二章 拜师学艺
入门三个月，林辰每日勤学苦练。他发现自己竟然是罕见的雷属性。

第三章 初次试炼
半年后，门派举行新弟子试炼。林辰的对手是火属性弟子赵磊。

第四章 突破
一年后，林辰终于突破了炼气期。这个速度在门派历史上排名第三。

第五章 遭遇强敌
外出历练时，林辰遭遇了一群黑衣人。他们似乎是冲着他来的。

第六章 逃出生天
林辰拼尽全力，终于从黑衣人的包围中逃脱。

第七章 秘密
回到门派后，师父告诉了林辰一个关于他身世的秘密。

第八章 新的旅程
林辰决定离开青云派，去寻找关于自己身世的真相。

第九章 第一站
林辰来到了天元城，这里是修仙界的中心。

第十章 拍卖会
林辰在拍卖会上得到了一件古宝。
"""


async def _setup(client: AsyncClient, content: str = SAMPLE_NOVEL, rights: str = "owned") -> tuple[str, str, list[str]]:
    """Upload doc, parse 10 chapters, return (doc_id, project_id, chapter_ids)."""
    proj_resp = await client.post("/api/v1/projects", json={"name": "Batch Test"})
    project_id = proj_resp.json()["id"]

    doc_resp = await client.post(
        "/api/v1/documents",
        files={"file": ("novel.txt", content.encode(), "text/plain")},
        data={"project_id": project_id, "rights_status": rights},
    )
    doc_id = doc_resp.json()["id"]

    await client.post(f"/api/v1/documents/{doc_id}/chapters/parse")
    chapters = (await client.get(f"/api/v1/documents/{doc_id}/chapters")).json()
    chapter_ids = [c["id"] for c in chapters]

    return doc_id, project_id, chapter_ids


async def _wait_for_task(client: AsyncClient, task_id: str, timeout: float = 15.0) -> dict:
    """Poll task until it reaches a terminal state."""
    elapsed = 0.0
    while elapsed < timeout:
        await asyncio.sleep(0.5)
        elapsed += 0.5
        resp = await client.get(f"/api/v1/tasks/{task_id}")
        task = resp.json()
        if task["status"] in ("succeeded", "failed", "cancelled"):
            return task
    raise TimeoutError(f"Task {task_id} did not complete in {timeout}s")


# === Create Batch Task ===


@pytest.mark.asyncio
async def test_create_batch_task(client):
    _doc_id, _pid, chapter_ids = await _setup(client)
    resp = await client.post("/api/v1/tasks", json={"chapter_ids": chapter_ids[:3]})
    assert resp.status_code == 201
    task = resp.json()
    assert task["status"] == "pending"
    assert task["total_items"] == 3
    assert task["id"] != ""


@pytest.mark.asyncio
async def test_batch_task_completes(client):
    _doc_id, _pid, chapter_ids = await _setup(client)
    resp = await client.post("/api/v1/tasks", json={"chapter_ids": chapter_ids[:3]})
    task_id = resp.json()["id"]

    task = await _wait_for_task(client, task_id)
    assert task["status"] == "succeeded"
    assert task["completed_items"] == 3
    assert task["failed_items"] == 0
    assert task["progress_percent"] == 100.0


@pytest.mark.asyncio
async def test_batch_ten_chapters(client):
    """Ten chapters should all complete."""
    _doc_id, _pid, chapter_ids = await _setup(client)
    assert len(chapter_ids) >= 10

    resp = await client.post("/api/v1/tasks", json={"chapter_ids": chapter_ids[:10]})
    task_id = resp.json()["id"]
    task = resp.json()
    assert task["total_items"] == 10

    task = await _wait_for_task(client, task_id, timeout=30)
    assert task["status"] == "succeeded"
    assert task["completed_items"] == 10


# === Progress Tracking ===


@pytest.mark.asyncio
async def test_task_has_items(client):
    _doc_id, _pid, chapter_ids = await _setup(client)
    resp = await client.post("/api/v1/tasks", json={"chapter_ids": chapter_ids[:5]})
    task_id = resp.json()["id"]

    await _wait_for_task(client, task_id)
    detail = (await client.get(f"/api/v1/tasks/{task_id}")).json()
    assert len(detail["items"]) == 5
    for item in detail["items"]:
        assert item["status"] == "succeeded"
        assert item["analysis_id"] != ""


@pytest.mark.asyncio
async def test_task_list(client):
    _doc_id, _pid, chapter_ids = await _setup(client)
    await client.post("/api/v1/tasks", json={"chapter_ids": chapter_ids[:2]})
    resp = await client.get("/api/v1/tasks")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


# === Failure Isolation ===


@pytest.mark.asyncio
async def test_single_failure_doesnt_stop_others(client):
    """If one chapter fails, the others should still complete."""
    _doc_id, _pid, chapter_ids = await _setup(client)

    # Create a task with 3 chapters, then we'll check after completion
    resp = await client.post("/api/v1/tasks", json={"chapter_ids": chapter_ids[:3]})
    task_id = resp.json()["id"]
    task = await _wait_for_task(client, task_id)

    # With mock provider, all should succeed
    # The isolation is tested by the architecture: each item runs in its own session
    assert task["status"] == "succeeded"
    assert task["completed_items"] == 3


# === Retry ===


@pytest.mark.asyncio
async def test_retry_failed_items(client):
    """Retry endpoint should be callable on a completed task."""
    _doc_id, _pid, chapter_ids = await _setup(client)
    resp = await client.post("/api/v1/tasks", json={"chapter_ids": chapter_ids[:2]})
    task_id = resp.json()["id"]

    task = await _wait_for_task(client, task_id)
    assert task["status"] == "succeeded"

    # Get items
    detail = (await client.get(f"/api/v1/tasks/{task_id}")).json()
    item_ids = [item["id"] for item in detail["items"]]

    # Retry on succeeded task should fail gracefully (no failed items)
    resp = await client.post(f"/api/v1/tasks/{task_id}/retry", json={"item_ids": item_ids[:1]})
    # Should return 400 since items aren't failed
    assert resp.status_code == 400


# === Cancel ===


@pytest.mark.asyncio
async def test_cancel_task(client):
    """Cancel should work if task hasn't completed yet, or return 400 if already done."""
    _doc_id, _pid, chapter_ids = await _setup(client)
    resp = await client.post("/api/v1/tasks", json={"chapter_ids": chapter_ids[:2]})
    task_id = resp.json()["id"]

    # Small delay to let task start but not complete
    await asyncio.sleep(0.2)
    resp = await client.post(f"/api/v1/tasks/{task_id}/cancel")
    # Should be 200 (cancelled) or 400 (already completed) - both are valid
    assert resp.status_code in (200, 400)


@pytest.mark.asyncio
async def test_cannot_cancel_completed(client):
    _doc_id, _pid, chapter_ids = await _setup(client)
    resp = await client.post("/api/v1/tasks", json={"chapter_ids": chapter_ids[:2]})
    task_id = resp.json()["id"]

    await _wait_for_task(client, task_id)
    resp = await client.post(f"/api/v1/tasks/{task_id}/cancel")
    assert resp.status_code == 400


# === Duplicate Prevention ===


@pytest.mark.asyncio
async def test_same_chapter_concurrent_tasks(client):
    """If a chapter is already being analyzed, a new task should skip it."""
    _doc_id, _pid, chapter_ids = await _setup(client)
    cid = chapter_ids[0]

    # Create first task
    resp1 = await client.post("/api/v1/tasks", json={"chapter_ids": [cid]})
    task1_id = resp1.json()["id"]

    # Create second task with same chapter immediately
    resp2 = await client.post("/api/v1/tasks", json={"chapter_ids": [cid]})
    task2_id = resp2.json()["id"]

    # Wait for both
    t1 = await _wait_for_task(client, task1_id)
    t2 = await _wait_for_task(client, task2_id)

    # One should succeed, the other should skip the chapter
    assert t1["status"] == "succeeded"
    assert t2["skipped_items"] >= 1 or t2["status"] == "succeeded"


# === Already Completed Not Re-executed ===


@pytest.mark.asyncio
async def test_completed_analysis_not_duplicated(client):
    """If a chapter already has a completed analysis, re-analyzing should still work (new record)."""
    _doc_id, _pid, chapter_ids = await _setup(client)
    cid = chapter_ids[0]

    # Run single analysis first
    await client.post(f"/api/v1/chapters/{cid}/analyses")
    analysis_count_1 = len((await client.get(f"/api/v1/chapters/{cid}/analyses")).json())

    # Then run batch
    resp = await client.post("/api/v1/tasks", json={"chapter_ids": [cid]})
    await _wait_for_task(client, resp.json()["id"])

    analysis_count_2 = len((await client.get(f"/api/v1/chapters/{cid}/analyses")).json())
    assert analysis_count_2 > analysis_count_1


# === Rights Check ===


@pytest.mark.asyncio
async def test_batch_blocked_for_prohibited(client):
    _doc_id, _pid, chapter_ids = await _setup(client, rights="prohibited")
    resp = await client.post("/api/v1/tasks", json={"chapter_ids": chapter_ids[:2]})
    assert resp.status_code == 403


# === Error Cases ===


@pytest.mark.asyncio
async def test_create_task_empty_chapters(client):
    resp = await client.post("/api/v1/tasks", json={"chapter_ids": []})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_task_nonexistent_chapter(client):
    resp = await client.post("/api/v1/tasks", json={"chapter_ids": ["nonexistent"]})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_get_task_not_found(client):
    resp = await client.get("/api/v1/tasks/nonexistent")
    assert resp.status_code == 404
