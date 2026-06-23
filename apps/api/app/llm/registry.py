"""LLM Provider registry — resolves provider name to implementation.

Business code must call get_llm_provider() to obtain a provider instance.
Never instantiate vendor SDKs directly.
"""

from __future__ import annotations

import logging

from app.core.config import settings
from app.llm.base import LLMProvider
from app.llm.mock_provider import MockLLMProvider

logger = logging.getLogger(__name__)

_provider: LLMProvider | None = None


class ProviderNotAvailableError(Exception):
    """Raised when the configured LLM provider cannot be initialized."""


def get_llm_provider() -> LLMProvider:
    """Get the configured LLM provider. Cached as a singleton."""
    global _provider
    if _provider is not None:
        return _provider

    name = settings.LLM_PROVIDER.lower().strip()
    if not name:
        raise ProviderNotAvailableError("LLM_PROVIDER is not configured")

    if name == "mock":
        _provider = MockLLMProvider()
        logger.info("LLM provider initialized: mock")
    else:
        raise ProviderNotAvailableError(f"Unknown LLM_PROVIDER: {name!r}. Supported: mock")

    return _provider


def create_mock_provider(
    fail_rate: float = 0.0,
    timeout_rate: float = 0.0,
    rate_limit_rate: float = 0.0,
    latency_ms: int = 100,
) -> MockLLMProvider:
    """Create a mock provider with custom simulation parameters (for testing)."""
    return MockLLMProvider(
        fail_rate=fail_rate,
        timeout_rate=timeout_rate,
        rate_limit_rate=rate_limit_rate,
        simulate_latency_ms=latency_ms,
    )


def reset_provider() -> None:
    """Reset the cached provider (useful for tests)."""
    global _provider
    _provider = None
