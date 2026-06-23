"""Provider routes — list providers, health check, mock testing."""

from __future__ import annotations

import logging
import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import LLMCallLog
from app.db.session import get_session
from app.llm.call_logger import track_llm_call
from app.llm.mock_provider import MockConnectionError, MockRateLimitError, MockTimeoutError
from app.llm.registry import ProviderNotAvailableError, create_mock_provider, get_llm_provider
from app.schemas.provider import (
    CallLogOut,
    MockTestRequest,
    MockTestResponse,
    ProviderHealthResponse,
    ProviderInfo,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/providers", tags=["providers"])

DB = Annotated[AsyncSession, Depends(get_session)]


@router.get("", response_model=list[ProviderInfo])
async def list_providers():
    """List available LLM providers and their current status."""
    providers = []
    try:
        get_llm_provider()  # verify it's available
        providers.append(
            ProviderInfo(
                name=settings.LLM_PROVIDER,
                model=settings.LLM_MODEL,
                status="available",
            )
        )
    except ProviderNotAvailableError as e:
        providers.append(
            ProviderInfo(
                name=settings.LLM_PROVIDER,
                model=settings.LLM_MODEL,
                status="unavailable",
                details={"error": str(e)},
            )
        )
    return providers


@router.get("/health", response_model=ProviderHealthResponse)
async def provider_health():
    """Check the health of the current LLM provider."""
    try:
        provider = get_llm_provider()
        start = time.monotonic()
        await provider.health_check()  # verify connectivity
        latency = int((time.monotonic() - start) * 1000)
        return ProviderHealthResponse(
            status="ok",
            provider=settings.LLM_PROVIDER,
            model=settings.LLM_MODEL,
            latency_ms=latency,
        )
    except ProviderNotAvailableError as e:
        return ProviderHealthResponse(
            status="unavailable",
            provider=settings.LLM_PROVIDER,
            model=settings.LLM_MODEL,
            error=str(e),
        )
    except Exception as e:
        return ProviderHealthResponse(
            status="error",
            provider=settings.LLM_PROVIDER,
            model=settings.LLM_MODEL,
            error=str(e),
        )


@router.post("/mock/test", response_model=MockTestResponse)
async def mock_test(req: MockTestRequest):
    """Test the mock provider with different simulation modes.

    test_type: success | failure | timeout | rate_limit
    """
    if settings.LLM_PROVIDER != "mock":
        raise HTTPException(
            status_code=400,
            detail="Mock test endpoint is only available when LLM_PROVIDER=mock",
        )

    # Create a provider with the requested behavior
    if req.test_type == "success":
        provider = create_mock_provider()
    elif req.test_type == "failure":
        provider = create_mock_provider(fail_rate=1.0)
    elif req.test_type == "timeout":
        provider = create_mock_provider(timeout_rate=1.0)
    elif req.test_type == "rate_limit":
        provider = create_mock_provider(rate_limit_rate=1.0)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown test_type: {req.test_type!r}. Use: success, failure, timeout, rate_limit",
        )

    start = time.monotonic()
    try:
        async with track_llm_call("mock", "mock-novel-model", "mock_test") as ctx:
            response = await provider.chat(messages=[{"role": "user", "content": req.message}])
            ctx.input_tokens = response.input_tokens
            ctx.output_tokens = response.output_tokens
            ctx.status = "success"

        latency = int((time.monotonic() - start) * 1000)
        return MockTestResponse(
            success=True,
            test_type=req.test_type,
            response=response.content,
            latency_ms=latency,
            log_id=ctx.log_id,
        )
    except MockConnectionError as e:
        latency = int((time.monotonic() - start) * 1000)
        return MockTestResponse(
            success=False,
            test_type=req.test_type,
            error=f"Connection error: {e}",
            latency_ms=latency,
        )
    except MockTimeoutError as e:
        latency = int((time.monotonic() - start) * 1000)
        return MockTestResponse(
            success=False,
            test_type=req.test_type,
            error=f"Timeout: {e}",
            latency_ms=latency,
        )
    except MockRateLimitError as e:
        latency = int((time.monotonic() - start) * 1000)
        return MockTestResponse(
            success=False,
            test_type=req.test_type,
            error=f"Rate limited: {e}",
            latency_ms=latency,
        )
    except Exception as e:
        latency = int((time.monotonic() - start) * 1000)
        return MockTestResponse(
            success=False,
            test_type=req.test_type,
            error=f"Unexpected error: {e}",
            latency_ms=latency,
        )


@router.get("/logs", response_model=list[CallLogOut])
async def list_call_logs(session: DB, limit: int = 50):
    """List recent LLM call logs."""
    result = await session.execute(select(LLMCallLog).order_by(LLMCallLog.created_at.desc()).limit(limit))
    return result.scalars().all()
