from abc import ABC, abstractmethod
from datetime import datetime


class Scheduler(ABC):
    @abstractmethod
    async def schedule_event_reminders(
        self, event_id: int, when_list: list[datetime]
    ) -> list[str]: ...

    @abstractmethod
    async def cancel_for_event(self, event_id: int) -> None: ...

    @abstractmethod
    async def schedule_daily(self, chat_id: int, cron: str, job_id: str) -> None: ...
