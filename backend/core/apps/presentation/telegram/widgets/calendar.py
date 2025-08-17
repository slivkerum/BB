from dataclasses import dataclass
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import date
import calendar as pycal


WEEKDAYS_RU = ["Пн","Вт","Ср","Чт","Пт","Сб","Вс"]


@dataclass
class InlineCalendar:
    year: int
    month: int

    def markup(self) -> InlineKeyboardMarkup:
        kb: list[list[InlineKeyboardButton]] = []

        # Шапка: «‹ Месяц YYYY ›»
        title = f"{self._month_name(self.month)} {self.year}"
        kb.append([
            InlineKeyboardButton(text="‹", callback_data=f"cal:{self.year:04d}-{self.month:02d}:nav:prev"),
            InlineKeyboardButton(text=title, callback_data=f"cal:{self.year:04d}-{self.month:02d}:noop"),
            InlineKeyboardButton(text="›", callback_data=f"cal:{self.year:04d}-{self.month:02d}:nav:next"),
        ])

        # Дни недели
        kb.append([InlineKeyboardButton(text=w, callback_data=f"cal:{self.year:04d}-{self.month:02d}:noop") for w in WEEKDAYS_RU])

        # Сетка дней
        monthcal = pycal.Calendar(firstweekday=0).monthdayscalendar(self.year, self.month)  # 0=Пн в Python? (на самом деле 0=Пн у calendar.setfirstweekday(0))
        # В aiogram неделя обычно Пн..Вс, выше как раз так и сделали.
        for week in monthcal:
            row: list[InlineKeyboardButton] = []
            for d in week:
                if d == 0:
                    row.append(InlineKeyboardButton(text=" ", callback_data=f"cal:{self.year:04d}-{self.month:02d}:noop"))
                else:
                    row.append(
                        InlineKeyboardButton(
                            text=str(d),
                            callback_data=f"cal:{self.year:04d}-{self.month:02d}:pick:{d:02d}"
                        )
                    )
            kb.append(row)

        return InlineKeyboardMarkup(inline_keyboard=kb)

    def _month_name(self, m: int) -> str:
        names = ["Янв","Фев","Мар","Апр","Май","Июн","Июл","Авг","Сен","Окт","Ноя","Дек"]
        return names[m-1]