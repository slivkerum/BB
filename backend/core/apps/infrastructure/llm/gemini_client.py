import anyio
import google.generativeai as genai

from dataclasses import dataclass
from typing import Sequence

from backend.core.apps.interfaces.ports.llm_gateway import (
    LLMGateway,
    LLMMessage,
    LLMResult
)



@dataclass
class FakeGemini(LLMGateway):
    async def generate(self, messages: Sequence[LLMMessage], max_tokens=None, temperature=None) -> LLMResult:
        last_user = next((m.content for m in reversed(messages) if m.role == "user"), "")
        return LLMResult(text=f"[FAKE GEMINI] Ты сказал: {last_user}")


@dataclass
class GeminiGateway(LLMGateway):
    api_key: str
    model_name: str = "gemini-1.5-flash"
    system_instruction: str = "You are a helpful, concise assistant."

    async def generate(self, messages: Sequence[LLMMessage], max_tokens=None, temperature=None) -> LLMResult:
        def _run_sync() -> str:
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=self.system_instruction,
            )
            # Склеим в один промпт (просто и надёжно). Хотим chat-history — можно собрать parts.
            prompt = "\n".join([f"{m.role.upper()}: {m.content}" for m in messages])
            resp = model.generate_content(
                prompt,
                generation_config={
                    "max_output_tokens": max_tokens,
                    "temperature": temperature,
                },
            )
            return resp.text or ""
        text = await anyio.to_thread.run_sync(_run_sync)
        return LLMResult(text=text)