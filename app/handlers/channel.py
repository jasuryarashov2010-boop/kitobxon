from __future__ import annotations

import logging

from aiogram import Bot, Router
from aiogram.types import Message

from app.config import Settings
from app.services.reactions import add_fire_reaction

logger = logging.getLogger(__name__)
router = Router(name="channel")


@router.channel_post()
async def channel_post_reaction(message: Message, bot: Bot, settings: Settings) -> None:
    # Only touch the configured channel. The bot can be an admin of several channels.
    if str(message.chat.id) != str(settings.channel_id):
        return
    await add_fire_reaction(bot, message.chat.id, message.message_id)


@router.edited_channel_post()
async def edited_channel_post_reaction(message: Message, bot: Bot, settings: Settings) -> None:
    if str(message.chat.id) != str(settings.channel_id):
        return
    await add_fire_reaction(bot, message.chat.id, message.message_id)
