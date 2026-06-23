"""Tests for draft version management, diff, restore, rewrite."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


async def _setup_draft(client: AsyncClient) -> tuple[str, str]:
    """Create project + full chain + adopted plan + draft. Returns (project_id, draft_id)."""
    pid = (await client.post("/api/v1/projects", json={"name": "Version Test"})).json()["id"]
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
    await client.post(f"/api/v1/projects/{pid}/volumes/{vols[0]['id']}/adopt")
    rhythms = (
        await client.post(
            f"/api/v1/projects/{pid}/rhythms/generate",
            json={"volume_id": vols[0]["id"], "chapter_count": 3},
        )
    ).json()
    plans = (
        await client.post(f"/api/v1/projects/{pid}/chapter-plans/generate", json={"rhythm_id": rhythms[0]["id"]})
    ).json()
    await client.post(f"/api/v1/projects/{pid}/chapter-plans/{plans[0]['id']}/adopt")
    draft = (await client.post(f"/api/v1/projects/{pid}/drafts/generate", json={"plan_id": plans[0]["id"]})).json()
    return pid, draft["id"]


# === Save Version ===


@pytest.mark.asyncio
async def test_save_version(client):
    pid, did = await _setup_draft(client)
    resp = await client.post(
        f"/api/v1/projects/{pid}/draft-versions/save",
        json={"draft_id": did, "body_text": "用户编辑的正文", "version_type": "user_edit"},
    )
    assert resp.status_code == 200
    v = resp.json()
    assert v["version_type"] == "user_edit"
    assert v["body_text"] == "用户编辑的正文"
    assert v["word_count"] > 0
    assert v["is_final"] is False


@pytest.mark.asyncio
async def test_save_version_increments(client):
    pid, did = await _setup_draft(client)
    v1 = (
        await client.post(
            f"/api/v1/projects/{pid}/draft-versions/save",
            json={"draft_id": did, "body_text": "v1", "version_type": "user_edit"},
        )
    ).json()
    v2 = (
        await client.post(
            f"/api/v1/projects/{pid}/draft-versions/save",
            json={"draft_id": did, "body_text": "v2", "version_type": "user_edit"},
        )
    ).json()
    assert v2["version_index"] > v1["version_index"]


# === List Versions ===


@pytest.mark.asyncio
async def test_list_versions(client):
    pid, did = await _setup_draft(client)
    await client.post(
        f"/api/v1/projects/{pid}/draft-versions/save",
        json={"draft_id": did, "body_text": "v1", "version_type": "user_edit"},
    )
    await client.post(
        f"/api/v1/projects/{pid}/draft-versions/save",
        json={"draft_id": did, "body_text": "v2", "version_type": "user_edit"},
    )
    resp = await client.get(f"/api/v1/projects/{pid}/draft-versions?draft_id={did}")
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


# === Mark Final ===


@pytest.mark.asyncio
async def test_mark_final(client):
    pid, did = await _setup_draft(client)
    v = (
        await client.post(
            f"/api/v1/projects/{pid}/draft-versions/save",
            json={"draft_id": did, "body_text": "final", "version_type": "user_edit"},
        )
    ).json()
    resp = await client.post(f"/api/v1/projects/{pid}/draft-versions/{v['id']}/mark-final")
    assert resp.status_code == 200
    assert resp.json()["is_final"] is True


@pytest.mark.asyncio
async def test_only_one_final(client):
    pid, did = await _setup_draft(client)
    v1 = (
        await client.post(
            f"/api/v1/projects/{pid}/draft-versions/save",
            json={"draft_id": did, "body_text": "v1", "version_type": "user_edit"},
        )
    ).json()
    v2 = (
        await client.post(
            f"/api/v1/projects/{pid}/draft-versions/save",
            json={"draft_id": did, "body_text": "v2", "version_type": "user_edit"},
        )
    ).json()
    await client.post(f"/api/v1/projects/{pid}/draft-versions/{v1['id']}/mark-final")
    await client.post(f"/api/v1/projects/{pid}/draft-versions/{v2['id']}/mark-final")
    versions = (await client.get(f"/api/v1/projects/{pid}/draft-versions?draft_id={did}")).json()
    finals = [v for v in versions if v["is_final"]]
    assert len(finals) == 1
    assert finals[0]["id"] == v2["id"]


@pytest.mark.asyncio
async def test_cannot_save_after_final(client):
    pid, did = await _setup_draft(client)
    v = (
        await client.post(
            f"/api/v1/projects/{pid}/draft-versions/save",
            json={"draft_id": did, "body_text": "final", "version_type": "user_edit"},
        )
    ).json()
    await client.post(f"/api/v1/projects/{pid}/draft-versions/{v['id']}/mark-final")
    resp = await client.post(
        f"/api/v1/projects/{pid}/draft-versions/save",
        json={"draft_id": did, "body_text": "should fail", "version_type": "user_edit"},
    )
    assert resp.status_code == 400


# === Restore ===


@pytest.mark.asyncio
async def test_restore_version(client):
    pid, did = await _setup_draft(client)
    v1 = (
        await client.post(
            f"/api/v1/projects/{pid}/draft-versions/save",
            json={"draft_id": did, "body_text": "原始内容", "version_type": "user_edit"},
        )
    ).json()
    await client.post(
        f"/api/v1/projects/{pid}/draft-versions/save",
        json={"draft_id": did, "body_text": "修改后内容", "version_type": "user_edit"},
    )
    # Restore v1
    resp = await client.post(f"/api/v1/projects/{pid}/draft-versions/{v1['id']}/restore")
    assert resp.status_code == 200
    # Draft should now have v1's content
    draft = (await client.get(f"/api/v1/projects/{pid}/drafts/{did}")).json()
    assert draft["body_text"] == "原始内容"


@pytest.mark.asyncio
async def test_restore_preserves_current(client):
    """Restoring should save current as a new version first."""
    pid, did = await _setup_draft(client)
    v1 = (
        await client.post(
            f"/api/v1/projects/{pid}/draft-versions/save",
            json={"draft_id": did, "body_text": "v1", "version_type": "user_edit"},
        )
    ).json()
    await client.post(
        f"/api/v1/projects/{pid}/draft-versions/save",
        json={"draft_id": did, "body_text": "v2", "version_type": "user_edit"},
    )
    await client.post(f"/api/v1/projects/{pid}/draft-versions/{v1['id']}/restore")
    versions = (await client.get(f"/api/v1/projects/{pid}/draft-versions?draft_id={did}")).json()
    assert len(versions) >= 3  # v1, v2, restore-save


# === Diff ===


@pytest.mark.asyncio
async def test_diff_versions(client):
    pid, did = await _setup_draft(client)
    v1 = (
        await client.post(
            f"/api/v1/projects/{pid}/draft-versions/save",
            json={"draft_id": did, "body_text": "hello world", "version_type": "user_edit"},
        )
    ).json()
    v2 = (
        await client.post(
            f"/api/v1/projects/{pid}/draft-versions/save",
            json={"draft_id": did, "body_text": "hello brave new world", "version_type": "user_edit"},
        )
    ).json()
    resp = await client.post(
        f"/api/v1/projects/{pid}/draft-versions/diff",
        json={"version_a_id": v1["id"], "version_b_id": v2["id"]},
    )
    assert resp.status_code == 200
    diff = resp.json()
    assert diff["additions"] > 0


# === AI Rewrite ===


@pytest.mark.asyncio
async def test_ai_rewrite(client):
    pid, did = await _setup_draft(client)
    await client.post(
        f"/api/v1/projects/{pid}/draft-versions/save",
        json={"draft_id": did, "body_text": "林辰站在山门前。他看着远方。", "version_type": "user_edit"},
    )
    resp = await client.post(
        f"/api/v1/projects/{pid}/draft-versions/rewrite",
        json={"draft_id": did, "selected_text": "林辰站在山门前", "instruction": "更加生动", "mode": "rewrite"},
    )
    assert resp.status_code == 200
    assert resp.json()["version_type"] == "ai_rewrite"


@pytest.mark.asyncio
async def test_ai_expand(client):
    pid, did = await _setup_draft(client)
    await client.post(
        f"/api/v1/projects/{pid}/draft-versions/save",
        json={"draft_id": did, "body_text": "他走了。", "version_type": "user_edit"},
    )
    resp = await client.post(
        f"/api/v1/projects/{pid}/draft-versions/rewrite",
        json={"draft_id": did, "selected_text": "他走了。", "instruction": "扩写", "mode": "expand"},
    )
    assert resp.status_code == 200
    assert len(resp.json()["body_text"]) > len("他走了。")


@pytest.mark.asyncio
async def test_ai_compress(client):
    pid, did = await _setup_draft(client)
    long_text = "这是一段很长的文字。" * 100
    await client.post(
        f"/api/v1/projects/{pid}/draft-versions/save",
        json={"draft_id": did, "body_text": long_text, "version_type": "user_edit"},
    )
    resp = await client.post(
        f"/api/v1/projects/{pid}/draft-versions/rewrite",
        json={"draft_id": did, "selected_text": long_text[:100], "instruction": "压缩", "mode": "compress"},
    )
    assert resp.status_code == 200


# === Version Types ===


@pytest.mark.asyncio
async def test_version_types(client):
    pid, did = await _setup_draft(client)
    for vtype in ("ai_draft", "ai_rewrite", "user_edit", "final", "discarded"):
        resp = await client.post(
            f"/api/v1/projects/{pid}/draft-versions/save",
            json={"draft_id": did, "body_text": f"content_{vtype}", "version_type": vtype},
        )
        assert resp.status_code == 200
        assert resp.json()["version_type"] == vtype


# === Persistence ===


@pytest.mark.asyncio
async def test_version_persists_after_refresh(client):
    """Version data persists in database."""
    pid, did = await _setup_draft(client)
    await client.post(
        f"/api/v1/projects/{pid}/draft-versions/save",
        json={"draft_id": did, "body_text": "持久化测试", "version_type": "user_edit"},
    )
    resp = await client.get(f"/api/v1/projects/{pid}/draft-versions?draft_id={did}")
    versions = resp.json()
    assert any("持久化测试" in v["body_text"] for v in versions)
