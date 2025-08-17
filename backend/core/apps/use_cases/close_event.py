from dataclasses import dataclass
from aiogram import Bot
from backend.core.apps.interfaces.ports.event_repo import EventRepository
from backend.core.apps.interfaces.ports.scheduler import Scheduler
from backend.core.apps.interfaces.ports.reminder_msg_repo import ReminderMessageRepository


@dataclass
class CloseEventInput:
    event_id: int


@dataclass
class CloseEvent:
    events: EventRepository
    scheduler: Scheduler
    bot: Bot
    reminders: ReminderMessageRepository

    async def __call__(self, data: CloseEventInput) -> None:
        # 1) закрываем и отменяем будущие JOB'ы
        await self.events.close(data.event_id)
        await self.scheduler.cancel_for_event(data.event_id)

        # 2) удаляем все уже отправленные напоминания
        msgs = await self.reminders.list_by_event(data.event_id)
        for chat_id, message_id in msgs:
            try:
                await self.bot.delete_message(chat_id, message_id)
            except Exception:
                # сообщение уже удалено/нет прав — пропускаем
                pass
        await self.reminders.delete_for_event(data.event_id)
