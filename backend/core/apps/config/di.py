from dataclasses import dataclass
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from backend.core.apps.config.settings import settings
from backend.core.apps.infrastructure.persistence.memory_session import InMemorySessionRepo
from backend.core.apps.infrastructure.persistence.sqlite_session import SQLiteSessionRepo
from backend.core.apps.infrastructure.persistence.sqlite_events import SQLiteEventRepo
from backend.core.apps.infrastructure.persistence.sqlite_regs import SQLiteRegistrationRepo
from backend.core.apps.infrastructure.persistence.sqlite_reminders import SQLiteReminderMsgRepo
from backend.core.apps.infrastructure.persistence.sqlite_members import SQLiteMemberRepo
from backend.core.apps.infrastructure.llm.gemini_client import FakeGemini, GeminiGateway
from backend.core.apps.infrastructure.scheduler.aps import APSSchedulerAdapter

from backend.core.apps.presentation.telegram.presenters.event_card import EventCardPresenter
from backend.core.apps.presentation.telegram.routers.chat import ChatRouterFactory
from backend.core.apps.presentation.telegram.routers.reset import ResetRouterFactory
from backend.core.apps.presentation.telegram.routers.events import EventsRouterFactory
from backend.core.apps.presentation.telegram.routers.events_wizard import EventsWizardRouterFactory
from backend.core.apps.presentation.telegram.routers.help import HelpRouterFactory
from backend.core.apps.presentation.telegram.routers.dm_start import DMStartRouterFactory

from backend.core.apps.use_cases.generate_reply import GenerateReply
from backend.core.apps.use_cases.reset_session import ResetSession
from backend.core.apps.use_cases.publish_event import PublishEvent
from backend.core.apps.use_cases.register_for_event import RegisterForEvent
from backend.core.apps.use_cases.close_event import CloseEvent
from backend.core.apps.use_cases.expire_event import ExpireEvent
from backend.core.apps.use_cases.send_event_reminder import SendEventReminder
from backend.core.apps.use_cases.post_daily_digest import PostDailyDigest



@dataclass
class Container:
    bot: Bot
    dp: Dispatcher
    scheduler: APSSchedulerAdapter


def build_container() -> Container:
    # -------------------
    # Infrastructure
    # -------------------
    sessions = (
        SQLiteSessionRepo(settings.SQLITE_DSN)
        if settings.SESSIONS_BACKEND == "sqlite"
        else InMemorySessionRepo()
    )

    llm = (
        GeminiGateway(
            api_key=settings.GEMINI_API_KEY or "",
            model_name=settings.GEMINI_MODEL,
            system_instruction=settings.SYSTEM_PROMPT,
        )
        if settings.LLM_PROVIDER == "gemini"
        else FakeGemini()
    )

    bot = Bot(
        settings.TELEGRAM_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    dp = Dispatcher()

    events_repo = SQLiteEventRepo(settings.SQLITE_DSN)
    regs_repo = SQLiteRegistrationRepo(settings.SQLITE_DSN)
    reminders_repo = SQLiteReminderMsgRepo(settings.SQLITE_DSN)
    members_repo = SQLiteMemberRepo(settings.SQLITE_DSN)

    presenter = EventCardPresenter()

    # -------------------
    # Use Cases
    # -------------------
    generate_reply = GenerateReply(llm=llm, sessions=sessions)
    reset_session = ResetSession(sessions=sessions)

    register_event = RegisterForEvent(
        events=events_repo,
        regs=regs_repo,
        presenter=presenter,
        members=members_repo,
    )

    post_daily = PostDailyDigest(
        bot=bot,
        llm=llm,
        system_prompt=settings.SYSTEM_PROMPT,
    )

    send_event_reminder = SendEventReminder(
        bot=bot,
        events=events_repo,
        regs=regs_repo,
        presenter=presenter,
        reminders_repo=reminders_repo,
    )

    # Создаём scheduler без expire_event
    scheduler = APSSchedulerAdapter(
        on_event_reminder=send_event_reminder,
        on_daily_post=post_daily,
        on_event_expire=None,
        tz_name=settings.TZ,
    )

    expire_event = ExpireEvent(
        events=events_repo,
        scheduler=scheduler,
        bot=bot,
        reminders=reminders_repo,
    )
    scheduler.on_event_expire = expire_event

    close_event = CloseEvent(
        events=events_repo,
        scheduler=scheduler,
        bot=bot,
        reminders=reminders_repo,
    )

    publish_event = PublishEvent(
        events=events_repo,
        regs=regs_repo,
        presenter=presenter,
        scheduler=scheduler,
    )

    # -------------------
    # Routers
    # -------------------
    dp.include_router(DMStartRouterFactory(members=members_repo).build())
    dp.include_router(HelpRouterFactory().build())
    dp.include_router(EventsWizardRouterFactory(publish_uc=publish_event).build())
    dp.include_router(ResetRouterFactory(use_case=reset_session).build())
    dp.include_router(
        EventsRouterFactory(
            publish_uc=publish_event,
            register_uc=register_event,
            events_repo=events_repo,
            close_uc=close_event,
        ).build()
    )
    dp.include_router(ChatRouterFactory(use_case=generate_reply).build())

    return Container(bot=bot, dp=dp, scheduler=scheduler)
