from dataclasses import dataclass
from datetime import datetime

import aiosqlite

from backend.core.apps.domain.entities.event import Event
from backend.core.apps.interfaces.ports.event_repo import EventRepository


@dataclass
class SQLiteEventRepo(EventRepository):
    dsn: str
    _initialized: bool = False

    async def _init(self):
        if self._initialized:
            return
        async with aiosqlite.connect(self.dsn) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS events (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  chat_id INTEGER NOT NULL,
                  message_id INTEGER,
                  title TEXT NOT NULL,
                  place TEXT NOT NULL,
                  category TEXT NOT NULL,
                  starts_at TEXT NOT NULL,
                  organizer_id INTEGER NOT NULL,
                  capacity INTEGER,
                  cost_policy TEXT,
                  notes TEXT,
                  status TEXT NOT NULL,
                  created_at TEXT NOT NULL
                );
            """)
            await db.commit()
        self._initialized = True

    async def create(self, evt: Event) -> Event:
        await self._init()
        async with aiosqlite.connect(self.dsn) as db:
            cur = await db.execute(
                """
              INSERT INTO events (chat_id,message_id,title,place,category,starts_at,organizer_id,
                                  capacity,cost_policy,notes,status,created_at)
              VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """,
                (
                    evt.chat_id,
                    evt.message_id,
                    evt.title,
                    evt.place,
                    evt.category,
                    evt.starts_at.isoformat(),
                    evt.organizer_id,
                    evt.capacity,
                    evt.cost_policy,
                    evt.notes,
                    evt.status,
                    evt.created_at.isoformat(),
                ),
            )
            await db.commit()
            evt.id = cur.lastrowid
            return evt

    async def update(self, evt: Event) -> None:
        await self._init()
        async with aiosqlite.connect(self.dsn) as db:
            await db.execute(
                """
              UPDATE events SET chat_id=?, message_id=?, title=?, place=?, category=?, starts_at=?,
                                organizer_id=?, capacity=?, cost_policy=?, notes=?, status=?
              WHERE id=?
            """,
                (
                    evt.chat_id,
                    evt.message_id,
                    evt.title,
                    evt.place,
                    evt.category,
                    evt.starts_at.isoformat(),
                    evt.organizer_id,
                    evt.capacity,
                    evt.cost_policy,
                    evt.notes,
                    evt.status,
                    evt.id,
                ),
            )
            await db.commit()

    async def close(self, event_id: int) -> None:
        await self._init()
        async with aiosqlite.connect(self.dsn) as db:
            await db.execute("UPDATE events SET status='closed' WHERE id=?", (event_id,))
            await db.commit()

    async def get(self, event_id: int) -> Event | None:
        await self._init()
        async with aiosqlite.connect(self.dsn) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT * FROM events WHERE id=?", (event_id,))
            row = await cur.fetchone()
            await cur.close()
            return self._row_to_event(row) if row else None

    async def get_by_message(self, chat_id: int, message_id: int) -> Event | None:
        await self._init()
        async with aiosqlite.connect(self.dsn) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT * FROM events WHERE chat_id=? AND message_id=?",
                (chat_id, message_id),
            )
            row = await cur.fetchone()
            await cur.close()
            return self._row_to_event(row) if row else None

    def _row_to_event(self, row) -> Event:
        return Event(
            id=row["id"],
            chat_id=row["chat_id"],
            message_id=row["message_id"],
            title=row["title"],
            place=row["place"],
            category=row["category"],
            starts_at=datetime.fromisoformat(row["starts_at"]),
            organizer_id=row["organizer_id"],
            capacity=row["capacity"],
            cost_policy=row["cost_policy"],
            notes=row["notes"],
            status=row["status"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )
