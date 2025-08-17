from dataclasses import dataclass, field

from backend.core.apps.domain.entities.session import ChatSession
from backend.core.apps.domain.value_objects.ids import ChatId
from backend.core.apps.interfaces.ports.session_repo import SessionRepository


@dataclass
class InMemorySessionRepo(SessionRepository):
    _store: dict[int, ChatSession] = field(default_factory=dict)

    async def load(self, chat_id: ChatId) -> ChatSession | None:
        return self._store.get(chat_id.value)

    async def save(self, session: ChatSession) -> None:
        self._store[session.chat_id] = session

    async def reset(self, chat_id: ChatId) -> None:
        self._store.pop(chat_id.value, None)
