"""Plain private-chat commands: /start, /help, /status, /purge."""

from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from ..storage import Storage
from ..texts import t

router = Router(name="common")
router.message.filter(F.chat.type == "private")


@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot, storage: Storage) -> None:
    # The `?start=settings` deep link is claimed earlier, by the settings router.
    prefs = await storage.get_prefs(message.chat.id)
    me = await bot.me()
    await message.answer(t(prefs.language, "start", bot_username=f"@{me.username}"))


@router.message(Command("help"))
async def cmd_help(message: Message, storage: Storage) -> None:
    prefs = await storage.get_prefs(message.chat.id)
    await message.answer(t(prefs.language, "help"))


@router.message(Command("status"))
async def cmd_status(message: Message, storage: Storage) -> None:
    prefs = await storage.get_prefs(message.chat.id)
    stats = await storage.stats(message.chat.id)
    if not stats["connections"]:
        await message.answer(t(prefs.language, "not_connected"))
        return
    await message.answer(t(prefs.language, "status", **stats))


@router.message(Command("purge"))
async def cmd_purge(message: Message, storage: Storage) -> None:
    prefs = await storage.get_prefs(message.chat.id)
    removed = await storage.forget_owner(message.chat.id)
    await message.answer(t(prefs.language, "purged", count=removed))
