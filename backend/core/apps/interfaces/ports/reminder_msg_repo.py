from abc import ABC, abstractmethod
from typing import Sequence


class ReminderMessageRepository(ABC):
    @abstractmethod
    async def add(self, event_id: int, chat_id: int, message_id: int) -> None: ...

    @abstractmethod
    async def list_by_event(self, event_id: int) -> Sequence[tuple[int, int]]: ...
    
    @abstractmethod
    async def delete_for_event(self, event_id: int) -> None: ...
