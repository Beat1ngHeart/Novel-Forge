"""Provider schemas for API responses."""

from __future__ import annotations

from pydantic import BaseModel


class ProviderInfo(BaseModel):
    name: str
    model: str
    status: str
    details: dict = {}


class ProviderHealthResponse(BaseModel):
    status: str
    provider: str
    model: str
    latency_ms: int = 0
    error: str | None = None


class MockTestRequest(BaseModel):
    """Configure mock behavior for testing."""

    test_type: str = "success"  # success | failure | timeout | rate_limit
    message: str = "Hello, test message."


class MockTestResponse(BaseModel):
    success: bool
    test_type: str
    response: str | None = None
    error: str | None = None
    latency_ms: int = 0
    log_id: str | None = None


class CallLogOut(BaseModel):
    id: str
    provider: str
    model: str
    task_type: str
    prompt_version: str
    status: str
    input_tokens: int
    output_tokens: int
    estimated_cost: float
    latency_ms: int
    error_message: str

    model_config = {"from_attributes": True}
