# backend/core/apps/entrypoints/polling.py
import asyncio
from aiogram.types import BotCommand
from backend.core.apps.config.di import build_container
from backend.core.apps.config.settings import settings

async def _run():
    c = build_container()
    print("Polling started (local).")

    await c.bot.set_my_commands([
        BotCommand(command="new_event", description="Создать мероприятие"),
        BotCommand(command="reset", description="Сбросить ИИ-сессию"),
        BotCommand(command="help", description="Помощь"),
    ])

    await c.scheduler.start()
    if settings.DAILY_CHAT_ID:
        await c.scheduler.schedule_daily(settings.DAILY_CHAT_ID, settings.DAILY_CRON, job_id="daily:post")

    await c.dp.start_polling(c.bot)

def main():
    asyncio.run(_run())
