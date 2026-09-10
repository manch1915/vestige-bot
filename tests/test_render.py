from __future__ import annotations

from datetime import datetime, timezone

from aiogram.types import Chat, Message, User

from vestige.render import chat_title, deleted_card, edited_card, once_card, user_title
from vestige.storage import Snapshot

CHAT = Chat(id=100, type="private", first_name="Полина")
NOW = datetime.now(tz=timezone.utc)


def snapshot(**overrides) -> Snapshot:
    payload = {
        "connection_id": "conn-1",
        "chat_id": 100,
        "message_id": 1,
        "owner_id": 42,
        "sent_at": int(NOW.timestamp()),
        "sender_name": "Полина",
        "text": "<b>не разметка</b>",
    }
    payload.update(overrides)
    return Snapshot(**payload)


def test_user_title_prefers_name_with_username() -> None:
    user = User(id=1, is_bot=False, first_name="Иван", last_name="Петров", username="ivan")
    assert user_title(user) == "Иван Петров (@ivan)"


def test_user_title_falls_back_to_id() -> None:
    assert user_title(User(id=7, is_bot=False, first_name="")) == "7"


def test_chat_title_for_private_chat() -> None:
    assert chat_title(CHAT) == "Полина"


def test_deleted_card_escapes_message_text() -> None:
    card = deleted_card(snapshot(), "ru", "Полина")
    assert "&lt;b&gt;не разметка&lt;/b&gt;" in card
    assert "Удалённое сообщение" in card


def test_deleted_card_reports_missing_content() -> None:
    card = deleted_card(snapshot(text=None), "ru", "Полина")
    assert "Содержимое не сохранилось" in card


def test_deleted_card_names_the_attachment() -> None:
    card = deleted_card(snapshot(text=None, media_type="voice"), "ru", "Полина")
    assert "голосовое" in card
    assert "Содержимое не сохранилось" not in card


def test_edited_card_shows_both_versions() -> None:
    new = Message(message_id=1, date=NOW, chat=CHAT, text="после")
    card = edited_card(snapshot(text="до"), new, "ru")
    assert "Было:" in card
    assert "до" in card
    assert "Стало:" in card
    assert "после" in card


def test_edited_card_without_a_snapshot() -> None:
    new = Message(message_id=1, date=NOW, chat=CHAT, text="после")
    card = edited_card(None, new, "en")
    assert "Nothing was stored" in card


def test_once_card_mentions_the_media_kind() -> None:
    original = Message(message_id=5, date=NOW, chat=CHAT, caption="подпись")
    card = once_card(original, "ru", "photo")
    assert "Одноразовое сообщение сохранено" in card
    assert "фото" in card
    assert "подпись" in card
