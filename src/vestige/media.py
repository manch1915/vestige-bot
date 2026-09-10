"""Extracting media from a Message and putting it back together for the owner."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aiogram import Bot
from aiogram.types import BufferedInputFile, Message

log = logging.getLogger(__name__)

# Attributes of Message that carry a downloadable file, in the order we probe them.
MEDIA_ATTRS = (
    "photo",
    "video",
    "animation",
    "video_note",
    "voice",
    "audio",
    "document",
    "sticker",
)

# Fields Telegram uses (now or in older layers) to mark self-destructing content.
# aiogram keeps unknown API fields in ``model_extra``, so new spellings are picked
# up without a library upgrade.
ONE_TIME_FLAGS = ("view_once", "is_one_time", "one_time", "self_destruct", "ttl_seconds")


@dataclass(slots=True)
class MediaRef:
    kind: str
    file_id: str
    file_unique_id: str
    file_size: int | None = None
    file_name: str | None = None


def extract_media(message: Message) -> MediaRef | None:
    """Return a reference to the single downloadable file of ``message``, if any."""
    for attr in MEDIA_ATTRS:
        value = getattr(message, attr, None)
        if not value:
            continue
        item = value[-1] if attr == "photo" else value  # photo is a list of sizes
        return MediaRef(
            kind=attr,
            file_id=item.file_id,
            file_unique_id=item.file_unique_id,
            file_size=getattr(item, "file_size", None),
            file_name=getattr(item, "file_name", None),
        )
    return None


def _extra_flags(obj: Any) -> dict[str, Any]:
    extra = getattr(obj, "model_extra", None)
    return extra if isinstance(extra, dict) else {}


def is_one_time(message: Message) -> bool:
    """Best-effort detection of view-once (self-destructing) media.

    The Bot API does not expose a stable, documented flag for it, so we look for
    any of the known spellings both on the message and on the media object. When
    Telegram sends nothing at all we return ``False`` and let the user's
    ``capture_any_media`` preference decide.
    """
    candidates: list[Any] = [message]
    media = extract_media(message)
    if media is not None:
        candidates.append(getattr(message, media.kind, None))

    for candidate in candidates:
        flags = _extra_flags(candidate)
        for name in ONE_TIME_FLAGS:
            value = flags.get(name)
            if isinstance(value, bool) and value:
                return True
            if isinstance(value, int) and not isinstance(value, bool) and value > 0:
                return True
    return False


async def cache_to_disk(bot: Bot, media: MediaRef, media_dir: Path, max_bytes: int) -> str | None:
    """Download the file next to the snapshot so it outlives the original message."""
    if media.file_size is not None and media.file_size > max_bytes:
        log.info("skip caching %s: %s bytes over the limit", media.file_unique_id, media.file_size)
        return None
    try:
        file = await bot.get_file(media.file_id)
        if not file.file_path:
            return None
        suffix = Path(file.file_path).suffix or ".bin"
        target = media_dir / f"{media.file_unique_id}{suffix}"
        if not target.exists():
            media_dir.mkdir(parents=True, exist_ok=True)
            await bot.download_file(file.file_path, destination=target)
        return str(target)
    except Exception:
        log.exception("failed to cache media %s", media.file_unique_id)
        return None


async def send_media(
    bot: Bot,
    chat_id: int,
    *,
    kind: str,
    file_id: str | None,
    file_path: str | None,
    caption: str | None = None,
) -> Message | None:
    """Re-send saved media to the owner.

    Tries the original ``file_id`` first — it stays valid for a while even after
    the message itself is gone — and falls back to the locally cached copy.
    """
    senders = {
        "photo": bot.send_photo,
        "video": bot.send_video,
        "animation": bot.send_animation,
        "video_note": bot.send_video_note,
        "voice": bot.send_voice,
        "audio": bot.send_audio,
        "document": bot.send_document,
        "sticker": bot.send_sticker,
    }
    sender = senders.get(kind, bot.send_document)
    # send_video_note and send_sticker do not accept a caption.
    supports_caption = kind not in {"video_note", "sticker"}
    kwargs: dict[str, Any] = {"caption": caption, "parse_mode": "HTML"} if supports_caption else {}

    if file_id:
        try:
            return await sender(chat_id, file_id, **kwargs)  # type: ignore[operator]
        except Exception as err:  # noqa: BLE001
            log.warning("re-sending by file_id failed (%s), falling back to disk: %s", kind, err)

    if file_path and Path(file_path).exists():
        path = Path(file_path)
        payload = BufferedInputFile(await asyncio.to_thread(path.read_bytes), filename=path.name)
        try:
            return await sender(chat_id, payload, **kwargs)  # type: ignore[operator]
        except Exception:
            log.exception("re-sending cached file failed (%s)", kind)

    return None
