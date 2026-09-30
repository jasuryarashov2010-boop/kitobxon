from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import ReactionTypeEmoji

logger = logging.getLogger(__name__)


async def add_fire_reaction(bot: Bot, chat_id: int | str, message_id: int) -> bool:
    try:
        await bot.set_message_reaction(
            chat_id=chat_id,
            message_id=message_id,
            reaction=[ReactionTypeEmoji(emoji="🔥")],
            is_big=False,
        )
        return True
    except (TelegramBadRequest, TelegramForbiddenError) as exc:
        logger.warning(
            "Could not set 🔥 reaction on chat=%s message=%s: %s",
            chat_id,
            message_id,
            exc,
        )
        return False
