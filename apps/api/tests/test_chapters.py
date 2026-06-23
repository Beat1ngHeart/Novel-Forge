"""Tests for text cleaning, chapter parsing, merge, split, edit."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


SAMPLE_NOVEL = """第一卷 起源

第一章 初入江湖
青云山上，雾气缭绕。少年林辰背着一把长剑，站在山门前。
"从今日起，你便是青云派的弟子了。"一位白发老者说道。
林辰心中激动，他知道，自己的修炼之路正式开始了。

第二章 拜师学艺
入门三个月，林辰每日勤学苦练。
他发现自己的灵根竟然是罕见的雷属性。
"雷属性灵根？"师父眉头微皱。

第三章 初次试炼
半年后，门派举行新弟子试炼。
林辰的对手是一名火属性弟子，名叫赵磊。
"你一个雷属性的，也敢来参加试炼？"赵磊冷笑。

第二卷 崛起

第四章 突破
一年后，林辰终于突破了炼气期。
这个速度在青云派历史上排名第三。
"""


async def _upload_doc(client: AsyncClient, content: str = SAMPLE_NOVEL, name: str = "novel.txt") -> str:
    resp = await client.post(
        "/api/v1/documents",
        files={"file": (name, content.encode(), "text/plain")},
        data={"rights_status": "owned"},
    )
    assert resp.status_code == 201
    return resp.json()["id"]


# === Parse Preview ===


@pytest.mark.asyncio
async def test_parse_preview(client):
    doc_id = await _upload_doc(client)
    resp = await client.get(f"/api/v1/documents/{doc_id}/chapters/parse-preview")
    assert resp.status_code == 200
    data = resp.json()
    assert data["encoding_detected"] in ("utf-8", "utf-8-sig")
    assert data["total_chapters"] >= 4
    assert data["chapters"][0]["title"] == "第一章 初入江湖"
    # Check volume detection
    vol_ch = next(c for c in data["chapters"] if c["volume_name"])
    assert "卷" in vol_ch["volume_name"]


# === Parse ===


@pytest.mark.asyncio
async def test_parse_creates_chapters(client):
    doc_id = await _upload_doc(client)
    resp = await client.post(f"/api/v1/documents/{doc_id}/chapters/parse")
    assert resp.status_code == 200
    chapters = resp.json()
    assert len(chapters) >= 4
    assert chapters[0]["title"] == "第一章 初入江湖"
    assert chapters[0]["chapter_index"] == 0
    assert chapters[0]["word_count"] > 0
    assert chapters[0]["parse_source"] == "auto"


@pytest.mark.asyncio
async def test_parse_idempotent(client):
    """Parsing twice should not create duplicate chapters."""
    doc_id = await _upload_doc(client)
    resp1 = await client.post(f"/api/v1/documents/{doc_id}/chapters/parse")
    resp2 = await client.post(f"/api/v1/documents/{doc_id}/chapters/parse")
    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert len(resp1.json()) == len(resp2.json())


@pytest.mark.asyncio
async def test_parse_no_chapters_detected(client):
    plain = "This is plain text without any chapter markers at all. " * 10
    doc_id = await _upload_doc(client, plain)
    resp = await client.post(f"/api/v1/documents/{doc_id}/chapters/parse")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["title"] == "全文"


@pytest.mark.asyncio
async def test_parse_chinese_numerals(client):
    content = """第十二章 测试一
内容一

第一百二十三章 测试二
内容二

第一千二百三十四章 测试三
内容三"""
    doc_id = await _upload_doc(client, content)
    resp = await client.post(f"/api/v1/documents/{doc_id}/chapters/parse")
    assert resp.status_code == 200
    chapters = resp.json()
    assert len(chapters) == 3
    assert "十二" in chapters[0]["title"]


@pytest.mark.asyncio
async def test_parse_arabic_numerals(client):
    content = """第一章 测试A
内容A

第10章 测试B
内容B

第99章 测试C
内容C"""
    doc_id = await _upload_doc(client, content)
    resp = await client.post(f"/api/v1/documents/{doc_id}/chapters/parse")
    assert resp.status_code == 200
    assert len(resp.json()) == 3


@pytest.mark.asyncio
async def test_parse_special_chapters(client):
    content = """序章 引子
这是序章内容。

第一章 正式开始
正文内容。

番外 后日谈
番外内容。"""
    doc_id = await _upload_doc(client, content)
    resp = await client.post(f"/api/v1/documents/{doc_id}/chapters/parse")
    assert resp.status_code == 200
    chapters = resp.json()
    assert len(chapters) == 3
    titles = [c["title"] for c in chapters]
    assert any("序章" in t for t in titles)
    assert any("番外" in t for t in titles)


@pytest.mark.asyncio
async def test_parse_encoding_error(client):
    # Create a document with a valid file first
    doc_id = await _upload_doc(client, "测试内容", name="test.txt")
    # Replace the stored file with bytes that fail all decodings
    from pathlib import Path

    from app.db.models import SourceDocument
    from app.db.session import async_session_factory

    async with async_session_factory() as session:
        doc = await session.get(SourceDocument, doc_id)
        # Write bytes that are invalid in all common encodings
        # These are invalid UTF-8 sequences
        Path(doc.storage_path).write_bytes(bytes([0xFF, 0xFE, 0xFD, 0xFC, 0xFB]))
        await session.commit()

    resp = await client.get(f"/api/v1/documents/{doc_id}/chapters/parse-preview")
    # Should either fail with encoding error or succeed with fallback
    assert resp.status_code in (200, 400)


# === List / Detail ===


@pytest.mark.asyncio
async def test_list_chapters(client):
    doc_id = await _upload_doc(client)
    await client.post(f"/api/v1/documents/{doc_id}/chapters/parse")
    resp = await client.get(f"/api/v1/documents/{doc_id}/chapters")
    assert resp.status_code == 200
    chapters = resp.json()
    assert len(chapters) >= 4
    # Verify order
    for i in range(len(chapters) - 1):
        assert chapters[i]["chapter_index"] <= chapters[i + 1]["chapter_index"]


@pytest.mark.asyncio
async def test_get_chapter_detail(client):
    doc_id = await _upload_doc(client)
    await client.post(f"/api/v1/documents/{doc_id}/chapters/parse")
    chapters = (await client.get(f"/api/v1/documents/{doc_id}/chapters")).json()
    ch_id = chapters[0]["id"]
    resp = await client.get(f"/api/v1/documents/{doc_id}/chapters/{ch_id}")
    assert resp.status_code == 200
    assert "content" in resp.json()
    assert "林辰" in resp.json()["content"]


# === Update (rename, reorder, volume, mark) ===


@pytest.mark.asyncio
async def test_update_chapter_rename(client):
    doc_id = await _upload_doc(client)
    await client.post(f"/api/v1/documents/{doc_id}/chapters/parse")
    chapters = (await client.get(f"/api/v1/documents/{doc_id}/chapters")).json()
    ch_id = chapters[0]["id"]
    resp = await client.patch(
        f"/api/v1/documents/{doc_id}/chapters/{ch_id}",
        json={"title": "新的章节名"},
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "新的章节名"


@pytest.mark.asyncio
async def test_update_chapter_volume(client):
    doc_id = await _upload_doc(client)
    await client.post(f"/api/v1/documents/{doc_id}/chapters/parse")
    chapters = (await client.get(f"/api/v1/documents/{doc_id}/chapters")).json()
    ch_id = chapters[0]["id"]
    resp = await client.patch(
        f"/api/v1/documents/{doc_id}/chapters/{ch_id}",
        json={"volume_name": "特别篇", "parse_source": "manual"},
    )
    assert resp.status_code == 200
    assert resp.json()["volume_name"] == "特别篇"
    assert resp.json()["parse_source"] == "manual"


@pytest.mark.asyncio
async def test_update_chapter_reorder(client):
    doc_id = await _upload_doc(client)
    await client.post(f"/api/v1/documents/{doc_id}/chapters/parse")
    chapters = (await client.get(f"/api/v1/documents/{doc_id}/chapters")).json()
    # Swap first two
    ch0_id, ch1_id = chapters[0]["id"], chapters[1]["id"]
    await client.patch(f"/api/v1/documents/{doc_id}/chapters/{ch0_id}", json={"chapter_index": 1})
    await client.patch(f"/api/v1/documents/{doc_id}/chapters/{ch1_id}", json={"chapter_index": 0})
    updated = (await client.get(f"/api/v1/documents/{doc_id}/chapters")).json()
    assert updated[0]["id"] == ch1_id
    assert updated[1]["id"] == ch0_id


# === Merge ===


@pytest.mark.asyncio
async def test_merge_chapters(client):
    doc_id = await _upload_doc(client)
    await client.post(f"/api/v1/documents/{doc_id}/chapters/parse")
    chapters = (await client.get(f"/api/v1/documents/{doc_id}/chapters")).json()
    assert len(chapters) >= 4
    ch1_id, ch2_id = chapters[0]["id"], chapters[1]["id"]

    resp = await client.post(
        f"/api/v1/documents/{doc_id}/chapters/merge",
        json={"chapter_ids": [ch1_id, ch2_id], "new_title": "合并章节"},
    )
    assert resp.status_code == 200
    merged = resp.json()
    assert merged["title"] == "合并章节"
    assert merged["parse_source"] == "manual"
    # Verify total count decreased
    remaining = (await client.get(f"/api/v1/documents/{doc_id}/chapters")).json()
    assert len(remaining) == len(chapters) - 1


@pytest.mark.asyncio
async def test_merge_preserves_order(client):
    doc_id = await _upload_doc(client)
    await client.post(f"/api/v1/documents/{doc_id}/chapters/parse")
    chapters = (await client.get(f"/api/v1/documents/{doc_id}/chapters")).json()
    ch1_id, ch2_id = chapters[0]["id"], chapters[1]["id"]

    await client.post(
        f"/api/v1/documents/{doc_id}/chapters/merge",
        json={"chapter_ids": [ch1_id, ch2_id]},
    )
    remaining = (await client.get(f"/api/v1/documents/{doc_id}/chapters")).json()
    # Verify sequential indices
    for i, ch in enumerate(remaining):
        assert ch["chapter_index"] == i


# === Split ===


@pytest.mark.asyncio
async def test_split_chapter(client):
    doc_id = await _upload_doc(client)
    await client.post(f"/api/v1/documents/{doc_id}/chapters/parse")
    chapters = (await client.get(f"/api/v1/documents/{doc_id}/chapters")).json()
    ch_id = chapters[0]["id"]
    original_count = len(chapters)

    # Get content to find a good split point
    detail = (await client.get(f"/api/v1/documents/{doc_id}/chapters/{ch_id}")).json()
    mid = len(detail["content"]) // 2

    resp = await client.post(
        f"/api/v1/documents/{doc_id}/chapters/{ch_id}/split",
        json={"split_position": mid, "new_title": "下半部分"},
    )
    assert resp.status_code == 200
    split_result = resp.json()
    assert len(split_result) == 2
    assert split_result[0]["id"] == ch_id
    assert split_result[1]["title"] == "下半部分"

    remaining = (await client.get(f"/api/v1/documents/{doc_id}/chapters")).json()
    assert len(remaining) == original_count + 1


@pytest.mark.asyncio
async def test_split_invalid_position(client):
    doc_id = await _upload_doc(client)
    await client.post(f"/api/v1/documents/{doc_id}/chapters/parse")
    chapters = (await client.get(f"/api/v1/documents/{doc_id}/chapters")).json()
    ch_id = chapters[0]["id"]
    detail = (await client.get(f"/api/v1/documents/{doc_id}/chapters/{ch_id}")).json()

    resp = await client.post(
        f"/api/v1/documents/{doc_id}/chapters/{ch_id}/split",
        json={"split_position": len(detail["content"]) + 10, "new_title": "bad"},
    )
    assert resp.status_code == 400


# === Delete ===


@pytest.mark.asyncio
async def test_delete_chapter(client):
    doc_id = await _upload_doc(client)
    await client.post(f"/api/v1/documents/{doc_id}/chapters/parse")
    chapters = (await client.get(f"/api/v1/documents/{doc_id}/chapters")).json()
    original_count = len(chapters)
    ch_id = chapters[-1]["id"]

    resp = await client.delete(f"/api/v1/documents/{doc_id}/chapters/{ch_id}")
    assert resp.status_code == 204

    remaining = (await client.get(f"/api/v1/documents/{doc_id}/chapters")).json()
    assert len(remaining) == original_count - 1
    # Verify reindexing
    for i, ch in enumerate(remaining):
        assert ch["chapter_index"] == i


# === Volume detection ===


@pytest.mark.asyncio
async def test_volume_detection(client):
    doc_id = await _upload_doc(client)
    resp = await client.get(f"/api/v1/documents/{doc_id}/chapters/parse-preview")
    chapters = resp.json()["chapters"]
    # Chapter 1-3 should be in 第一卷, Chapter 4 in 第二卷
    vol1 = [c for c in chapters if c["volume_name"] and "一" in c["volume_name"]]
    vol2 = [c for c in chapters if c["volume_name"] and "二" in c["volume_name"]]
    assert len(vol1) >= 3
    assert len(vol2) >= 1
