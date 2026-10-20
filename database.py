
import time
import aiosqlite


class Database:
    def __init__(self, path: str):
        self.path = path

    async def connect(self):
        db = await aiosqlite.connect(self.path)
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys=ON")
        return db

    async def initialize(self):
        db = await self.connect()
        try:
            await db.execute("PRAGMA journal_mode=WAL")

            await db.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    first_seen INTEGER NOT NULL,
                    last_seen INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    platform TEXT NOT NULL,
                    clicked_at INTEGER NOT NULL,
                    FOREIGN KEY(user_id)
                        REFERENCES users(user_id)
                );

                CREATE INDEX IF NOT EXISTS idx_interactions_user_time
                ON interactions(user_id, clicked_at);

                CREATE TABLE IF NOT EXISTS alerts (
                    user_id INTEGER PRIMARY KEY,
                    alerted_at INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS soundtrack (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    kind TEXT NOT NULL,
                    file_id TEXT,
                    title TEXT,
                    url TEXT,
                    updated_at INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS soundtrack_deliveries (
                    user_id INTEGER PRIMARY KEY,
                    sent_at INTEGER NOT NULL,
                    FOREIGN KEY(user_id)
                        REFERENCES users(user_id)
                );
            """)

            await db.commit()
        finally:
            await db.close()

    async def register_user(self, user):
        now = int(time.time())
        db = await self.connect()
        try:
            cursor = await db.execute(
                "SELECT user_id FROM users WHERE user_id = ?",
                (user.id,),
            )
            existing = await cursor.fetchone()

            await db.execute("""
                INSERT INTO users (
                    user_id, username, first_name, last_name,
                    first_seen, last_seen
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    username = excluded.username,
                    first_name = excluded.first_name,
                    last_name = excluded.last_name,
                    last_seen = excluded.last_seen
            """, (
                user.id,
                user.username,
                user.first_name,
                user.last_name,
                now,
                now,
            ))

            await db.commit()
            return existing is None
        finally:
            await db.close()

    async def record_interaction(
        self,
        user_id: int,
        platform: str,
        window_seconds: int = 300,
    ):
        now = int(time.time())
        db = await self.connect()
        try:
            await db.execute("""
                INSERT INTO interactions (
                    user_id, platform, clicked_at
                )
                VALUES (?, ?, ?)
            """, (user_id, platform, now))

            await db.commit()

            cursor = await db.execute("""
                SELECT
                    COUNT(*) AS click_count,
                    COUNT(DISTINCT platform) AS platform_count
                FROM interactions
                WHERE user_id = ?
                  AND clicked_at >= ?
            """, (user_id, now - window_seconds))

            row = await cursor.fetchone()
            return row["click_count"], row["platform_count"]
        finally:
            await db.close()

    async def has_alerted(self, user_id: int) -> bool:
        db = await self.connect()
        try:
            cursor = await db.execute(
                "SELECT 1 FROM alerts WHERE user_id = ?",
                (user_id,),
            )
            return await cursor.fetchone() is not None
        finally:
            await db.close()

    async def mark_alerted(self, user_id: int):
        db = await self.connect()
        try:
            await db.execute("""
                INSERT OR IGNORE INTO alerts (user_id, alerted_at)
                VALUES (?, ?)
            """, (user_id, int(time.time())))
            await db.commit()
        finally:
            await db.close()

    async def has_received_soundtrack(self, user_id: int) -> bool:
        db = await self.connect()
        try:
            cursor = await db.execute(
                "SELECT 1 FROM soundtrack_deliveries WHERE user_id = ?",
                (user_id,),
            )
            return await cursor.fetchone() is not None
        finally:
            await db.close()

    async def mark_soundtrack_sent(self, user_id: int):
        db = await self.connect()
        try:
            await db.execute("""
                INSERT OR IGNORE INTO soundtrack_deliveries (
                    user_id, sent_at
                )
                VALUES (?, ?)
            """, (user_id, int(time.time())))
            await db.commit()
        finally:
            await db.close()

    async def get_users(self):
        db = await self.connect()
        try:
            cursor = await db.execute("""
                SELECT
                    user_id, username, first_name, last_name,
                    first_seen, last_seen
                FROM users
                ORDER BY first_seen DESC
            """)
            return await cursor.fetchall()
        finally:
            await db.close()

    async def get_stats(self):
        db = await self.connect()
        try:
            cursor = await db.execute("""
                SELECT
                    (SELECT COUNT(*) FROM users) AS users,
                    (SELECT COUNT(*) FROM interactions) AS interactions,
                    (SELECT COUNT(*) FROM alerts) AS alerts
            """)
            return await cursor.fetchone()
        finally:
            await db.close()

    async def save_soundtrack(
        self,
        kind: str,
        file_id: str | None = None,
        title: str = "",
        url: str | None = None,
    ):
        db = await self.connect()
        try:
            await db.execute("""
                INSERT INTO soundtrack (
                    id, kind, file_id, title, url, updated_at
                )
                VALUES (1, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    kind = excluded.kind,
                    file_id = excluded.file_id,
                    title = excluded.title,
                    url = excluded.url,
                    updated_at = excluded.updated_at
            """, (
                kind,
                file_id,
                title,
                url,
                int(time.time()),
            ))
            await db.commit()
        finally:
            await db.close()

    async def get_soundtrack(self):
        db = await self.connect()
        try:
            cursor = await db.execute(
                "SELECT * FROM soundtrack WHERE id = 1"
            )
            return await cursor.fetchone()
        finally:
            await db.close()
