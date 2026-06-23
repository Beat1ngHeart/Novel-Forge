import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "app" in data
    assert "database" in data
    assert "llm" in data


@pytest.mark.asyncio
async def test_system_info(client):
    resp = await client.get("/api/v1/system/info")
    assert resp.status_code == 200
    data = resp.json()
    assert data["app_name"] == "Novel Forge"
    assert data["llm_provider"] == "mock"


@pytest.mark.asyncio
async def test_system_health(client):
    resp = await client.get("/api/v1/system/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "version" in data
    assert "dependencies" in data
    assert "database" in data["dependencies"]
    assert "llm" in data["dependencies"]
    assert data["dependencies"]["llm"]["status"] in ("ok", "healthy")
