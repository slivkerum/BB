from dataclasses import dataclass

from aiogram import Bot

from backend.core.apps.interfaces.ports.event_repo import EventRepository
from backend.core.apps.interfaces.ports.reminder_msg_repo import ReminderMessageRepository
from backend.core.apps.interfaces.ports.scheduler import Scheduler


@dataclass
class ExpireEventInput:
    event_id: int


@dataclass
class ExpireEvent:
    events: EventRepository
    scheduler: Scheduler
    bot: Bot
    reminders: ReminderMessageRepository

    async def __call__(self, data: ExpireEventInput) -> None:
        evt = await self.events.get(data.event_id)
        if not evt:
            return

        # отменим все будущие задачи (на всякий)
        await self.scheduler.cancel_for_event(data.event_id)

        # удалим карточку события (если ещё висит)
        if evt.message_id:
            try:
                await self.bot.delete_message(evt.chat_id, evt.message_id)
            except Exception:
                pass

        # удалим все уже отправленные напоминания
        msgs = await self.reminders.list_by_event(data.event_id)
        for chat_id, message_id in msgs:
            try:
                await self.bot.delete_message(chat_id, message_id)
            except Exception:
                pass
        await self.reminders.delete_for_event(data.event_id)

        # закроем событие
        await self.events.close(data.event_id)
