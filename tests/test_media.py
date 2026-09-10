from __future__ import annotations

from datetime import datetime, timezone

from aiogram.types import Chat, Message, PhotoSize, Voice

from vestige.media import extract_media, is_one_time

CHAT = Chat(id=100, type="private", first_name="Полина")
NOW = datetime.now(tz=timezone.utc)


def photo_message(**extra) -> Message:
    return Message(
        message_id=1,
        date=NOW,
        chat=CHAT,
        photo=[
            PhotoSize(file_id="small", file_unique_id="u-small", width=90, height=90),
            PhotoSize(
                file_id="big", file_unique_id="u-big", width=1280, height=1280, file_size=4096
            ),
        ],
        **extra,
    )


def test_extract_media_picks_the_largest_photo() -> None:
    media = extract_media(photo_message())
    assert media is not None
    assert media.kind == "photo"
    assert media.file_id == "big"
    assert media.file_size == 4096


def test_extract_media_handles_voice() -> None:
    message = Message(
        message_id=2,
        date=NOW,
        chat=CHAT,
        voice=Voice(file_id="v", file_unique_id="u-v", duration=3),
    )
    media = extract_media(message)
    assert media is not None
    assert media.kind == "voice"


def test_extract_media_returns_none_for_text() -> None:
    assert extract_media(Message(message_id=3, date=NOW, chat=CHAT, text="привет")) is None


def test_plain_media_is_not_one_time() -> None:
    assert is_one_time(photo_message()) is False


def test_one_time_flag_on_message_is_detected() -> None:
    assert is_one_time(photo_message(view_once=True)) is True


def test_ttl_seconds_marks_one_time() -> None:
    assert is_one_time(photo_message(ttl_seconds=5)) is True


def test_zero_ttl_is_not_one_time() -> None:
    assert is_one_time(photo_message(ttl_seconds=0)) is False
