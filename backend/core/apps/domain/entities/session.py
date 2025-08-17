from dataclasses import dataclass, field
from typing import Literal

Mode = Literal["general", "code", "admin"]


@dataclass
class Message:
    role: Literal["user", "assistant"]
    text: str


@dataclass
class ChatSession:
    chat_id: int
    mode: Mode = "general"
    history: list[Message] = field(default_factory=list)
