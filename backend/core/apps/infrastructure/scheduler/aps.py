from dataclasses import dataclass, field
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from pytz import timezone


@dataclass
class APSSchedulerAdapter:
    on_event_reminder: callable
    on_daily_post: callable
    on_event_expire: callable
    tz_name: str = "Asia/Qostanay"
    _scheduler: AsyncIOScheduler = field(init=False)

    def __post_init__(self):
        self._scheduler = AsyncIOScheduler(timezone=timezone(self.tz_name))

    async def start(self):
        if not self._scheduler.running:
            self._scheduler.start()

    async def shutdown(self):
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)

    async def _event_reminder_job(self, event_id: int):
        await self.on_event_reminder(event_id)

    async def _daily_post_job(self, chat_id: int):
        await self.on_daily_post(chat_id)

    async def _event_expiry_job(self, event_id: int):
        await self.on_event_expire(event_id)

    async def schedule_event_reminders(self, event_id: int, when_list: list[datetime]) -> list[str]:
        ids: list[str] = []
        for when in when_list:
            job_id = f"evt:{event_id}:{int(when.timestamp())}"
            self._scheduler.add_job(
                self._event_reminder_job,
                DateTrigger(run_date=when),
                args=[event_id],
                id=job_id,
                replace_existing=True,
            )
            ids.append(job_id)
        return ids

    async def cancel_for_event(self, event_id: int) -> None:
        for job in list(self._scheduler.get_jobs()):
            if job.id.startswith(f"evt:{event_id}:"):
                self._scheduler.remove_job(job.id)

    async def schedule_daily(self, chat_id: int, cron: str, job_id: str) -> None:
        m, h, dom, mon, dow = cron.split()
        trig = CronTrigger(
            minute=m, hour=h, day=dom, month=mon, day_of_week=dow, timezone=timezone(self.tz_name)
        )
        self._scheduler.add_job(
            self._daily_post_job,
            trig,
            args=[chat_id],
            id=job_id,
            replace_existing=True,
        )

    async def schedule_event_expiry(self, event_id: int, when: datetime) -> str:
        job_id = f"exp:{event_id}:{int(when.timestamp())}"
        self._scheduler.add_job(
            self._event_expiry_job,
            DateTrigger(run_date=when),
            args=[event_id],
            id=job_id,
            replace_existing=True,
        )
        return job_id
