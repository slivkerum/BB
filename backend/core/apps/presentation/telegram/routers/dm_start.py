from dataclasses import dataclass
from aiogram import Router, types, F
from backend.core.apps.interfaces.ports.member_repo import MemberRepository
from backend.core.apps.domain.entities.event import Member

@dataclass
class DMStartRouterFactory:
    members: MemberRepository

    def build(self) -> Router:
        r = Router()

        @r.message(F.chat.type == "private", F.text == "/start")
        async def _start(m: types.Message):
            await self.members.upsert(Member(
                user_id=m.from_user.id,
                display_name=m.from_user.full_name,
                username=m.from_user.username,
                can_dm=True,
            ))
            await self.members.touch_activity(m.from_user.id)
            await m.answer("Привет! Я буду присылать тебе личные напоминания о событиях, если ты отметишься как «Иду».")

        return r
