"""Turning live business messages into snapshots we can resurrect later."""

from __future__ import annotations

import logging
import time

from aiogram import Bot
from aiogram.types import Message

from .config import Settings
from .media import cache_to_disk, extract_media
from .render import user_title
from .storage import Connection, Snapshot, Storage

log = logging.getLogger(__name__)


def build_snapshot(message: Message, connection: Connection) -> Snapshot:
    media = extract_media(message)
    sender = message.from_user
    return Snapshot(
        connection_id=connection.connection_id,
        chat_id=message.chat.id,
        message_id=message.message_id,
        owner_id=connection.owner_id,
        sender_id=sender.id if sender else None,
        sender_name=user_title(sender),
        is_outgoing=bool(sender and sender.id == connection.owner_id),
        sent_at=int(message.date.timestamp()),
        saved_at=int(time.time()),
        text=message.text or message.caption,
        entities=[e.model_dump(exclude_none=True) for e in message.entities or []],
        media_type=media.kind if media else None,
        file_id=media.file_id if media else None,
        file_unique_id=media.file_unique_id if media else None,
        extra={"has_media_spoiler": bool(message.has_media_spoiler)}
        if message.has_media_spoiler
        else {},
    )


async def capture_message(
    bot: Bot,
    storage: Storage,
    settings: Settings,
    message: Message,
    connection: Connection,
) -> Snapshot:
    """Store a snapshot of ``message``, optionally pulling the media onto disk."""
    snapshot = build_snapshot(message, connection)

    if settings.cache_media and snapshot.file_id:
        media = extract_media(message)
        if media is not None:
            snapshot.file_path = await cache_to_disk(
                bot, media, settings.media_dir, settings.max_cache_file_bytes
            )

    await storage.put_snapshot(snapshot)
    return snapshot
