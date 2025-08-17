from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from backend.core.apps.config.settings import settings
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from backend.core.apps.domain.entities.event import Event
from backend.core.apps.interfaces.ports.event_repo import EventRepository
from backend.core.apps.interfaces.ports.registration_repo import RegistrationRepository
from backend.core.apps.presentation.telegram.presenters.event_card import EventCardPresenter


def event_keyboard(event_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Я пойду", callback_data=f"e:{event_id}:g"),
            InlineKeyboardButton(text="Не могу", callback_data=f"e:{event_id}:d"),
            InlineKeyboardButton(text="Список", callback_data=f"e:{event_id}:l"),
        ],
        [
            InlineKeyboardButton(text="Закрыть", callback_data=f"e:{event_id}:c"),
        ]
    ])


@dataclass
class PublishEventInput:
    chat_id: int
    organizer_id: int
    title: str
    place: str
    category: str
    starts_at: datetime
    capacity: int | None = None
    cost_policy: str | None = None
    notes: str | None = None


@dataclass
class PublishEventOutput:
    event_id: int
    message_text: str


@dataclass
class PublishEvent:
    events: EventRepository
    regs: RegistrationRepository
    presenter: EventCardPresenter
    scheduler: any = None

    async def build_text(self, evt: Event) -> str:
        return self.presenter.render(evt, [], [])

    async def create(self, data: PublishEventInput) -> Event:
        evt = Event(
            id=None,
            chat_id=data.chat_id,
            message_id=None,
            title=data.title,
            place=data.place,
            category=data.category,
            starts_at=data.starts_at,
            organizer_id=data.organizer_id,
            capacity=data.capacity,
            cost_policy=data.cost_policy,
            notes=data.notes,
        )
        return await self.events.create(evt)

    async def set_message_id(self, evt: Event, message_id: int) -> None:
        evt.message_id = message_id
        await self.events.update(evt)

    async def finalize_and_schedule(self, evt: Event) -> None:
        if not self.scheduler:
            return

        local_tz = ZoneInfo(settings.TZ)
        starts_local = evt.starts_at.astimezone(local_tz)

        t1 = starts_local - timedelta(hours=24)
        t2 = starts_local - timedelta(minutes=30)
        now_local = datetime.now(local_tz)
        when_list = [t for t in (t1, t2) if t > now_local]

        if when_list:
            await self.scheduler.schedule_event_reminders(evt.id, when_list)

        if starts_local > now_local:
            await self.scheduler.schedule_event_expiry(evt.id, starts_local)
