"""Tests for document upload, rights registration, dedup, security."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


SAMPLE_TXT = "第一章 测试\n这是一个测试文件的内容。\n"
SAMPLE_MD = "# 标题\n\n这是 Markdown 内容。\n"


async def _create_project(client: AsyncClient, name: str = "Test Project") -> str:
    resp = await client.post("/api/v1/projects", json={"name": name})
    assert resp.status_code == 201
    return resp.json()["id"]


async def _upload(client: AsyncClient, filename: str, content: bytes, **form_data) -> dict:
    resp = await client.post(
        "/api/v1/documents",
        files={"file": (filename, content, "text/plain")},
        data=form_data,
    )
    return resp.json() if resp.status_code != 204 else {}


# === Upload ===


@pytest.mark.asyncio
async def test_upload_txt(client):
    resp = await client.post(
        "/api/v1/documents",
        files={"file": ("test.txt", SAMPLE_TXT.encode(), "text/plain")},
        data={"source_name": "原创", "author_name": "测试", "rights_status": "owned"},
    )
    assert resp.status_code == 201
    doc = resp.json()
    assert doc["original_filename"] == "test.txt"
    assert doc["file_type"] == "txt"
    assert doc["mime_type"] == "text/plain"
    assert doc["rights_status"] == "owned"
    assert doc["analysis_allowed"] is True
    assert doc["generation_reference_allowed"] is True
    assert doc["parse_status"] == "completed"
    assert doc["sha256"] != ""


@pytest.mark.asyncio
async def test_upload_markdown(client):
    resp = await client.post(
        "/api/v1/documents",
        files={"file": ("story.md", SAMPLE_MD.encode(), "text/markdown")},
        data={},
    )
    assert resp.status_code == 201
    assert resp.json()["file_type"] == "md"


@pytest.mark.asyncio
async def test_upload_with_project(client):
    pid = await _create_project(client)
    resp = await client.post(
        "/api/v1/documents",
        files={"file": ("test.txt", SAMPLE_TXT.encode(), "text/plain")},
        data={"project_id": pid, "rights_status": "authorized"},
    )
    assert resp.status_code == 201
    assert resp.json()["project_id"] == pid


@pytest.mark.asyncio
async def test_upload_nonexistent_project(client):
    resp = await client.post(
        "/api/v1/documents",
        files={"file": ("test.txt", SAMPLE_TXT.encode(), "text/plain")},
        data={"project_id": "nonexistent"},
    )
    assert resp.status_code == 404


# === Validation ===


@pytest.mark.asyncio
async def test_rejects_bad_extension(client):
    resp = await client.post(
        "/api/v1/documents",
        files={"file": ("virus.exe", b"MZ...", "application/octet-stream")},
        data={},
    )
    assert resp.status_code == 400
    assert "可执行" in resp.json()["detail"] or "不支持" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_rejects_script_extension(client):
    resp = await client.post(
        "/api/v1/documents",
        files={"file": ("script.sh", b"#!/bin/bash", "application/x-sh")},
        data={},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_rejects_oversized(client):
    big = b"x" * (11 * 1024 * 1024)  # 11MB
    resp = await client.post(
        "/api/v1/documents",
        files={"file": ("big.txt", big, "text/plain")},
        data={},
    )
    assert resp.status_code == 400
    assert "过大" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_rejects_empty(client):
    resp = await client.post(
        "/api/v1/documents",
        files={"file": ("empty.txt", b"", "text/plain")},
        data={},
    )
    assert resp.status_code == 400
    assert "空" in resp.json()["detail"]


# === SHA-256 Dedup ===


@pytest.mark.asyncio
async def test_duplicate_detection(client):
    content = SAMPLE_TXT.encode()
    resp1 = await client.post(
        "/api/v1/documents",
        files={"file": ("first.txt", content, "text/plain")},
        data={},
    )
    assert resp1.status_code == 201

    resp2 = await client.post(
        "/api/v1/documents",
        files={"file": ("second.txt", content, "text/plain")},
        data={},
    )
    assert resp2.status_code == 409
    assert "已存在" in resp2.json()["detail"]


@pytest.mark.asyncio
async def test_same_content_different_project_allowed(client):
    pid1 = await _create_project(client, "P1")
    pid2 = await _create_project(client, "P2")
    content = SAMPLE_TXT.encode()

    resp1 = await client.post(
        "/api/v1/documents",
        files={"file": ("a.txt", content, "text/plain")},
        data={"project_id": pid1},
    )
    assert resp1.status_code == 201

    # Same content, different project — allowed
    resp2 = await client.post(
        "/api/v1/documents",
        files={"file": ("a.txt", content, "text/plain")},
        data={"project_id": pid2},
    )
    assert resp2.status_code == 201


# === Rights Status ===


@pytest.mark.asyncio
async def test_rights_prohibited(client):
    resp = await client.post(
        "/api/v1/documents",
        files={"file": ("test.txt", SAMPLE_TXT.encode(), "text/plain")},
        data={"rights_status": "prohibited"},
    )
    assert resp.status_code == 201
    doc = resp.json()
    assert doc["rights_status"] == "prohibited"
    assert doc["analysis_allowed"] is False
    assert doc["generation_reference_allowed"] is False


@pytest.mark.asyncio
async def test_rights_unknown_default(client):
    resp = await client.post(
        "/api/v1/documents",
        files={"file": ("test.txt", SAMPLE_TXT.encode(), "text/plain")},
        data={},
    )
    assert resp.status_code == 201
    doc = resp.json()
    assert doc["rights_status"] == "unknown"
    assert doc["analysis_allowed"] is True
    assert doc["generation_reference_allowed"] is False


@pytest.mark.asyncio
async def test_rights_owned(client):
    resp = await client.post(
        "/api/v1/documents",
        files={"file": ("test.txt", SAMPLE_TXT.encode(), "text/plain")},
        data={"rights_status": "owned"},
    )
    assert resp.status_code == 201
    doc = resp.json()
    assert doc["analysis_allowed"] is True
    assert doc["generation_reference_allowed"] is True


# === Path Traversal ===


@pytest.mark.asyncio
async def test_path_traversal_filename(client):
    resp = await client.post(
        "/api/v1/documents",
        files={"file": ("../../../etc/passwd", SAMPLE_TXT.encode(), "text/plain")},
        data={},
    )
    if resp.status_code == 201:
        doc = resp.json()
        assert ".." not in doc["stored_filename"]
        assert "etc" not in doc["storage_path"]
    else:
        # Rejected is also acceptable
        assert resp.status_code == 400


# === List / Detail / Delete ===


@pytest.mark.asyncio
async def test_list_documents(client):
    await client.post(
        "/api/v1/documents",
        files={"file": ("a.txt", b"content a", "text/plain")},
        data={},
    )
    resp = await client.get("/api/v1/documents")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_list_filter_by_rights(client):
    await client.post(
        "/api/v1/documents",
        files={"file": ("a.txt", b"a", "text/plain")},
        data={"rights_status": "owned"},
    )
    await client.post(
        "/api/v1/documents",
        files={"file": ("b.txt", b"b", "text/plain")},
        data={"rights_status": "unknown"},
    )
    resp = await client.get("/api/v1/documents?rights_status=owned")
    assert resp.status_code == 200
    assert all(d["rights_status"] == "owned" for d in resp.json())


@pytest.mark.asyncio
async def test_get_document(client):
    upload = await client.post(
        "/api/v1/documents",
        files={"file": ("test.txt", SAMPLE_TXT.encode(), "text/plain")},
        data={"rights_status": "owned"},
    )
    doc_id = upload.json()["id"]
    resp = await client.get(f"/api/v1/documents/{doc_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == doc_id


@pytest.mark.asyncio
async def test_get_document_not_found(client):
    resp = await client.get("/api/v1/documents/nonexistent")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_document(client):
    upload = await client.post(
        "/api/v1/documents",
        files={"file": ("del.txt", b"to delete", "text/plain")},
        data={},
    )
    doc_id = upload.json()["id"]
    resp = await client.delete(f"/api/v1/documents/{doc_id}")
    assert resp.status_code == 204
    resp = await client.get(f"/api/v1/documents/{doc_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_not_found(client):
    resp = await client.delete("/api/v1/documents/nonexistent")
    assert resp.status_code == 404
