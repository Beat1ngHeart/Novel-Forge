"""Tests for bible candidate generation, approval, rejection, apply, undo."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


async def _setup_with_direction(client: AsyncClient) -> tuple[str, str]:
    """Create project, generate creative directions, adopt one. Returns (project_id, direction_id)."""
    pid = (await client.post("/api/v1/projects", json={"name": "Bible Gen Test"})).json()["id"]
    dirs = (
        await client.post(
            f"/api/v1/projects/{pid}/creative/generate",
            json={"one_line_idea": "一个炼器师在末法时代重建修仙文明的故事"},
        )
    ).json()
    did = dirs[0]["id"]
    await client.post(f"/api/v1/projects/{pid}/creative/directions/{did}/accept")
    return pid, did


# === Generate ===


@pytest.mark.asyncio
async def test_generate_candidates(client):
    pid, did = await _setup_with_direction(client)
    resp = await client.post(
        f"/api/v1/projects/{pid}/bible-candidates/generate",
        json={"direction_id": did},
    )
    assert resp.status_code == 200
    candidates = resp.json()
    assert len(candidates) > 0
    categories = {c["category"] for c in candidates}
    assert "character" in categories
    assert "world_rule" in categories
    assert "plot_thread" in categories
    assert "foreshadowing" in categories


@pytest.mark.asyncio
async def test_candidates_have_pending_status(client):
    pid, did = await _setup_with_direction(client)
    candidates = (
        await client.post(
            f"/api/v1/projects/{pid}/bible-candidates/generate",
            json={"direction_id": did},
        )
    ).json()
    for c in candidates:
        assert c["status"] == "pending"
        assert c["source_status"] == "ai_suggestion"


@pytest.mark.asyncio
async def test_generate_requires_adopted_direction(client):
    pid = (await client.post("/api/v1/projects", json={"name": "X"})).json()["id"]
    dirs = (
        await client.post(
            f"/api/v1/projects/{pid}/creative/generate",
            json={"one_line_idea": "一个炼器师的故事"},
        )
    ).json()
    # Don't adopt
    resp = await client.post(
        f"/api/v1/projects/{pid}/bible-candidates/generate",
        json={"direction_id": dirs[0]["id"]},
    )
    assert resp.status_code == 400


# === List ===


@pytest.mark.asyncio
async def test_list_candidates(client):
    pid, did = await _setup_with_direction(client)
    await client.post(
        f"/api/v1/projects/{pid}/bible-candidates/generate",
        json={"direction_id": did},
    )
    resp = await client.get(f"/api/v1/projects/{pid}/bible-candidates")
    assert resp.status_code == 200
    assert len(resp.json()) > 0


@pytest.mark.asyncio
async def test_filter_by_category(client):
    pid, did = await _setup_with_direction(client)
    await client.post(
        f"/api/v1/projects/{pid}/bible-candidates/generate",
        json={"direction_id": did},
    )
    resp = await client.get(f"/api/v1/projects/{pid}/bible-candidates?category=character")
    chars = resp.json()
    assert all(c["category"] == "character" for c in chars)


# === Approve / Reject ===


@pytest.mark.asyncio
async def test_approve_candidate(client):
    pid, did = await _setup_with_direction(client)
    candidates = (
        await client.post(
            f"/api/v1/projects/{pid}/bible-candidates/generate",
            json={"direction_id": did},
        )
    ).json()
    cid = candidates[0]["id"]
    resp = await client.post(f"/api/v1/projects/{pid}/bible-candidates/{cid}/approve")
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"
    assert resp.json()["confirmed_at"] is not None


@pytest.mark.asyncio
async def test_reject_candidate(client):
    pid, did = await _setup_with_direction(client)
    candidates = (
        await client.post(
            f"/api/v1/projects/{pid}/bible-candidates/generate",
            json={"direction_id": did},
        )
    ).json()
    cid = candidates[0]["id"]
    resp = await client.post(
        f"/api/v1/projects/{pid}/bible-candidates/{cid}/reject",
        json={"reason": "不够新颖"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"
    assert resp.json()["rejection_reason"] == "不够新颖"


@pytest.mark.asyncio
async def test_rejected_not_applied(client):
    pid, did = await _setup_with_direction(client)
    candidates = (
        await client.post(
            f"/api/v1/projects/{pid}/bible-candidates/generate",
            json={"direction_id": did},
        )
    ).json()
    cid = candidates[0]["id"]
    await client.post(f"/api/v1/projects/{pid}/bible-candidates/{cid}/reject", json={"reason": "x"})
    resp = await client.post(f"/api/v1/projects/{pid}/bible-candidates/apply", json=[cid])
    assert resp.json()["applied"] == 0


# === Edit ===


@pytest.mark.asyncio
async def test_edit_pending_candidate(client):
    pid, did = await _setup_with_direction(client)
    candidates = (
        await client.post(
            f"/api/v1/projects/{pid}/bible-candidates/generate",
            json={"direction_id": did},
        )
    ).json()
    cid = candidates[0]["id"]
    resp = await client.patch(
        f"/api/v1/projects/{pid}/bible-candidates/{cid}",
        json={"title": "修改后的标题"},
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "修改后的标题"


@pytest.mark.asyncio
async def test_cannot_edit_non_pending(client):
    pid, did = await _setup_with_direction(client)
    candidates = (
        await client.post(
            f"/api/v1/projects/{pid}/bible-candidates/generate",
            json={"direction_id": did},
        )
    ).json()
    cid = candidates[0]["id"]
    await client.post(f"/api/v1/projects/{pid}/bible-candidates/{cid}/approve")
    resp = await client.patch(
        f"/api/v1/projects/{pid}/bible-candidates/{cid}",
        json={"title": "should fail"},
    )
    assert resp.status_code == 400


# === Apply ===


@pytest.mark.asyncio
async def test_apply_approved_candidates(client):
    pid, did = await _setup_with_direction(client)
    candidates = (
        await client.post(
            f"/api/v1/projects/{pid}/bible-candidates/generate",
            json={"direction_id": did},
        )
    ).json()
    # Approve all
    ids = [c["id"] for c in candidates]
    for cid in ids:
        await client.post(f"/api/v1/projects/{pid}/bible-candidates/{cid}/approve")

    # Apply
    resp = await client.post(f"/api/v1/projects/{pid}/bible-candidates/apply", json=ids)
    assert resp.status_code == 200
    result = resp.json()
    assert result["applied"] == len(ids)

    # Check bible now has content
    chars = (await client.get(f"/api/v1/projects/{pid}/characters")).json()
    rules = (await client.get(f"/api/v1/projects/{pid}/world-rules")).json()
    assert len(chars) > 0
    assert len(rules) > 0
    # All should be ai_suggestion
    for c in chars:
        assert c["source_status"] == "ai_suggestion"


@pytest.mark.asyncio
async def test_applied_candidates_have_bible_id(client):
    pid, did = await _setup_with_direction(client)
    candidates = (
        await client.post(
            f"/api/v1/projects/{pid}/bible-candidates/generate",
            json={"direction_id": did},
        )
    ).json()
    cid = candidates[0]["id"]
    await client.post(f"/api/v1/projects/{pid}/bible-candidates/{cid}/approve")
    await client.post(f"/api/v1/projects/{pid}/bible-candidates/apply", json=[cid])
    resp = await client.get(f"/api/v1/projects/{pid}/bible-candidates?status=applied")
    applied = resp.json()
    assert len(applied) >= 1
    assert applied[0]["applied_bible_id"] != ""


# === Undo ===


@pytest.mark.asyncio
async def test_undo_apply(client):
    pid, did = await _setup_with_direction(client)
    candidates = (
        await client.post(
            f"/api/v1/projects/{pid}/bible-candidates/generate",
            json={"direction_id": did},
        )
    ).json()
    # Pick a character candidate
    char_cand = next(c for c in candidates if c["category"] == "character")
    cid = char_cand["id"]
    await client.post(f"/api/v1/projects/{pid}/bible-candidates/{cid}/approve")
    await client.post(f"/api/v1/projects/{pid}/bible-candidates/apply", json=[cid])

    # Verify in bible
    chars_before = (await client.get(f"/api/v1/projects/{pid}/characters")).json()
    assert len(chars_before) >= 1

    # Undo
    resp = await client.post(f"/api/v1/projects/{pid}/bible-candidates/{cid}/undo")
    assert resp.status_code == 200
    assert resp.json()["status"] == "pending"

    # Verify removed from bible
    chars_after = (await client.get(f"/api/v1/projects/{pid}/characters")).json()
    assert len(chars_after) < len(chars_before)


# === Transaction safety ===


@pytest.mark.asyncio
async def test_apply_empty_list(client):
    pid, _ = await _setup_with_direction(client)
    resp = await client.post(f"/api/v1/projects/{pid}/bible-candidates/apply", json=[])
    assert resp.status_code == 200
    assert resp.json()["applied"] == 0
