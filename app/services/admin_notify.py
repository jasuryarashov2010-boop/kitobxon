from __future__ import annotations

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from app.db.base import Recommendation
from app.keyboards.admin import moderation_keyboard
from app.services.formatting import recommendation_summary


async def send_recommendation_to_admins(bot: Bot, admin_ids: set[int], recommendation: Recommendation) -> list[int]:
    markup = moderation_keyboard(recommendation.id)
    summary = recommendation_summary(recommendation)
    sent_message_ids: list[int] = []

    for admin_id in admin_ids:
        try:
            if recommendation.photo_file_id:
                message = await bot.send_photo(
                    chat_id=admin_id,
                    photo=recommendation.photo_file_id,
                    caption=summary,
                    reply_markup=markup,
                )
            else:
                message = await bot.send_message(
                    chat_id=admin_id,
                    text=summary,
                    reply_markup=markup,
                )
            sent_message_ids.append(message.message_id)
        except TelegramBadRequest:
            # One blocked/deleted admin must not stop delivery to other admins.
            continue
    return sent_message_ids


async def mark_admin_message_done(message, *, approved: bool) -> None:
    status_text = "✅ <b>Kanalga joylandi</b>" if approved else "❌ <b>Rad etildi</b>"
    try:
        if message.photo:
            await message.edit_caption(caption=f"{message.caption or ''}\n\n{status_text}", reply_markup=None)
        else:
            await message.edit_text(text=f"{message.text or ''}\n\n{status_text}", reply_markup=None)
    except TelegramBadRequest:
        # The recommendation can still be successfully processed even when the old admin message
        # was already edited/deleted manually.
        return
