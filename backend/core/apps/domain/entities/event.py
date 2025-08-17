from dataclasses import dataclass, field
from typing import Literal
from datetime import datetime


EventStatus = Literal["published", "closed"]
Category = Literal["walk", "cinema", "cafe", "sport", "meetup", "other"]
CostPolicy = Literal["split", "each", "free", "org"]


@dataclass
class Event:
    id: int | None
    chat_id: int
    message_id: int | None
    title: str
    place: str
    category: Category
    starts_at: datetime
    organizer_id: int
    capacity: int | None = None
    cost_policy: CostPolicy | None = None
    notes: str | None = None
    status: EventStatus = "published"
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class Registration:
    event_id: int
    user_id: int
    status: Literal["going", "declined"]
    updated_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class Member:
    user_id: int
    display_name: str
    username: str | None = None
    can_dm: bool = False
    last_activity: datetime | None = None
