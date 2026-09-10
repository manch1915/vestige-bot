"""The settings section: t.me/<bot>?start=settings or /settings.

Every notification the bot can produce is a switch here, so a user who is annoyed
by, say, edit alerts can turn just those off and keep the rest.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from ..storage import PREF_KEYS, Prefs, Storage
from ..texts import next_language, t

router = Router(name="settings")

CALLBACK_PREFIX = "pref"


def settings_keyboard(prefs: Prefs) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for key in PREF_KEYS:
        enabled = getattr(prefs, key)
        mark = "✅" if enabled else "☑️"
        state = t(prefs.language, "pref_on" if enabled else "pref_off")
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{mark} {t(prefs.language, f'pref_{key}')} — {state}",
                    callback_data=f"{CALLBACK_PREFIX}:{key}",
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text=t(prefs.language, "btn_language"),
                callback_data=f"{CALLBACK_PREFIX}:lang",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def show_settings(message: Message, storage: Storage) -> None:
    prefs = await storage.get_prefs(message.chat.id)
    await message.answer(t(prefs.language, "settings_title"), reply_markup=settings_keyboard(prefs))


@router.message(CommandStart(deep_link=True, magic=F.args == "settings"), F.chat.type == "private")
async def deep_link_settings(message: Message, storage: Storage) -> None:
    await show_settings(message, storage)


@router.message(Command("settings"), F.chat.type == "private")
async def cmd_settings(message: Message, storage: Storage) -> None:
    await show_settings(message, storage)


@router.callback_query(F.data.startswith(f"{CALLBACK_PREFIX}:"))
async def toggle(callback: CallbackQuery, storage: Storage) -> None:
    owner_id = callback.from_user.id
    _, key = callback.data.split(":", 1)

    if key == "lang":
        prefs = await storage.get_prefs(owner_id)
        prefs = await storage.set_language(owner_id, next_language(prefs.language))
    elif key in PREF_KEYS:
        prefs = await storage.toggle_pref(owner_id, key)
    else:
        await callback.answer()
        return

    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            t(prefs.language, "settings_title"), reply_markup=settings_keyboard(prefs)
        )
    await callback.answer(t(prefs.language, "settings_saved"))
