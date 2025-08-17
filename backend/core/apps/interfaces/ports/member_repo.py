from abc import ABC, abstractmethod
from backend.core.apps.domain.entities.event import Member


class MemberRepository(ABC):
    @abstractmethod
    async def upsert(self, member: Member) -> None: ...

    @abstractmethod
    async def set_can_dm(self, user_id: int, can_dm: bool) -> None: ...

    @abstractmethod
    async def get(self, user_id: int) -> Member | None: ...

    @abstractmethod
    async def touch_activity(self, user_id: int) -> None: ...
