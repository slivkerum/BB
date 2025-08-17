from abc import ABC, abstractmethod

from backend.core.apps.domain.entities.event import Registration


class RegistrationRepository(ABC):
    @abstractmethod
    async def set_status(self, reg: Registration) -> bool: ...

    @abstractmethod
    async def get_all(self, event_id: int) -> dict[int, str]: ...

    @abstractmethod
    async def get_attendees(self, event_id: int) -> list[int]: ...

    @abstractmethod
    async def get_declined(self, event_id: int) -> list[int]: ...
