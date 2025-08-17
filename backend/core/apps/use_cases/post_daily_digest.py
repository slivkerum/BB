from dataclasses import dataclass
from backend.core.apps.interfaces.ports.llm_gateway import LLMGateway, LLMMessage
from aiogram import Bot
from datetime import datetime


@dataclass
class PostDailyDigest:
    bot: Bot
    llm: LLMGateway
    system_prompt: str

    async def __call__(self, chat_id: int) -> None:
        today = datetime.now().strftime("%Y-%m-%d")
        messages = [
            LLMMessage("system", self.system_prompt),
            LLMMessage("user", f"Сгенерируй короткую бодрую утреннюю заметку для группы друзей на {today}. "
                               f"2-3 предложения. Без эмодзи, на русском, без перечислений."),
        ]
        res = await self.llm.generate(messages, max_tokens=180, temperature=0.7)
        await self.bot.send_message(chat_id, "🌅 Утренний пост:\n\n" + res.text)
