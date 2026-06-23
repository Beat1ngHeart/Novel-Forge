"""Tests for chapter draft generation, update, paragraph rewrite."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


async def _setup_adopted_plan(client: AsyncClient) -> tuple[str, str]:
    """Create project + direction + synopsis + volume + rhythm + plans. Returns (project_id, plan_id)."""
    pid = (await client.post("/api/v1/projects", json={"name": "Draft Test"})).json()["id"]
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
    rhythms = (
        await client.post(f"/api/v1/projects/{pid}/rhythms/generate", json={"volume_id": vid, "chapter_count": 3})
    ).json()
    rid = rhythms[0]["id"]
    plans = (await client.post(f"/api/v1/projects/{pid}/chapter-plans/generate", json={"rhythm_id": rid})).json()
    plan_id = plans[0]["id"]
    await client.post(f"/api/v1/projects/{pid}/chapter-plans/{plan_id}/adopt")
    return pid, plan_id


# === Generate ===


@pytest.mark.asyncio
async def test_generate_draft(client):
    pid, plan_id = await _setup_adopted_plan(client)
    resp = await client.post(
        f"/api/v1/projects/{pid}/drafts/generate",
        json={"plan_id": plan_id},
    )
    assert resp.status_code == 200
    draft = resp.json()
    assert draft["status"] == "ai_draft"
    assert draft["body_text"] != ""
    assert draft["chapter_summary"] != ""
    assert draft["actual_word_count"] > 0
    assert draft["plan_id"] == plan_id
    assert draft["draft_type"] == "ai_draft"


@pytest.mark.asyncio
async def test_draft_with_parameters(client):
    pid, plan_id = await _setup_adopted_plan(client)
    resp = await client.post(
        f"/api/v1/projects/{pid}/drafts/generate",
        json={
            "plan_id": plan_id,
            "parameters": {
                "target_words": 5000,
                "person": "first",
                "pov": "first_person",
                "dialogue_density": "high",
                "pacing": "fast",
            },
        },
    )
    assert resp.status_code == 200
    draft = resp.json()
    assert draft["target_words"] == 5000
    assert draft["person"] == "first"
    assert draft["pov"] == "first_person"
    assert draft["dialogue_density"] == "high"
    assert draft["pacing"] == "fast"


@pytest.mark.asyncio
async def test_draft_requires_adopted_plan(client):
    pid, plan_id = await _setup_adopted_plan(client)
    # Reject the plan
    await client.post(f"/api/v1/projects/{pid}/chapter-plans/{plan_id}/reject")
    resp = await client.post(
        f"/api/v1/projects/{pid}/drafts/generate",
        json={"plan_id": plan_id},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_draft_has_candidates(client):
    pid, plan_id = await _setup_adopted_plan(client)
    resp = await client.post(
        f"/api/v1/projects/{pid}/drafts/generate",
        json={"plan_id": plan_id},
    )
    draft = resp.json()
    import json

    chars = json.loads(draft["new_character_candidates_json"])
    settings = json.loads(draft["new_setting_candidates_json"])
    facts = json.loads(draft["facts_to_confirm_json"])
    assert len(chars) > 0
    assert len(settings) > 0
    assert len(facts) > 0


# === List / Get ===


@pytest.mark.asyncio
async def test_list_drafts(client):
    pid, plan_id = await _setup_adopted_plan(client)
    await client.post(f"/api/v1/projects/{pid}/drafts/generate", json={"plan_id": plan_id})
    resp = await client.get(f"/api/v1/projects/{pid}/drafts?plan_id={plan_id}")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_get_draft(client):
    pid, plan_id = await _setup_adopted_plan(client)
    draft = (await client.post(f"/api/v1/projects/{pid}/drafts/generate", json={"plan_id": plan_id})).json()
    resp = await client.get(f"/api/v1/projects/{pid}/drafts/{draft['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == draft["id"]


# === Human revision ===


@pytest.mark.asyncio
async def test_update_draft_text(client):
    pid, plan_id = await _setup_adopted_plan(client)
    draft = (await client.post(f"/api/v1/projects/{pid}/drafts/generate", json={"plan_id": plan_id})).json()
    new_text = "这是人工修改后的正文。"
    resp = await client.patch(
        f"/api/v1/projects/{pid}/drafts/{draft['id']}",
        json={"body_text": new_text},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "human_revision"
    assert resp.json()["body_text"] == new_text
    assert resp.json()["actual_word_count"] == len(new_text)


@pytest.mark.asyncio
async def test_ai_draft_preserved_on_revision(client):
    """Generating a new draft should not overwrite human revisions."""
    pid, plan_id = await _setup_adopted_plan(client)
    # Generate first draft
    d1 = (await client.post(f"/api/v1/projects/{pid}/drafts/generate", json={"plan_id": plan_id})).json()
    # Human revise
    await client.patch(f"/api/v1/projects/{pid}/drafts/{d1['id']}", json={"body_text": "人工修改"})
    # Generate second draft
    await client.post(f"/api/v1/projects/{pid}/drafts/generate", json={"plan_id": plan_id})
    # Both should exist
    all_drafts = (await client.get(f"/api/v1/projects/{pid}/drafts?plan_id={plan_id}")).json()
    assert len(all_drafts) >= 2
    # Original should still have human revision
    original = (await client.get(f"/api/v1/projects/{pid}/drafts/{d1['id']}")).json()
    assert original["status"] == "human_revision"


# === Paragraph rewrite ===


@pytest.mark.asyncio
async def test_rewrite_paragraph(client):
    pid, plan_id = await _setup_adopted_plan(client)
    draft = (await client.post(f"/api/v1/projects/{pid}/drafts/generate", json={"plan_id": plan_id})).json()
    resp = await client.post(
        f"/api/v1/projects/{pid}/drafts/rewrite-paragraph",
        json={"draft_id": draft["id"], "paragraph_index": 0, "instruction": "更加生动"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "human_revision"


# === Delete ===


@pytest.mark.asyncio
async def test_delete_draft(client):
    pid, plan_id = await _setup_adopted_plan(client)
    draft = (await client.post(f"/api/v1/projects/{pid}/drafts/generate", json={"plan_id": plan_id})).json()
    resp = await client.delete(f"/api/v1/projects/{pid}/drafts/{draft['id']}")
    assert resp.status_code == 204


# === Error cases ===


@pytest.mark.asyncio
async def test_draft_not_found(client):
    pid, _ = await _setup_adopted_plan(client)
    resp = await client.get(f"/api/v1/projects/{pid}/drafts/nonexistent")
    assert resp.status_code == 404
