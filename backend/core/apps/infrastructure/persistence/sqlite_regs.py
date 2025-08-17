from dataclasses import dataclass

import aiosqlite

from backend.core.apps.domain.entities.event import Registration
from backend.core.apps.interfaces.ports.registration_repo import RegistrationRepository


@dataclass
class SQLiteRegistrationRepo(RegistrationRepository):
    dsn: str
    _initialized: bool = False

    async def _init(self):
        if self._initialized:
            return
        async with aiosqlite.connect(self.dsn) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS registrations (
                  event_id INTEGER NOT NULL,
                  user_id INTEGER NOT NULL,
                  status TEXT NOT NULL,
                  updated_at TEXT NOT NULL,
                  PRIMARY KEY (event_id, user_id)
                );
            """)
            await db.commit()
        self._initialized = True

    async def set_status(self, reg: Registration) -> bool:
        await self._init()
        async with aiosqlite.connect(self.dsn) as db:
            # узнаём старое значение
            cur = await db.execute(
                "SELECT status FROM registrations WHERE event_id=? AND user_id=?",
                (reg.event_id, reg.user_id),
            )
            row = await cur.fetchone()
            await cur.close()
            old = row[0] if row else None
            changed = old != reg.status

            # апсертим только если изменилось (но можно и всегда — не принципиально)
            await db.execute(
                """
                             INSERT INTO registrations (event_id, user_id, status, updated_at)
                             VALUES (?, ?, ?, ?) ON CONFLICT(event_id, user_id) DO
                             UPDATE SET
                                 status=excluded.status, updated_at=excluded.updated_at
                             """,
                (reg.event_id, reg.user_id, reg.status, reg.updated_at.isoformat()),
            )
            await db.commit()

            return changed

    async def get_all(self, event_id: int) -> dict[int, str]:
        await self._init()
        async with aiosqlite.connect(self.dsn) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT user_id, status FROM registrations WHERE event_id=?", (event_id,)
            )
            rows = await cur.fetchall()
            await cur.close()
            return {r["user_id"]: r["status"] for r in rows}

    async def get_attendees(self, event_id: int) -> list[int]:
        await self._init()
        async with aiosqlite.connect(self.dsn) as db:
            cur = await db.execute(
                "SELECT user_id FROM registrations WHERE event_id=? AND status='going'", (event_id,)
            )
            rows = await cur.fetchall()
            await cur.close()
            return [r[0] for r in rows]

    async def get_declined(self, event_id: int) -> list[int]:
        await self._init()
        async with aiosqlite.connect(self.dsn) as db:
            cur = await db.execute(
                "SELECT user_id FROM registrations WHERE event_id=? AND status='declined'",
                (event_id,),
            )
            rows = await cur.fetchall()
            await cur.close()
            return [r[0] for r in rows]
