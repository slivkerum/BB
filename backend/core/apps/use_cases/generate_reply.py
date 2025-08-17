from dataclasses import dataclass

from backend.core.apps.domain.entities.session import ChatSession, Message
from backend.core.apps.domain.value_objects.ids import ChatId
from backend.core.apps.interfaces.ports.llm_gateway import LLMGateway, LLMMessage, LLMResult
from backend.core.apps.interfaces.ports.session_repo import SessionRepository


@dataclass
class GenerateReplyInput:
    chat_id: int
    user_text: str


@dataclass
class GenerateReplyOutput:
    reply_text: str


@dataclass
class GenerateReply:
    llm: LLMGateway
    sessions: SessionRepository

    async def __call__(self, data: GenerateReplyInput) -> GenerateReplyOutput:
        chat_id = ChatId(data.chat_id)
        session = await self.sessions.load(chat_id) or ChatSession(chat_id=chat_id.value)

        mode_tag = f"[mode={session.mode}] "

        messages: list[LLMMessage] = [
            LLMMessage(role="system", content="You are a helpful assistant.")
        ]
        for m in session.history[-10:]:
            messages.append(LLMMessage("user" if m.role == "user" else "assistant", m.text))
        messages.append(LLMMessage("user", mode_tag + data.user_text))

        result: LLMResult = await self.llm.generate(messages)

        session.history.append(Message(role="user", text=data.user_text))
        session.history.append(Message(role="assistant", text=result.text))
        await self.sessions.save(session)

        return GenerateReplyOutput(reply_text=result.text)
