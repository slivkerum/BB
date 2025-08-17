from dataclasses import dataclass
from aiogram import Router, types, F
from zoneinfo import ZoneInfo
from backend.core.apps.config.settings import settings
from datetime import datetime
from backend.core.apps.use_cases.publish_event import PublishEvent, PublishEventInput, event_keyboard
from backend.core.apps.use_cases.register_for_event import RegisterForEvent, ToggleGoingInput, ToggleDeclineInput
from backend.core.apps.interfaces.ports.event_repo import EventRepository
from backend.core.apps.use_cases.close_event import CloseEvent, CloseEventInput


@dataclass
class EventsRouterFactory:
    publish_uc: PublishEvent
    register_uc: RegisterForEvent
    events_repo: EventRepository
    close_uc: CloseEvent | None = None

    def build(self) -> Router:
        r = Router()

        @r.message(F.text.startswith("/event_quick"))
        async def event_quick(m: types.Message):
            try:
                _, payload = m.text.split(" ", 1)
                title, place, category, starts = [p.strip() for p in payload.split("|")]
                starts_at = datetime.fromisoformat(starts)
                if starts_at.tzinfo is None:
                    starts_at = starts_at.replace(tzinfo=ZoneInfo(settings.TZ))
                else:
                    starts_at = starts_at.astimezone(ZoneInfo(settings.TZ))
            except Exception:
                await m.reply("Формат: /event_quick <title> | <place> | <category> | <YYYY-MM-DD HH:MM>")
                return

            data = PublishEventInput(
                chat_id=m.chat.id,
                organizer_id=m.from_user.id,
                title=title,
                place=place,
                category=category,
                starts_at=starts_at,
            )
            evt = await self.publish_uc.create(data)
            text = await self.publish_uc.build_text(evt)
            sent = await m.answer(text, reply_markup=event_keyboard(evt.id), disable_web_page_preview=True)
            evt.message_id = sent.message_id
            await self.publish_uc.events.update(evt)
            await self.publish_uc.finalize_and_schedule(evt)

        @r.callback_query(F.data.regexp(r"^e:(\d+):g$"))
        async def on_going(cb: types.CallbackQuery):
            event_id = int(cb.data.split(":")[1])
            changed, payload = await self.register_uc.toggle_going(
                event_id,
                ToggleGoingInput(
                    chat_id=cb.message.chat.id,
                    message_id=cb.message.message_id,
                    user_id=cb.from_user.id,
                    user_name=cb.from_user.full_name,
                    user_username=cb.from_user.username,
                ),
            )
            if changed:
                await cb.message.edit_text(payload, reply_markup=event_keyboard(event_id),
                                           disable_web_page_preview=True)
                await cb.answer("Записал: идёшь!")
            else:
                await cb.answer(payload)

        @r.callback_query(F.data.regexp(r"^e:(\d+):d$"))
        async def on_decline(cb: types.CallbackQuery):
            event_id = int(cb.data.split(":")[1])
            changed, payload = await self.register_uc.toggle_decline(
                event_id,
                ToggleDeclineInput(
                    chat_id=cb.message.chat.id,
                    message_id=cb.message.message_id,
                    user_id=cb.from_user.id,
                    user_name=cb.from_user.full_name,
                    user_username=cb.from_user.username,
                ),
            )
            if changed:
                await cb.message.edit_text(payload, reply_markup=event_keyboard(event_id),
                                           disable_web_page_preview=True)
                await cb.answer("Ок, не идёшь.")
            else:
                await cb.answer(payload)

        @r.callback_query(F.data.regexp(r"^e:(\d+):l$"))
        async def on_list(cb: types.CallbackQuery):
            event_id = int(cb.data.split(":")[1])
            evt = await self.events_repo.get(event_id)
            if not evt:
                await cb.answer("Событие не найдено", show_alert=True)
                return

            await cb.answer("Обновил список")

        @r.callback_query(F.data.regexp(r"^e:(\d+):c$"))
        async def on_close(cb: types.CallbackQuery):
            event_id = int(cb.data.split(":")[1])

            if self.close_uc:
                await self.close_uc(CloseEventInput(event_id=event_id))

            try:
                await cb.message.delete()
            except Exception:
                pass

            await cb.answer("Событие закрыто и удалено ✅")

        return r