from dataclasses import dataclass
from aiogram import Router, F, types
from backend.core.apps.use_cases.reset_session import ResetSession, ResetSessionInput

@dataclass
class ResetRouterFactory:
    use_case: ResetSession

    def build(self) -> Router:
        r = Router()

        @r.message(F.text.regexp(r"^/reset(?:@\w+)?$"))
        async def on_reset(m: types.Message):
            await self.use_case(ResetSessionInput(chat_id=m.chat.id))
            await m.answer("Сессия очищена ✅")

        return r
