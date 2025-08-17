# backend/core/apps/presentation/telegram/routers/events_wizard.py
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from backend.core.apps.config.settings import settings
from backend.core.apps.presentation.telegram.widgets.calendar import InlineCalendar
from backend.core.apps.use_cases.publish_event import (
    PublishEvent,
    PublishEventInput,
    event_keyboard,
)

PLACES = ["Набережная", "Парк", "Кинотеатр", "Кафе", "Спортзал"]
CATEGORIES = [
    ("Прогулка", "walk"),
    ("Кино", "cinema"),
    ("Кафе", "cafe"),
    ("Спорт", "sport"),
    ("Митап", "meetup"),
]


class NewEventFSM(StatesGroup):
    place = State()
    category = State()
    title = State()
    starts_date = State()
    starts_time = State()
    notes = State()


@dataclass
class EventsWizardRouterFactory:
    publish_uc: PublishEvent

    def build(self) -> Router:
        r = Router()

        @r.message(F.text == "/new_event")
        async def start(m: types.Message, state: FSMContext):
            if m.chat.type != "private":
                await m.answer(
                    "Создание событий только в ЛС. Напишите мне сюда 👉 @"
                    + (await m.bot.me()).username
                )
                return
            if not settings.EVENTS_CHAT_ID:
                await m.answer(
                    "Не задан EVENTS_CHAT_ID в .env — укажи ID группы, куда публиковать событие."
                )
                return
            kb = InlineKeyboardBuilder()
            for p in PLACES:
                kb.button(text=p, callback_data=f"w:place:{p}")
            kb.adjust(2)
            await state.clear()
            await state.set_state(NewEventFSM.place)
            await m.answer("Выбери место:", reply_markup=kb.as_markup())

        @r.callback_query(F.data.startswith("w:place:"), NewEventFSM.place)
        async def set_place(cb: types.CallbackQuery, state: FSMContext):
            place = cb.data.split("w:place:")[1]
            await state.update_data(place=place)
            kb = InlineKeyboardBuilder()
            for title, code in CATEGORIES:
                kb.button(text=title, callback_data=f"w:cat:{code}")
            kb.adjust(3)
            await state.set_state(NewEventFSM.category)
            await cb.message.edit_text(
                f"Место: <b>{place}</b>\nТеперь выбери тип:",
                parse_mode="HTML",
                reply_markup=kb.as_markup(),
            )
            await cb.answer()

        @r.callback_query(F.data.startswith("w:cat:"), NewEventFSM.category)
        async def set_category(cb: types.CallbackQuery, state: FSMContext):
            cat = cb.data.split("w:cat:")[1]
            await state.update_data(category=cat)
            await state.set_state(NewEventFSM.title)
            await cb.message.edit_text(
                f"Тип: <b>{cat}</b>\nВведи короткое название события:", parse_mode="HTML"
            )
            await cb.answer()

        @r.message(NewEventFSM.title)
        async def set_title(m: types.Message, state: FSMContext):
            await state.update_data(title=m.text.strip())
            # показать календарь текущего месяца
            today = datetime.now(ZoneInfo(settings.TZ)).date()
            cal = InlineCalendar(year=today.year, month=today.month)
            await state.set_state(NewEventFSM.starts_date)
            await m.answer("Выбери дату:", reply_markup=cal.markup())

        @r.callback_query(
            F.data.regexp(r"^cal:\d{4}-\d{2}:nav:(prev|next)$"), NewEventFSM.starts_date
        )
        async def cal_nav(cb: types.CallbackQuery, state: FSMContext):
            parts = cb.data.split(":")  # ['cal', 'YYYY-MM', 'nav', 'prev|next']
            ym = parts[1]
            direction = parts[3]
            year, month = map(int, ym.split("-"))

            if direction == "prev":
                month -= 1
                if month == 0:
                    month = 12
                    year -= 1
            else:
                month += 1
                if month == 13:
                    month = 1
                    year += 1

            cal = InlineCalendar(year=year, month=month)
            await cb.message.edit_reply_markup(reply_markup=cal.markup())
            await cb.answer()

        @r.callback_query(F.data.regexp(r"^cal:\d{4}-\d{2}:noop$"), NewEventFSM.starts_date)
        async def cal_noop(cb: types.CallbackQuery):
            await cb.answer()

        @r.callback_query(F.data.regexp(r"^cal:\d{4}-\d{2}:pick:\d{2}$"), NewEventFSM.starts_date)
        async def cal_pick(cb: types.CallbackQuery, state: FSMContext):
            parts = cb.data.split(":")  # ['cal', 'YYYY-MM', 'pick', 'DD']
            ym = parts[1]
            dd = parts[3]
            year, month = map(int, ym.split("-"))
            day = int(dd)

            await state.update_data(date=f"{year:04d}-{month:02d}-{day:02d}")

            kb = InlineKeyboardBuilder()
            for hhmm in ["18:00", "18:30", "19:00", "19:30", "20:00", "20:30"]:
                kb.button(text=hhmm, callback_data=f"time:{hhmm}")
            kb.button(text="Другое (HH:MM)", callback_data="time:other")
            kb.adjust(3, 3, 1)

            await state.set_state(NewEventFSM.starts_time)
            await cb.message.edit_text(
                f"Дата: <b>{day:02d}.{month:02d}.{year:04d}</b>\nТеперь выбери время:",
                parse_mode="HTML",
                reply_markup=kb.as_markup(),
            )
            await cb.answer()

        @r.callback_query(F.data.regexp(r"^time:\d{2}:\d{2}$"), NewEventFSM.starts_time)
        async def pick_time_quick(cb: types.CallbackQuery, state: FSMContext):
            hhmm = cb.data.split("time:", 1)[1]
            await state.update_data(time=hhmm)
            await proceed_to_notes(cb.message, state)

        @r.callback_query(F.data == "time:other", NewEventFSM.starts_time)
        async def pick_time_other(cb: types.CallbackQuery, state: FSMContext):
            await cb.message.edit_text("Введи время в формате <b>HH:MM</b>", parse_mode="HTML")
            await cb.answer()

        @r.message(NewEventFSM.starts_time)
        async def set_time_manual(m: types.Message, state: FSMContext):
            txt = m.text.strip()
            try:
                t = datetime.strptime(txt, "%H:%M").time()
            except Exception:
                await m.answer("Неверный формат. Пример: <code>19:30</code>", parse_mode="HTML")
                return
            await state.update_data(time=t.strftime("%H:%M"))
            await proceed_to_notes(m, state)

        async def proceed_to_notes(msg: types.Message, state: FSMContext):
            data = await state.get_data()
            if "date" not in data or "time" not in data:
                await msg.answer("Не хватает даты или времени. Начни заново: /new_event")
                return
            y, m, d = map(int, data["date"].split("-"))
            h, mi = map(int, data["time"].split(":"))
            tz = ZoneInfo(settings.TZ)
            dt = datetime(y, m, d, h, mi, tzinfo=tz)
            await state.update_data(starts_at=dt.isoformat())

            await state.set_state(NewEventFSM.notes)
            await msg.answer("Добавь заметку (или отправь «-» чтобы пропустить)")

        @r.message(NewEventFSM.notes)
        async def set_notes_and_publish(m: types.Message, state: FSMContext):
            data = await state.get_data()
            notes = None if m.text.strip() == "-" else m.text.strip()
            tz = ZoneInfo(settings.TZ)
            evt_dt = datetime.fromisoformat(data["starts_at"]).astimezone(tz)

            inp = PublishEventInput(
                chat_id=settings.EVENTS_CHAT_ID,
                organizer_id=m.from_user.id,
                title=data["title"],
                place=data["place"],
                category=data["category"],
                starts_at=evt_dt,
                notes=notes,
            )
            evt = await self.publish_uc.create(inp)
            text = await self.publish_uc.build_text(evt)

            sent = await m.bot.send_message(
                settings.EVENTS_CHAT_ID,
                text,
                reply_markup=event_keyboard(evt.id),
                disable_web_page_preview=True,
            )
            evt.message_id = sent.message_id
            await self.publish_uc.events.update(evt)
            await self.publish_uc.finalize_and_schedule(evt)

            await m.answer("Событие опубликовано в группе ✅")
            await state.clear()

        return r
