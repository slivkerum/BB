from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class LLMMessage:
    role: str
    content: str


@dataclass(frozen=True)
class LLMResult:
    text: str
    tokens_input: int | None = None
    tokens_output: int | None = None
    latency_ms: int | None = None


class LLMGateway(ABC):
    @abstractmethod
    async def generate(
        self,
        messages: Sequence[LLMMessage],
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> LLMResult: ...
