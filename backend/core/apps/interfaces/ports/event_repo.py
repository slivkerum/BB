from abc import ABC, abstractmethod

from backend.core.apps.domain.entities.event import Event


class EventRepository(ABC):
    @abstractmethod
    async def create(self, evt: Event) -> Event: ...

    @abstractmethod
    async def update(self, evt: Event) -> None: ...

    @abstractmethod
    async def close(self, event_id: int) -> None: ...

    @abstractmethod
    async def get(self, event_id: int) -> Event | None: ...

    @abstractmethod
    async def get_by_message(self, chat_id: int, message_id: int) -> Event | None: ...
