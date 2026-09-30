from __future__ import annotations

from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from app.config import Settings


async def is_subscribed(bot: Bot, settings: Settings, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=settings.channel_id, user_id=user_id)
    except (TelegramBadRequest, TelegramForbiddenError):
        return False

    if member.status in {
        ChatMemberStatus.CREATOR,
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.MEMBER,
    }:
        return True
    if member.status == ChatMemberStatus.RESTRICTED:
        return bool(member.is_member)
    return False
