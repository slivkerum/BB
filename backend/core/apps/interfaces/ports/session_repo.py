from abc import ABC, abstractmethod

from backend.core.apps.domain.entities.session import ChatSession
from backend.core.apps.domain.value_objects.ids import ChatId


class SessionRepository(ABC):
    @abstractmethod
    async def load(self, chat_id: ChatId) -> ChatSession | None: ...

    @abstractmethod
    async def save(self, session: ChatSession) -> None: ...

    @abstractmethod
    async def reset(self, chat_id: ChatId) -> None: ...
