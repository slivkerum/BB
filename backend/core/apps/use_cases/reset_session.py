from dataclasses import dataclass
from backend.core.apps.interfaces.ports.session_repo import SessionRepository
from backend.core.apps.domain.value_objects.ids import ChatId


@dataclass
class ResetSessionInput:
    chat_id: int


@dataclass
class ResetSessionOutput:
    ok: bool


@dataclass
class ResetSession:
    sessions: SessionRepository

    async def __call__(self, data: ResetSessionInput) -> ResetSessionOutput:
        await self.sessions.reset(ChatId(data.chat_id))
        return ResetSessionOutput(ok=True)
