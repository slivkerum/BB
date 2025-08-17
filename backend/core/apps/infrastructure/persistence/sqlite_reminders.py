from dataclasses import dataclass
from typing import Sequence

import aiosqlite


@dataclass
class SQLiteReminderMsgRepo:
    dsn: str
    _initialized: bool = False

    async def _init(self):
        if self._initialized:
            return
        async with aiosqlite.connect(self.dsn) as db:
            await db.execute("""
              CREATE TABLE IF NOT EXISTS reminder_messages (
                event_id   INTEGER NOT NULL,
                chat_id    INTEGER NOT NULL,
                message_id INTEGER NOT NULL
              );
            """)
            await db.commit()
        self._initialized = True

    async def add(self, event_id: int, chat_id: int, message_id: int) -> None:
        await self._init()
        async with aiosqlite.connect(self.dsn) as db:
            await db.execute(
                "INSERT INTO reminder_messages(event_id, chat_id, message_id) VALUES(?,?,?)",
                (event_id, chat_id, message_id),
            )
            await db.commit()

    async def list_by_event(self, event_id: int) -> Sequence[tuple[int, int]]:
        await self._init()
        async with aiosqlite.connect(self.dsn) as db:
            cur = await db.execute(
                "SELECT chat_id, message_id FROM reminder_messages WHERE event_id=?",
                (event_id,),
            )
            rows = await cur.fetchall()
            await cur.close()
            return [(r[0], r[1]) for r in rows]

    async def delete_for_event(self, event_id: int) -> None:
        await self._init()
        async with aiosqlite.connect(self.dsn) as db:
            await db.execute("DELETE FROM reminder_messages WHERE event_id=?", (event_id,))
            await db.commit()
