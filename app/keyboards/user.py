from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def subscription_keyboard(channel_url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📢 Kanalga qo‘shilish", url=channel_url)
    builder.button(text="✅ Obunani tekshirish", callback_data="subscription:check")
    builder.adjust(1)
    return builder.as_markup()


def main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📖 Kitob tavsiya qilish", callback_data="recommendation:start")
    builder.adjust(1)
    return builder.as_markup()


def cancel_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Bekor qilish", callback_data="recommendation:cancel")
    return builder.as_markup()


def skip_photo_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Rasmsiz davom etish", callback_data="recommendation:skip_photo")
    builder.button(text="❌ Bekor qilish", callback_data="recommendation:cancel")
    builder.adjust(1)
    return builder.as_markup()


def confirm_recommendation_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Yuborish", callback_data="recommendation:submit")
    builder.button(text="❌ Bekor qilish", callback_data="recommendation:cancel")
    builder.adjust(1)
    return builder.as_markup()
