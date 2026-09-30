from __future__ import annotations

from aiogram import Bot

from app.config import Settings
from app.db.base import Recommendation
from app.services.formatting import channel_post_text
from app.services.reactions import add_fire_reaction


async def publish_recommendation(
    bot: Bot,
    settings: Settings,
    channel_id: int | str,
    recommendation: Recommendation,
) -> int:
    text = channel_post_text(recommendation, settings.bot_username)

    if recommendation.photo_file_id:
        message = await bot.send_photo(
            chat_id=channel_id,
            photo=recommendation.photo_file_id,
            caption=text,
        )
    else:
        message = await bot.send_message(
            chat_id=channel_id,
            text=text,
        )

    await add_fire_reaction(bot, channel_id, message.message_id)
    return message.message_id
