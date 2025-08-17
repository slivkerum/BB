import json
import aiosqlite
from dataclasses import dataclass
from backend.core.apps.interfaces.ports.session_repo import SessionRepository
from backend.core.apps.domain.entities.session import ChatSession, Message
from backend.core.apps.domain.value_objects.ids import ChatId


@dataclass
class SQLiteSessionRepo(SessionRepository):
    dsn: str
    _initialized: bool = False

    async def _init(self) -> None:
        if self._initialized:
            return
        async with aiosqlite.connect(self.dsn) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    chat_id INTEGER PRIMARY KEY,
                    mode TEXT NOT NULL,
                    history TEXT NOT NULL
                );
                """
            )
            await db.commit()
        self._initialized = True

    async def load(self, chat_id: ChatId) -> ChatSession | None:
        await self._init()
        async with aiosqlite.connect(self.dsn) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT chat_id, mode, history FROM sessions WHERE chat_id = ?",
                (chat_id.value,),
            )
            row = await cur.fetchone()
            await cur.close()
            if not row:
                return None
            history = [Message(**m) for m in json.loads(row["history"])]
            return ChatSession(chat_id=row["chat_id"], mode=row["mode"], history=history)

    async def save(self, session: ChatSession) -> None:
        await self._init()
        history_raw = json.dumps([m.__dict__ for m in session.history], ensure_ascii=False)
        async with aiosqlite.connect(self.dsn) as db:
            await db.execute(
                """
                INSERT INTO sessions(chat_id, mode, history)
                VALUES (?, ?, ?)
                ON CONFLICT(chat_id) DO UPDATE SET mode = excluded.mode, history = excluded.history
                """,
                (session.chat_id, session.mode, history_raw),
            )
            await db.commit()

    async def reset(self, chat_id: ChatId) -> None:
        await self._init()
        async with aiosqlite.connect(self.dsn) as db:
            await db.execute("DELETE FROM sessions WHERE chat_id = ?", (chat_id.value,))
            await db.commit()
