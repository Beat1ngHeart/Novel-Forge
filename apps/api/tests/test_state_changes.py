"""Tests for state change extraction, accept, reject, undo."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


async def _setup_draft(client: AsyncClient) -> tuple[str, str, str]:
    """Returns (project_id, draft_id, version_id)."""
    pid = (await client.post("/api/v1/projects", json={"name": "SC Test"})).json()["id"]
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
    # Save a version
    ver = (
        await client.post(
            f"/api/v1/projects/{pid}/draft-versions/save",
            json={"draft_id": draft["id"], "body_text": "正文内容", "version_type": "user_edit"},
        )
    ).json()
    return pid, draft["id"], ver["id"]


# === Generate ===


@pytest.mark.asyncio
async def test_generate_candidates(client):
    pid, did, _ = await _setup_draft(client)
    resp = await client.post(f"/api/v1/projects/{pid}/state-changes/generate", json={"draft_id": did})
    assert resp.status_code == 200
    candidates = resp.json()
    assert len(candidates) > 0
    for c in candidates:
        assert c["status"] == "pending"
        assert c["change_type"] != ""
        assert c["entity_name"] != ""
        assert c["project_id"] == pid


@pytest.mark.asyncio
async def test_candidates_have_various_types(client):
    pid, did, _ = await _setup_draft(client)
    candidates = (await client.post(f"/api/v1/projects/{pid}/state-changes/generate", json={"draft_id": did})).json()
    types = {c["change_type"] for c in candidates}
    assert "new_character" in types or "character_location" in types
    assert "new_foreshadow" in types or "foreshadow_resolved" in types


# === List ===


@pytest.mark.asyncio
async def test_list_candidates(client):
    pid, did, _ = await _setup_draft(client)
    await client.post(f"/api/v1/projects/{pid}/state-changes/generate", json={"draft_id": did})
    resp = await client.get(f"/api/v1/projects/{pid}/state-changes")
    assert resp.status_code == 200
    assert len(resp.json()) > 0


@pytest.mark.asyncio
async def test_filter_by_status(client):
    pid, did, _ = await _setup_draft(client)
    candidates = (await client.post(f"/api/v1/projects/{pid}/state-changes/generate", json={"draft_id": did})).json()
    await client.post(f"/api/v1/projects/{pid}/state-changes/{candidates[0]['id']}/accept")
    accepted = (await client.get(f"/api/v1/projects/{pid}/state-changes?status=accepted")).json()
    assert all(c["status"] == "accepted" for c in accepted)


# === Accept ===


@pytest.mark.asyncio
async def test_accept_creates_bible_entry(client):
    pid, did, _ = await _setup_draft(client)
    candidates = (await client.post(f"/api/v1/projects/{pid}/state-changes/generate", json={"draft_id": did})).json()
    # Find a new_character candidate
    new_char = next((c for c in candidates if c["change_type"] == "new_character"), None)
    assert new_char is not None
    resp = await client.post(f"/api/v1/projects/{pid}/state-changes/{new_char['id']}/accept")
    assert resp.status_code == 200
    accepted = resp.json()
    assert accepted["status"] == "accepted"
    assert accepted["applied_bible_id"] != ""
    assert accepted["applied_bible_table"] == "bible_characters"

    # Verify in bible
    chars = (await client.get(f"/api/v1/projects/{pid}/characters")).json()
    assert any(c["name"] == new_char["entity_name"] for c in chars)


@pytest.mark.asyncio
async def test_accept_foreshadow(client):
    pid, did, _ = await _setup_draft(client)
    candidates = (await client.post(f"/api/v1/projects/{pid}/state-changes/generate", json={"draft_id": did})).json()
    fs = next((c for c in candidates if c["change_type"] == "new_foreshadow"), None)
    assert fs is not None
    resp = await client.post(f"/api/v1/projects/{pid}/state-changes/{fs['id']}/accept")
    assert resp.status_code == 200
    assert resp.json()["applied_bible_table"] == "bible_foreshadowings"


@pytest.mark.asyncio
async def test_accept_character_location(client):
    pid, did, _ = await _setup_draft(client)
    candidates = (await client.post(f"/api/v1/projects/{pid}/state-changes/generate", json={"draft_id": did})).json()
    loc = next((c for c in candidates if c["change_type"] == "character_location"), None)
    if loc:
        resp = await client.post(f"/api/v1/projects/{pid}/state-changes/{loc['id']}/accept")
        assert resp.status_code == 200


# === Reject ===


@pytest.mark.asyncio
async def test_reject_candidate(client):
    pid, did, _ = await _setup_draft(client)
    candidates = (await client.post(f"/api/v1/projects/{pid}/state-changes/generate", json={"draft_id": did})).json()
    cid = candidates[0]["id"]
    resp = await client.post(
        f"/api/v1/projects/{pid}/state-changes/{cid}/reject",
        json={"reason": "不够合理"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"
    assert resp.json()["rejection_reason"] == "不够合理"


@pytest.mark.asyncio
async def test_rejected_not_in_bible(client):
    pid, did, _ = await _setup_draft(client)
    candidates = (await client.post(f"/api/v1/projects/{pid}/state-changes/generate", json={"draft_id": did})).json()
    chars_before = len((await client.get(f"/api/v1/projects/{pid}/characters")).json())
    new_char = next((c for c in candidates if c["change_type"] == "new_character"), None)
    if new_char:
        await client.post(f"/api/v1/projects/{pid}/state-changes/{new_char['id']}/reject", json={"reason": "x"})
    chars_after = len((await client.get(f"/api/v1/projects/{pid}/characters")).json())
    assert chars_after == chars_before


# === Undo ===


@pytest.mark.asyncio
async def test_undo_accept(client):
    pid, did, _ = await _setup_draft(client)
    candidates = (await client.post(f"/api/v1/projects/{pid}/state-changes/generate", json={"draft_id": did})).json()
    new_char = next((c for c in candidates if c["change_type"] == "new_character"), None)
    assert new_char is not None
    await client.post(f"/api/v1/projects/{pid}/state-changes/{new_char['id']}/accept")
    chars_before = len((await client.get(f"/api/v1/projects/{pid}/characters")).json())
    # Undo
    resp = await client.post(f"/api/v1/projects/{pid}/state-changes/{new_char['id']}/undo")
    assert resp.status_code == 200
    assert resp.json()["status"] == "pending"
    chars_after = len((await client.get(f"/api/v1/projects/{pid}/characters")).json())
    assert chars_after < chars_before


# === Transaction behavior ===


@pytest.mark.asyncio
async def test_partial_accept_reject(client):
    """Accept some, reject others — should work independently."""
    pid, did, _ = await _setup_draft(client)
    candidates = (await client.post(f"/api/v1/projects/{pid}/state-changes/generate", json={"draft_id": did})).json()
    if len(candidates) >= 2:
        await client.post(f"/api/v1/projects/{pid}/state-changes/{candidates[0]['id']}/accept")
        await client.post(f"/api/v1/projects/{pid}/state-changes/{candidates[1]['id']}/reject", json={"reason": "x"})
        all_c = (await client.get(f"/api/v1/projects/{pid}/state-changes")).json()
        statuses = {c["status"] for c in all_c}
        assert "accepted" in statuses or "rejected" in statuses


# === Error cases ===


@pytest.mark.asyncio
async def test_candidate_not_found(client):
    pid, _, _ = await _setup_draft(client)
    resp = await client.get(f"/api/v1/projects/{pid}/state-changes?status=nonexistent")
    assert resp.status_code == 200
    assert len(resp.json()) == 0
