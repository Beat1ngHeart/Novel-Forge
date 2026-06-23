from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    content: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = ""
    provider: str = ""


@dataclass
class TokenCount:
    count: int = 0
    model: str = ""


class LLMProvider(ABC):
    """Unified LLM provider interface.

    All business code must use this interface, never vendor SDKs directly.
    """

    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse: ...

    @abstractmethod
    async def structured_output(
        self,
        messages: list[dict[str, str]],
        schema: dict,
        temperature: float = 0.3,
    ) -> LLMResponse: ...

    @abstractmethod
    async def embedding(self, texts: list[str]) -> list[list[float]]: ...

    @abstractmethod
    async def count_tokens(self, text: str) -> TokenCount: ...

    @abstractmethod
    async def health_check(self) -> dict: ...

    def get_provider_name(self) -> str:
        """Return the provider name for logging."""
        return "unknown"

    def get_model_name(self) -> str:
        """Return the model name for logging."""
        return "unknown"
