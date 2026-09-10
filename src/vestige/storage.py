"""SQLite storage: business connections, user preferences and message snapshots.

Telegram never tells a bot *what* was deleted — the ``deleted_business_messages``
update carries nothing but chat and message ids. The only way to show the owner
the vanished text or media is to keep our own snapshot of every message that
passed through the connection, which is what this module is for.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import aiosqlite

SCHEMA = """
CREATE TABLE IF NOT EXISTS connections (
    connection_id   TEXT PRIMARY KEY,
    owner_id        INTEGER NOT NULL,
    owner_chat_id   INTEGER NOT NULL,
    is_enabled      INTEGER NOT NULL DEFAULT 1,
    can_read        INTEGER NOT NULL DEFAULT 0,
    can_delete_sent INTEGER NOT NULL DEFAULT 0,
    updated_at      INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_connections_owner ON connections(owner_id);

CREATE TABLE IF NOT EXISTS prefs (
    owner_id        INTEGER PRIMARY KEY,
    notify_deleted  INTEGER NOT NULL DEFAULT 1,
    notify_edited   INTEGER NOT NULL DEFAULT 1,
    capture_once    INTEGER NOT NULL DEFAULT 1,
    include_own     INTEGER NOT NULL DEFAULT 0,
    capture_any_media INTEGER NOT NULL DEFAULT 0,
    language        TEXT NOT NULL DEFAULT 'ru'
);

CREATE TABLE IF NOT EXISTS snapshots (
    connection_id   TEXT NOT NULL,
    chat_id         INTEGER NOT NULL,
    message_id      INTEGER NOT NULL,
    owner_id        INTEGER NOT NULL,
    sender_id       INTEGER,
    sender_name     TEXT,
    is_outgoing     INTEGER NOT NULL DEFAULT 0,
    sent_at         INTEGER NOT NULL,
    saved_at        INTEGER NOT NULL,
    text            TEXT,
    entities        TEXT,
    media_type      TEXT,
    file_id         TEXT,
    file_unique_id  TEXT,
    file_path       TEXT,
    extra           TEXT,
    PRIMARY KEY (connection_id, chat_id, message_id)
);

CREATE INDEX IF NOT EXISTS idx_snapshots_saved_at ON snapshots(saved_at);
"""

PREF_KEYS = (
    "notify_deleted",
    "notify_edited",
    "capture_once",
    "include_own",
    "capture_any_media",
)


@dataclass(slots=True)
class Connection:
    connection_id: str
    owner_id: int
    owner_chat_id: int
    is_enabled: bool = True
    can_read: bool = False
    can_delete_sent: bool = False


@dataclass(slots=True)
class Prefs:
    owner_id: int
    notify_deleted: bool = True
    notify_edited: bool = True
    capture_once: bool = True
    include_own: bool = False
    capture_any_media: bool = False
    language: str = "ru"


@dataclass(slots=True)
class Snapshot:
    connection_id: str
    chat_id: int
    message_id: int
    owner_id: int
    sent_at: int
    sender_id: int | None = None
    sender_name: str | None = None
    is_outgoing: bool = False
    text: str | None = None
    entities: list[dict[str, Any]] = field(default_factory=list)
    media_type: str | None = None
    file_id: str | None = None
    file_unique_id: str | None = None
    file_path: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)
    saved_at: int = 0

    @property
    def has_content(self) -> bool:
        return bool(self.text or self.file_id or self.file_path)


class Storage:
    """Thin async wrapper over a single SQLite connection."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._db: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self._db = await aiosqlite.connect(self._path)
        self._db.row_factory = aiosqlite.Row
        await self._db.execute("PRAGMA journal_mode=WAL")
        await self._db.execute("PRAGMA foreign_keys=ON")
        await self._db.executescript(SCHEMA)
        await self._db.commit()

    async def close(self) -> None:
        if self._db is not None:
            await self._db.close()
            self._db = None

    @property
    def db(self) -> aiosqlite.Connection:
        if self._db is None:
            raise RuntimeError("Storage.connect() must be awaited before use")
        return self._db

    # ------------------------------------------------------------------ connections

    async def save_connection(self, conn: Connection) -> None:
        await self.db.execute(
            """
            INSERT INTO connections
                (connection_id, owner_id, owner_chat_id, is_enabled,
                 can_read, can_delete_sent, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(connection_id) DO UPDATE SET
                owner_id = excluded.owner_id,
                owner_chat_id = excluded.owner_chat_id,
                is_enabled = excluded.is_enabled,
                can_read = excluded.can_read,
                can_delete_sent = excluded.can_delete_sent,
                updated_at = excluded.updated_at
            """,
            (
                conn.connection_id,
                conn.owner_id,
                conn.owner_chat_id,
                int(conn.is_enabled),
                int(conn.can_read),
                int(conn.can_delete_sent),
                int(time.time()),
            ),
        )
        await self.db.commit()

    async def get_connection(self, connection_id: str) -> Connection | None:
        async with self.db.execute(
            "SELECT * FROM connections WHERE connection_id = ?", (connection_id,)
        ) as cursor:
            row = await cursor.fetchone()
        if row is None:
            return None
        return Connection(
            connection_id=row["connection_id"],
            owner_id=row["owner_id"],
            owner_chat_id=row["owner_chat_id"],
            is_enabled=bool(row["is_enabled"]),
            can_read=bool(row["can_read"]),
            can_delete_sent=bool(row["can_delete_sent"]),
        )

    async def disable_connection(self, connection_id: str) -> None:
        await self.db.execute(
            "UPDATE connections SET is_enabled = 0, updated_at = ? WHERE connection_id = ?",
            (int(time.time()), connection_id),
        )
        await self.db.commit()

    # ----------------------------------------------------------------------- prefs

    async def get_prefs(self, owner_id: int) -> Prefs:
        async with self.db.execute("SELECT * FROM prefs WHERE owner_id = ?", (owner_id,)) as cursor:
            row = await cursor.fetchone()
        if row is None:
            prefs = Prefs(owner_id=owner_id)
            await self.db.execute(
                "INSERT OR IGNORE INTO prefs (owner_id) VALUES (?)",
                (owner_id,),
            )
            await self.db.commit()
            return prefs
        return Prefs(
            owner_id=row["owner_id"],
            notify_deleted=bool(row["notify_deleted"]),
            notify_edited=bool(row["notify_edited"]),
            capture_once=bool(row["capture_once"]),
            include_own=bool(row["include_own"]),
            capture_any_media=bool(row["capture_any_media"]),
            language=row["language"],
        )

    async def toggle_pref(self, owner_id: int, key: str) -> Prefs:
        if key not in PREF_KEYS:
            raise ValueError(f"unknown preference: {key}")
        await self.get_prefs(owner_id)  # make sure the row exists
        await self.db.execute(
            f"UPDATE prefs SET {key} = 1 - {key} WHERE owner_id = ?",  # key is allow-listed above
            (owner_id,),
        )
        await self.db.commit()
        return await self.get_prefs(owner_id)

    async def set_language(self, owner_id: int, language: str) -> Prefs:
        await self.get_prefs(owner_id)
        await self.db.execute(
            "UPDATE prefs SET language = ? WHERE owner_id = ?",
            (language, owner_id),
        )
        await self.db.commit()
        return await self.get_prefs(owner_id)

    # ------------------------------------------------------------------- snapshots

    async def put_snapshot(self, snapshot: Snapshot) -> None:
        await self.db.execute(
            """
            INSERT INTO snapshots
                (connection_id, chat_id, message_id, owner_id, sender_id, sender_name,
                 is_outgoing, sent_at, saved_at, text, entities, media_type,
                 file_id, file_unique_id, file_path, extra)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(connection_id, chat_id, message_id) DO UPDATE SET
                text = excluded.text,
                entities = excluded.entities,
                media_type = excluded.media_type,
                file_id = excluded.file_id,
                file_unique_id = excluded.file_unique_id,
                file_path = COALESCE(excluded.file_path, snapshots.file_path),
                extra = excluded.extra,
                saved_at = excluded.saved_at
            """,
            (
                snapshot.connection_id,
                snapshot.chat_id,
                snapshot.message_id,
                snapshot.owner_id,
                snapshot.sender_id,
                snapshot.sender_name,
                int(snapshot.is_outgoing),
                snapshot.sent_at,
                snapshot.saved_at or int(time.time()),
                snapshot.text,
                json.dumps(snapshot.entities, ensure_ascii=False) if snapshot.entities else None,
                snapshot.media_type,
                snapshot.file_id,
                snapshot.file_unique_id,
                snapshot.file_path,
                json.dumps(snapshot.extra, ensure_ascii=False) if snapshot.extra else None,
            ),
        )
        await self.db.commit()

    async def get_snapshot(
        self, connection_id: str, chat_id: int, message_id: int
    ) -> Snapshot | None:
        async with self.db.execute(
            """
            SELECT * FROM snapshots
            WHERE connection_id = ? AND chat_id = ? AND message_id = ?
            """,
            (connection_id, chat_id, message_id),
        ) as cursor:
            row = await cursor.fetchone()
        return _row_to_snapshot(row) if row is not None else None

    async def pop_snapshots(
        self, connection_id: str, chat_id: int, message_ids: list[int]
    ) -> list[Snapshot]:
        """Read snapshots for the given ids and forget them.

        Deleted messages are handed to the owner exactly once; keeping them any
        longer only grows the database.
        """
        if not message_ids:
            return []
        placeholders = ",".join("?" * len(message_ids))
        params = [connection_id, chat_id, *message_ids]
        async with self.db.execute(
            f"""
            SELECT * FROM snapshots
            WHERE connection_id = ? AND chat_id = ? AND message_id IN ({placeholders})
            ORDER BY message_id
            """,  # placeholders are generated, values stay parameterised
            params,
        ) as cursor:
            rows = await cursor.fetchall()
        await self.db.execute(
            f"""
            DELETE FROM snapshots
            WHERE connection_id = ? AND chat_id = ? AND message_id IN ({placeholders})
            """,
            params,
        )
        await self.db.commit()
        return [_row_to_snapshot(row) for row in rows]

    async def purge_older_than(self, seconds: int) -> list[str]:
        """Drop snapshots older than ``seconds``; returns cached file paths to unlink."""
        threshold = int(time.time()) - seconds
        async with self.db.execute(
            "SELECT file_path FROM snapshots WHERE saved_at < ? AND file_path IS NOT NULL",
            (threshold,),
        ) as cursor:
            rows = await cursor.fetchall()
        await self.db.execute("DELETE FROM snapshots WHERE saved_at < ?", (threshold,))
        await self.db.commit()
        return [row["file_path"] for row in rows]

    async def forget_owner(self, owner_id: int) -> int:
        """Delete every snapshot of an owner (used by /purge and on disconnect)."""
        cursor = await self.db.execute("DELETE FROM snapshots WHERE owner_id = ?", (owner_id,))
        await self.db.commit()
        return cursor.rowcount if cursor.rowcount > 0 else 0

    async def stats(self, owner_id: int) -> dict[str, int]:
        async with self.db.execute(
            "SELECT COUNT(*) AS n FROM snapshots WHERE owner_id = ?", (owner_id,)
        ) as cursor:
            row = await cursor.fetchone()
        snapshots = int(row["n"]) if row else 0
        async with self.db.execute(
            "SELECT COUNT(*) AS n FROM connections WHERE owner_id = ? AND is_enabled = 1",
            (owner_id,),
        ) as cursor:
            row = await cursor.fetchone()
        return {"snapshots": snapshots, "connections": int(row["n"]) if row else 0}


def _row_to_snapshot(row: aiosqlite.Row) -> Snapshot:
    return Snapshot(
        connection_id=row["connection_id"],
        chat_id=row["chat_id"],
        message_id=row["message_id"],
        owner_id=row["owner_id"],
        sender_id=row["sender_id"],
        sender_name=row["sender_name"],
        is_outgoing=bool(row["is_outgoing"]),
        sent_at=row["sent_at"],
        saved_at=row["saved_at"],
        text=row["text"],
        entities=json.loads(row["entities"]) if row["entities"] else [],
        media_type=row["media_type"],
        file_id=row["file_id"],
        file_unique_id=row["file_unique_id"],
        file_path=row["file_path"],
        extra=json.loads(row["extra"]) if row["extra"] else {},
    )
