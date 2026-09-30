from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def moderation_keyboard(recommendation_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Kanalga joylash", callback_data=f"moderate:approve:{recommendation_id}")
    builder.button(text="❌ Rad etish", callback_data=f"moderate:reject:{recommendation_id}")
    builder.adjust(1)
    return builder.as_markup()
