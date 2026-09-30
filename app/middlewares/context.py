from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.config import Settings
from app.db.session import Database


class AppContextMiddleware(BaseMiddleware):
    def __init__(self, settings: Settings, db: Database) -> None:
        self.settings = settings
        self.db = db

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        data["settings"] = self.settings
        data["db"] = self.db
        return await handler(event, data)
