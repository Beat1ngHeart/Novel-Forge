"""LLM call logger — records every LLM call to llm_call_logs table."""

from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncGenerator

import app.db.session as db_session_module
from app.db.models import LLMCallLog

logger = logging.getLogger(__name__)


@dataclass
class CallLogContext:
    """Mutable context passed through an LLM call for recording."""

    log_id: str
    provider: str
    model: str
    task_type: str
    prompt_version: str
    start_time: float
    status: str = "pending"
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost: float = 0.0
    error_message: str = ""


@asynccontextmanager
async def track_llm_call(
    provider: str,
    model: str,
    task_type: str,
    prompt_version: str = "",
) -> AsyncGenerator[CallLogContext, None]:
    """Context manager that tracks an LLM call and writes a log entry on exit.

    Usage:
        async with track_llm_call("mock", "mock-model", "chat") as ctx:
            response = await provider.chat(messages)
            ctx.input_tokens = response.input_tokens
            ctx.output_tokens = response.output_tokens
            ctx.status = "success"
    """
    ctx = CallLogContext(
        log_id=str(uuid.uuid4()),
        provider=provider,
        model=model,
        task_type=task_type,
        prompt_version=prompt_version,
        start_time=time.monotonic(),
    )

    try:
        yield ctx
    except Exception as e:
        ctx.status = "failed"
        ctx.error_message = str(e)[:2000]
        raise
    finally:
        latency_ms = int((time.monotonic() - ctx.start_time) * 1000)
        try:
            async with db_session_module.async_session_factory() as session:
                log_entry = LLMCallLog(
                    id=ctx.log_id,
                    provider=ctx.provider,
                    model=ctx.model,
                    task_type=ctx.task_type,
                    prompt_version=ctx.prompt_version,
                    status=ctx.status,
                    input_tokens=ctx.input_tokens,
                    output_tokens=ctx.output_tokens,
                    estimated_cost=ctx.estimated_cost,
                    latency_ms=latency_ms,
                    error_message=ctx.error_message,
                )
                session.add(log_entry)
                await session.commit()
        except Exception:
            logger.exception("Failed to write LLM call log")
