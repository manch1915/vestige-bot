"""Dependency injection for handlers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from .config import Settings
from .storage import Storage


class DependenciesMiddleware(BaseMiddleware):
    """Put ``storage`` and ``settings`` into every handler's kwargs.

    Set explicitly instead of relying on dispatcher workflow data, so the names
    cannot be shadowed by aiogram's own context keys.
    """

    def __init__(self, storage: Storage, settings: Settings) -> None:
        self._storage = storage
        self._settings = settings

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        data["storage"] = self._storage
        data["settings"] = self._settings
        return await handler(event, data)
