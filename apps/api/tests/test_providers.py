"""Tests for LLM provider endpoints and mock provider behavior."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.llm.registry import reset_provider
from app.main import app


@pytest.fixture(autouse=True)
def _reset_provider():
    """Reset provider singleton between tests."""
    reset_provider()
    yield
    reset_provider()


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


# === Provider listing ===


@pytest.mark.asyncio
async def test_list_providers(client):
    resp = await client.get("/api/v1/providers")
    assert resp.status_code == 200
    providers = resp.json()
    assert len(providers) >= 1
    assert providers[0]["name"] == "mock"
    assert providers[0]["status"] == "available"


@pytest.mark.asyncio
async def test_provider_health(client):
    resp = await client.get("/api/v1/providers/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["provider"] == "mock"
    assert data["latency_ms"] >= 0


# === Mock test endpoint ===


@pytest.mark.asyncio
async def test_mock_test_success(client):
    resp = await client.post(
        "/api/v1/providers/mock/test",
        json={"test_type": "success", "message": "测试消息"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["test_type"] == "success"
    assert data["response"] is not None
    assert data["latency_ms"] >= 0
    assert data["log_id"] is not None


@pytest.mark.asyncio
async def test_mock_test_failure(client):
    resp = await client.post(
        "/api/v1/providers/mock/test",
        json={"test_type": "failure"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert "Connection error" in data["error"]


@pytest.mark.asyncio
async def test_mock_test_timeout(client):
    resp = await client.post(
        "/api/v1/providers/mock/test",
        json={"test_type": "timeout"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert "Timeout" in data["error"]


@pytest.mark.asyncio
async def test_mock_test_rate_limit(client):
    resp = await client.post(
        "/api/v1/providers/mock/test",
        json={"test_type": "rate_limit"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert "Rate limited" in data["error"]


@pytest.mark.asyncio
async def test_mock_test_invalid_type(client):
    resp = await client.post(
        "/api/v1/providers/mock/test",
        json={"test_type": "invalid"},
    )
    assert resp.status_code == 400


# === Call logs ===


@pytest.mark.asyncio
async def test_call_logs_created_on_mock_test(client):
    # Run a success test
    await client.post(
        "/api/v1/providers/mock/test",
        json={"test_type": "success", "message": "log test"},
    )

    # Check call logs
    resp = await client.get("/api/v1/providers/logs")
    assert resp.status_code == 200
    logs = resp.json()
    assert len(logs) >= 1
    # Find our log
    test_log = next((entry for entry in logs if entry["task_type"] == "mock_test"), None)
    assert test_log is not None
    assert test_log["provider"] == "mock"
    assert test_log["status"] == "success"
    assert test_log["input_tokens"] > 0
    assert test_log["latency_ms"] >= 0


@pytest.mark.asyncio
async def test_call_logs_on_failure(client):
    await client.post(
        "/api/v1/providers/mock/test",
        json={"test_type": "failure"},
    )

    resp = await client.get("/api/v1/providers/logs")
    logs = resp.json()
    # Find the failed log
    failed_log = next(
        (entry for entry in logs if entry["task_type"] == "mock_test" and entry["status"] == "failed"),
        None,
    )
    # Note: the log may be "success" if the mock didn't fail on the tracked call
    # but the endpoint returns success=False. The log tracks the actual LLM call.
    # Since we use track_llm_call which catches the exception, the status should be "failed".
    assert failed_log is not None
    assert failed_log["error_message"] != ""
