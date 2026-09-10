"""Building the notification cards the owner actually sees."""

from __future__ import annotations

import html
from datetime import datetime, timezone

from aiogram.types import Chat, Message, User

from .storage import Snapshot
from .texts import t

MEDIA_NAMES = {
    "photo": "🖼 фото",
    "video": "🎬 видео",
    "animation": "🎞 GIF",
    "video_note": "⭕️ видеосообщение",
    "voice": "🎤 голосовое",
    "audio": "🎵 аудио",
    "document": "📄 файл",
    "sticker": "🩹 стикер",
}

MEDIA_NAMES_EN = {
    "photo": "🖼 photo",
    "video": "🎬 video",
    "animation": "🎞 GIF",
    "video_note": "⭕️ video message",
    "voice": "🎤 voice message",
    "audio": "🎵 audio",
    "document": "📄 file",
    "sticker": "🩹 sticker",
}


def esc(value: str | None) -> str:
    return html.escape(value or "", quote=False)


def user_title(user: User | None) -> str:
    if user is None:
        return "—"
    name = " ".join(part for part in (user.first_name, user.last_name) if part).strip()
    if user.username:
        return f"{name} (@{user.username})" if name else f"@{user.username}"
    return name or str(user.id)


def chat_title(chat: Chat | None) -> str:
    if chat is None:
        return "—"
    if chat.title:
        return chat.title
    name = " ".join(part for part in (chat.first_name, chat.last_name) if part).strip()
    if chat.username:
        return f"{name} (@{chat.username})" if name else f"@{chat.username}"
    return name or str(chat.id)


def media_name(kind: str | None, language: str) -> str:
    if not kind:
        return ""
    table = MEDIA_NAMES_EN if language == "en" else MEDIA_NAMES
    return table.get(kind, kind)


def _timestamp(value: int | float | datetime | None) -> str:
    if value is None:
        return "—"
    if isinstance(value, datetime):
        moment = value
    else:
        moment = datetime.fromtimestamp(value, tz=timezone.utc)
    return moment.astimezone().strftime("%d.%m.%Y %H:%M:%S")


def _quote(text: str | None) -> str:
    if not text:
        return ""
    return f"<blockquote expandable>{esc(text)}</blockquote>"


def _meta_lines(
    language: str, *, sender: str, chat: str, when: str, media: str | None = None
) -> list[str]:
    lines = [
        f"{t(language, 'from_label')}: {esc(sender)}",
        f"{t(language, 'chat_label')}: {esc(chat)}",
        f"{t(language, 'time_label')}: {when}",
    ]
    if media:
        lines.append(f"{t(language, 'media_label')}: {media}")
    return lines


def deleted_card(snapshot: Snapshot, language: str, chat_name: str) -> str:
    """Card shown when the interlocutor deletes a message."""
    parts = [t(language, "deleted_header"), ""]
    parts += _meta_lines(
        language,
        sender=snapshot.sender_name or "—",
        chat=chat_name,
        when=_timestamp(snapshot.sent_at),
        media=media_name(snapshot.media_type, language) or None,
    )
    body = _quote(snapshot.text)
    if body:
        parts += ["", body]
    elif not snapshot.media_type:
        parts += ["", t(language, "no_content")]
    return "\n".join(parts)


def edited_card(old: Snapshot | None, new: Message, language: str) -> str:
    """Card shown when the interlocutor edits a message: both versions side by side."""
    new_text = new.text or new.caption
    parts = [t(language, "edited_header"), ""]
    parts += _meta_lines(
        language,
        sender=user_title(new.from_user),
        chat=chat_title(new.chat),
        when=_timestamp(new.edit_date or new.date),
    )
    parts += ["", t(language, "old_version")]
    if old is not None and old.text:
        parts.append(_quote(old.text))
    else:
        parts.append(t(language, "no_content"))
    parts += ["", t(language, "new_version"), _quote(new_text)]
    return "\n".join(parts)


def once_card(message: Message, language: str, kind: str | None) -> str:
    """Card attached to a rescued view-once file."""
    parts = [t(language, "once_header"), ""]
    parts += _meta_lines(
        language,
        sender=user_title(message.from_user),
        chat=chat_title(message.chat),
        when=_timestamp(message.date),
        media=media_name(kind, language) or None,
    )
    caption = message.caption
    if caption:
        parts += ["", _quote(caption)]
    return "\n".join(parts)
