from dataclasses import dataclass

from aiogram import F, Router, types


@dataclass
class HelpRouterFactory:
    def build(self) -> Router:
        r = Router()

        @r.message(F.text == "/help")
        async def help_msg(m: types.Message):
            await m.answer(
                "Команды:\n"
                "/new_event — запустить создание события\n"
                "/reset — сбросить ИИ-сессию\n"
                "/help — помощь\n\n"
                "Под карточками событий доступны кнопки: Я пойду / Не могу / Список / Закрыть"
            )

        return r
