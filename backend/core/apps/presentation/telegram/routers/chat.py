from dataclasses import dataclass

from aiogram import F, Router, types

from backend.core.apps.use_cases.generate_reply import GenerateReply, GenerateReplyInput


@dataclass
class ChatRouterFactory:
    use_case: GenerateReply

    def build(self) -> Router:
        router = Router()

        @router.message(F.text & ~F.text.startswith("/"))
        async def on_message(msg: types.Message):
            out = await self.use_case(GenerateReplyInput(chat_id=msg.chat.id, user_text=msg.text))
            await msg.answer(out.reply_text)

        return router
