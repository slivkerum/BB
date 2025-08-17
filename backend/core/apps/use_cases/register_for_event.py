from dataclasses import dataclass
from backend.core.apps.domain.entities.event import Registration, Member
from backend.core.apps.interfaces.ports.event_repo import EventRepository
from backend.core.apps.interfaces.ports.registration_repo import RegistrationRepository
from backend.core.apps.presentation.telegram.presenters.event_card import EventCardPresenter
from backend.core.apps.interfaces.ports.member_repo import MemberRepository


@dataclass
class ToggleGoingInput:
    chat_id: int
    message_id: int
    user_id: int
    user_name: str
    user_username: str | None = None


@dataclass
class ToggleDeclineInput:
    chat_id: int
    message_id: int
    user_id: int
    user_name: str
    user_username: str | None = None


@dataclass
class RegisterForEvent:
    events: EventRepository
    regs: RegistrationRepository
    presenter: EventCardPresenter
    members: MemberRepository

    async def _rebuild(self, event_id: int) -> str:
        evt = await self.events.get(event_id)
        if not evt:
            return "Событие не найдено."

        all_map = await self.regs.get_all(event_id)
        going_ids = [uid for uid, st in all_map.items() if st == "going"]
        declined_ids = [uid for uid, st in all_map.items() if st == "declined"]

        async def label(uid: int) -> tuple[int, str]:
            m = await self.members.get(uid)
            if m and m.username:
                return uid, f"@{m.username}"
            if m and m.display_name:
                return uid, m.display_name
            return uid, f"User {uid}"

        going = [await label(uid) for uid in going_ids]
        declined = [await label(uid) for uid in declined_ids]

        return self.presenter.render(evt, going, declined)

    async def toggle_going(self, event_id: int, data: ToggleGoingInput) -> tuple[bool, str]:
        await self.members.upsert(Member(
            user_id=data.user_id,
            display_name=data.user_name,
            username=data.user_username,
        ))
        await self.members.touch_activity(data.user_id)

        changed = await self.regs.set_status(Registration(event_id=event_id, user_id=data.user_id, status="going"))
        if not changed:
            return False, "Все еще красавчик"
        text = await self._rebuild(event_id)
        return True, text

    async def toggle_decline(self, event_id: int, data: ToggleDeclineInput) -> tuple[bool, str]:
        await self.members.upsert(Member(
            user_id=data.user_id,
            display_name=data.user_name,
            username=data.user_username,
        ))
        await self.members.touch_activity(data.user_id)

        changed = await self.regs.set_status(Registration(event_id=event_id, user_id=data.user_id, status="declined"))
        if not changed:
            return False, "Черт бляяя"
        text = await self._rebuild(event_id)
        return True, text
