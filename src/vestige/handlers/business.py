"""Everything that arrives through a business connection.

Four updates matter here:

``business_connection``      the bot was added to / removed from an account
``business_message``         a new message in one of the account's chats
``edited_business_message``  someone edited a message we already know
``deleted_business_messages``someone deleted messages — ids only, no content
"""

from __future__ import annotations

import logging

from aiogram import Bot, Router
from aiogram.types import BusinessConnection, BusinessMessagesDeleted, Message

from ..capture import capture_message
from ..config import Settings
from ..media import extract_media, is_one_time, send_media
from ..render import chat_title, deleted_card, edited_card, once_card
from ..storage import Connection, Snapshot, Storage
from ..texts import t

log = logging.getLogger(__name__)

router = Router(name="business")

# Telegram caps captions at 1024 characters; longer cards go out as a separate message.
CAPTION_LIMIT = 1024


@router.business_connection()
async def on_connection(event: BusinessConnection, bot: Bot, storage: Storage) -> None:
    rights = event.rights
    connection = Connection(
        connection_id=event.id,
        owner_id=event.user.id,
        owner_chat_id=event.user_chat_id,
        is_enabled=event.is_enabled,
        can_read=bool(getattr(rights, "can_read_messages", False)),
        can_delete_sent=bool(getattr(rights, "can_delete_sent_messages", False)),
    )
    await storage.save_connection(connection)
    prefs = await storage.get_prefs(connection.owner_id)

    if not event.is_enabled:
        await storage.disable_connection(event.id)
        await storage.forget_owner(connection.owner_id)
        await bot.send_message(connection.owner_chat_id, t(prefs.language, "disconnected"))
        return

    await bot.send_message(connection.owner_chat_id, t(prefs.language, "connected"))
    if not connection.can_read:
        await bot.send_message(connection.owner_chat_id, t(prefs.language, "no_read_right"))


@router.business_message()
async def on_business_message(
    message: Message, bot: Bot, storage: Storage, settings: Settings
) -> None:
    connection = await _resolve(storage, message.business_connection_id)
    if connection is None:
        return

    await capture_message(bot, storage, settings, message, connection)
    await _maybe_rescue_one_time(message, bot, storage, connection)


@router.edited_business_message()
async def on_edited_business_message(
    message: Message, bot: Bot, storage: Storage, settings: Settings
) -> None:
    connection = await _resolve(storage, message.business_connection_id)
    if connection is None:
        return

    old = await storage.get_snapshot(connection.connection_id, message.chat.id, message.message_id)
    # Re-snapshot first: even if the owner muted edit alerts, a later deletion
    # should show the newest text.
    await capture_message(bot, storage, settings, message, connection)

    prefs = await storage.get_prefs(connection.owner_id)
    if not prefs.notify_edited:
        return
    is_own = bool(message.from_user and message.from_user.id == connection.owner_id)
    if is_own and not prefs.include_own:
        return
    if old is not None and (old.text or None) == (message.text or message.caption or None):
        return  # media-only edit with identical text: nothing to show

    await bot.send_message(
        connection.owner_chat_id,
        edited_card(old, message, prefs.language),
        parse_mode="HTML",
    )


@router.deleted_business_messages()
async def on_deleted_business_messages(
    event: BusinessMessagesDeleted, bot: Bot, storage: Storage
) -> None:
    connection = await _resolve(storage, event.business_connection_id)
    if connection is None:
        return

    prefs = await storage.get_prefs(connection.owner_id)
    snapshots = await storage.pop_snapshots(
        connection.connection_id, event.chat.id, list(event.message_ids)
    )
    if not prefs.notify_deleted:
        return

    chat_name = chat_title(event.chat)
    for snapshot in snapshots:
        if snapshot.is_outgoing and not prefs.include_own:
            continue
        await _deliver(bot, connection.owner_chat_id, snapshot, prefs.language, chat_name)


# --------------------------------------------------------------------------- helpers


async def _resolve(storage: Storage, connection_id: str | None) -> Connection | None:
    if not connection_id:
        return None
    connection = await storage.get_connection(connection_id)
    if connection is None or not connection.is_enabled:
        log.debug("update from unknown or disabled connection %s", connection_id)
        return None
    return connection


async def _deliver(
    bot: Bot, chat_id: int, snapshot: Snapshot, language: str, chat_name: str
) -> None:
    """Send one deletion card, with the media attached when there is any."""
    card = deleted_card(snapshot, language, chat_name)

    if snapshot.media_type:
        caption = card if len(card) <= CAPTION_LIMIT else None
        sent = await send_media(
            bot,
            chat_id,
            kind=snapshot.media_type,
            file_id=snapshot.file_id,
            file_path=snapshot.file_path,
            caption=caption,
        )
        if sent is not None:
            if caption is None:
                await bot.send_message(chat_id, card, parse_mode="HTML")
            return
        card = f"{card}\n\n{t(language, 'media_lost')}"

    await bot.send_message(chat_id, card, parse_mode="HTML")


async def _maybe_rescue_one_time(
    message: Message, bot: Bot, storage: Storage, connection: Connection
) -> None:
    """Save a view-once file when the owner replies to it before opening it.

    Telegram delivers the replied-to message inside the reply, so the file is
    still reachable at this moment — once the owner opens it, it is gone.
    """
    original = message.reply_to_message
    if original is None:
        return
    is_owner_reply = bool(message.from_user and message.from_user.id == connection.owner_id)
    if not is_owner_reply:
        return

    media = extract_media(original)
    if media is None:
        return
    if original.from_user and original.from_user.id == connection.owner_id:
        return  # the owner's own file, nothing to rescue

    prefs = await storage.get_prefs(connection.owner_id)
    if not prefs.capture_once:
        return
    if not (is_one_time(original) or prefs.capture_any_media):
        return

    card = once_card(original, prefs.language, media.kind)
    caption = card if len(card) <= CAPTION_LIMIT else None
    sent = await send_media(
        bot,
        connection.owner_chat_id,
        kind=media.kind,
        file_id=media.file_id,
        file_path=None,
        caption=caption,
    )
    if sent is None:
        await bot.send_message(
            connection.owner_chat_id,
            f"{card}\n\n{t(prefs.language, 'media_lost')}",
            parse_mode="HTML",
        )
    elif caption is None:
        await bot.send_message(connection.owner_chat_id, card, parse_mode="HTML")
