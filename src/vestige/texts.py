"""User-facing strings. Russian is the default, English is the fallback locale."""

from __future__ import annotations

from typing import Any

DEFAULT_LANGUAGE = "ru"

RU: dict[str, str] = {
    "start": (
        "<b>Vestige</b> — хранитель следов.\n\n"
        "Я подключаюсь к вашему аккаунту как чат-бот и сохраняю то, что исчезает:\n"
        "• 🗑 <b>удалённые сообщения</b> — пришлю копию сразу после удаления;\n"
        "• ✏️ <b>изменённые сообщения</b> — покажу старую и новую версию;\n"
        "• 🔥 <b>одноразовые медиа</b> — ответьте на файл до просмотра, и он останется у вас.\n\n"
        "<b>Как подключить (Telegram Premium не нужен):</b>\n"
        "1. Откройте свой профиль и нажмите «Изм.»\n"
        "2. Найдите раздел «Автоматизация чатов»\n"
        "3. Введите {bot_username} и нажмите «Добавить»\n\n"
        "Затем откройте /settings — там включается и отключается каждое уведомление."
    ),
    "help": (
        "<b>Команды</b>\n"
        "/start — как подключить бота\n"
        "/settings — включить и отключить уведомления\n"
        "/status — состояние подключения и статистика\n"
        "/purge — стереть все сохранённые снимки\n"
        "/help — эта справка\n\n"
        "<b>Одноразовые медиа.</b> Перед просмотром ответьте на одноразовый файл "
        "любым сообщением — я сохраню его вам."
    ),
    "settings_title": ("⚙️ <b>Настройки</b>\n\nНажмите на пункт, чтобы включить или отключить его."),
    "settings_saved": "Сохранено",
    "pref_notify_deleted": "🗑 Уведомления об удалении",
    "pref_notify_edited": "✏️ Уведомления об изменении",
    "pref_capture_once": "🔥 Сохранение одноразок",
    "pref_include_own": "👤 Учитывать мои сообщения",
    "pref_capture_any_media": "📎 Сохранять любое медиа в ответе",
    "pref_on": "вкл",
    "pref_off": "выкл",
    "btn_language": "🌐 Язык: Русский",
    "connected": (
        "✅ Бот подключён к вашему аккаунту.\n\n"
        "Теперь я слежу за удалёнными и изменёнными сообщениями. "
        "Настроить уведомления: /settings"
    ),
    "disconnected": "👋 Бот отключён от вашего аккаунта. Сохранённые снимки удалены.",
    "no_read_right": (
        "⚠️ У бота нет права <b>читать сообщения</b>, поэтому уведомления работать не будут.\n"
        "Профиль → «Изм.» → «Автоматизация чатов» → разрешите боту читать сообщения."
    ),
    "deleted_header": "🗑 <b>Удалённое сообщение</b>",
    "edited_header": "✏️ <b>Изменённое сообщение</b>",
    "once_header": "🔥 <b>Одноразовое сообщение сохранено</b>",
    "old_version": "<b>Было:</b>",
    "new_version": "<b>Стало:</b>",
    "from_label": "От",
    "chat_label": "Чат",
    "time_label": "Время",
    "media_label": "Вложение",
    "no_content": "<i>Содержимое не сохранилось — сообщение пришло до подключения бота.</i>",
    "media_lost": "<i>Файл больше недоступен: Telegram отозвал ссылку на него.</i>",
    "status": (
        "<b>Состояние</b>\n"
        "Активных подключений: {connections}\n"
        "Сохранённых снимков: {snapshots}\n\n"
        "Настройки: /settings"
    ),
    "purged": "🧹 Удалено снимков: {count}.",
    "not_connected": ("Бот ещё не подключён к вашему аккаунту. Как это сделать — /start"),
}

EN: dict[str, str] = {
    "start": (
        "<b>Vestige</b> — the keeper of traces.\n\n"
        "I connect to your account as a chatbot and save what disappears:\n"
        "• 🗑 <b>deleted messages</b> — a copy arrives the moment they are gone;\n"
        "• ✏️ <b>edited messages</b> — you get both the old and the new version;\n"
        "• 🔥 <b>view-once media</b> — reply to the file before opening it "
        "and it stays with you.\n\n"
        "<b>How to connect (no Telegram Premium needed):</b>\n"
        "1. Open your profile and tap “Edit”\n"
        "2. Find the “Chatbots” section\n"
        "3. Enter {bot_username} and tap “Add”\n\n"
        "Then open /settings to turn each notification on or off."
    ),
    "help": (
        "<b>Commands</b>\n"
        "/start — how to connect the bot\n"
        "/settings — turn notifications on and off\n"
        "/status — connection state and statistics\n"
        "/purge — wipe every stored snapshot\n"
        "/help — this message\n\n"
        "<b>View-once media.</b> Reply to the file with any message before opening it "
        "and I will save it for you."
    ),
    "settings_title": "⚙️ <b>Settings</b>\n\nTap an item to turn it on or off.",
    "settings_saved": "Saved",
    "pref_notify_deleted": "🗑 Deletion alerts",
    "pref_notify_edited": "✏️ Edit alerts",
    "pref_capture_once": "🔥 Save view-once media",
    "pref_include_own": "👤 Include my own messages",
    "pref_capture_any_media": "📎 Save any replied-to media",
    "pref_on": "on",
    "pref_off": "off",
    "btn_language": "🌐 Language: English",
    "connected": (
        "✅ The bot is connected to your account.\n\n"
        "I am watching for deleted and edited messages now. Tune it: /settings"
    ),
    "disconnected": "👋 The bot was disconnected. Stored snapshots have been removed.",
    "no_read_right": (
        "⚠️ The bot has no <b>read messages</b> right, so alerts will not work.\n"
        "Profile → “Edit” → “Chatbots” → allow the bot to read messages."
    ),
    "deleted_header": "🗑 <b>Deleted message</b>",
    "edited_header": "✏️ <b>Edited message</b>",
    "once_header": "🔥 <b>View-once message saved</b>",
    "old_version": "<b>Before:</b>",
    "new_version": "<b>After:</b>",
    "from_label": "From",
    "chat_label": "Chat",
    "time_label": "Time",
    "media_label": "Attachment",
    "no_content": "<i>Nothing was stored — the message predates the connection.</i>",
    "media_lost": "<i>The file is gone: Telegram revoked its reference.</i>",
    "status": (
        "<b>Status</b>\n"
        "Active connections: {connections}\n"
        "Stored snapshots: {snapshots}\n\n"
        "Settings: /settings"
    ),
    "purged": "🧹 Snapshots removed: {count}.",
    "not_connected": "The bot is not connected to your account yet. See /start",
}

LANGUAGES: dict[str, dict[str, str]] = {"ru": RU, "en": EN}


def t(language: str, key: str, **kwargs: Any) -> str:
    table = LANGUAGES.get(language, RU)
    template = table.get(key) or RU.get(key) or key
    return template.format(**kwargs) if kwargs else template


def next_language(language: str) -> str:
    order = list(LANGUAGES)
    if language not in order:
        return DEFAULT_LANGUAGE
    return order[(order.index(language) + 1) % len(order)]
