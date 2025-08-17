from dataclasses import dataclass
from aiogram import Bot
from backend.core.apps.interfaces.ports.event_repo import EventRepository
from backend.core.apps.interfaces.ports.registration_repo import RegistrationRepository
from backend.core.apps.presentation.telegram.presenters.event_card import EventCardPresenter
from backend.core.apps.interfaces.ports.reminder_msg_repo import ReminderMessageRepository

@dataclass
class SendEventReminder:
    bot: Bot
    events: EventRepository
    regs: RegistrationRepository
    presenter: EventCardPresenter
    reminders_repo: ReminderMessageRepository

    async def __call__(self, event_id: int) -> None:
        evt = await self.events.get(event_id)
        if not evt or evt.status == "closed":
            return

        all_map = await self.regs.get_all(event_id)
        going_ids = [uid for uid, st in all_map.items() if st == "going"]
        declined_ids = [uid for uid, st in all_map.items() if st == "declined"]
        going = [(uid, f"User {uid}") for uid in going_ids]
        declined = [(uid, f"User {uid}") for uid in declined_ids]
        text = "Напоминание ⏰\n\n" + self.presenter.render(evt, going, declined)

        msg = await self.bot.send_message(evt.chat_id, text, parse_mode="HTML", disable_web_page_preview=True)
        # сохраняем, чтобы при закрытии удалить
        await self.reminders_repo.add(event_id=event_id, chat_id=evt.chat_id, message_id=msg.message_id)
