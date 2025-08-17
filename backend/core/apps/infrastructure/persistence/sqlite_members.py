from dataclasses import dataclass
from datetime import datetime

import aiosqlite

from backend.core.apps.domain.entities.event import Member
from backend.core.apps.interfaces.ports.member_repo import MemberRepository


@dataclass
class SQLiteMemberRepo(MemberRepository):
    dsn: str
    _initialized: bool = False

    async def _init(self):
        if self._initialized:
            return
        async with aiosqlite.connect(self.dsn) as db:
            await db.execute("""
              CREATE TABLE IF NOT EXISTS members (
                user_id       INTEGER PRIMARY KEY,
                display_name  TEXT NOT NULL,
                username      TEXT,
                can_dm        INTEGER NOT NULL DEFAULT 0,
                last_activity TEXT
              );
            """)
            await db.commit()
        self._initialized = True

    async def upsert(self, member: Member) -> None:
        await self._init()
        async with aiosqlite.connect(self.dsn) as db:
            await db.execute(
                """
              INSERT INTO members(user_id, display_name, username, can_dm, last_activity)
              VALUES(?,?,?,?,?)
              ON CONFLICT(user_id) DO UPDATE SET
                display_name=excluded.display_name,
                username=excluded.username,
                can_dm=COALESCE(excluded.can_dm, can_dm),
                last_activity=COALESCE(excluded.last_activity, last_activity)
            """,
                (
                    member.user_id,
                    member.display_name,
                    member.username,
                    1 if getattr(member, "can_dm", False) else 0,
                    getattr(member, "last_activity", None).isoformat()
                    if getattr(member, "last_activity", None)
                    else None,
                ),
            )
            await db.commit()

    async def set_can_dm(self, user_id: int, can_dm: bool) -> None:
        await self._init()
        async with aiosqlite.connect(self.dsn) as db:
            await db.execute(
                "UPDATE members SET can_dm=? WHERE user_id=?", (1 if can_dm else 0, user_id)
            )
            await db.commit()

    async def get(self, user_id: int) -> Member | None:
        await self._init()
        async with aiosqlite.connect(self.dsn) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT * FROM members WHERE user_id=?", (user_id,))
            row = await cur.fetchone()
            await cur.close()
            if not row:
                return None
            return Member(
                user_id=row["user_id"],
                display_name=row["display_name"],
                username=row["username"],
                can_dm=bool(row["can_dm"]),
                last_activity=datetime.fromisoformat(row["last_activity"])
                if row["last_activity"]
                else None,
            )

    async def touch_activity(self, user_id: int) -> None:
        await self._init()
        now = datetime.utcnow().isoformat()
        async with aiosqlite.connect(self.dsn) as db:
            await db.execute(
                """
              INSERT INTO members(user_id, display_name, username, can_dm, last_activity)
              VALUES(?, COALESCE((SELECT display_name FROM members WHERE user_id=?), 'User'), 
                         COALESCE((SELECT username FROM members WHERE user_id=?), NULL),
                         COALESCE((SELECT can_dm FROM members WHERE user_id=?), 0),
                         ?)
              ON CONFLICT(user_id) DO UPDATE SET last_activity=excluded.last_activity
            """,
                (user_id, user_id, user_id, user_id, now),
            )
            await db.commit()
