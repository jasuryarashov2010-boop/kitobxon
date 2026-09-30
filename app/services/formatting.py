from __future__ import annotations

from html import escape

from aiogram.types import User as TgUser

from app.db.base import Recommendation, User


def user_display(user: User | TgUser) -> str:
    username = getattr(user, "username", None)
    if username:
        return f"@{escape(username)}"
    return escape(getattr(user, "first_name", None) or str(getattr(user, "id", "Foydalanuvchi")))


def recommendation_summary(recommendation: Recommendation) -> str:
    return (
        "📚 <b>Yangi kitob tavsiyasi</b>\n\n"
        f"<b>📖 Kitob:</b> {escape(recommendation.title)}\n"
        f"<b>✍️ Muallif:</b> {escape(recommendation.author)}\n\n"
        f"<b>💭 Kitobxon fikri:</b>\n{escape(recommendation.reason)}\n\n"
        f"<b>👤 Tavsiya qilgan:</b> {user_display(recommendation.user)}\n"
        f"<b>🆔 Tavsiya ID:</b> <code>#{recommendation.id}</code>"
    )


def channel_post_text(recommendation: Recommendation, bot_username: str) -> str:
    return (
        "📚 <b>BUGUNGI KITOB TAVSIYASI</b>\n\n"
        f"📖 <b>{escape(recommendation.title)}</b>\n"
        f"✍️ {escape(recommendation.author)}\n\n"
        f"💭 <b>Kitobxon tavsiyasi:</b>\n{escape(recommendation.reason)}\n\n"
        "📚 Siz ham o‘qigan kitobingizni tavsiya qiling:\n"
        f"👉 <b>{escape(bot_username)}</b>"
    )


def subscription_required_text(channel_username: str) -> str:
    channel_title = escape(channel_username or "kanal")
    return (
        "📚 <b>Kitobxonlar davrasiga xush kelibsiz!</b>\n\n"
        f"Botdan foydalanishdan oldin {channel_title} kanaliga obuna bo‘ling.\n\n"
        "Obuna bo‘lgach, <b>✅ Obunani tekshirish</b> tugmasini bosing."
    )


def start_text() -> str:
    return (
        "📚 <b>Kitobxon Tavsiya Bot</b>\n\n"
        "O‘qigan kitobingizni boshqalarga ham tavsiya qiling. "
        "Siz yuborgan tavsiya avval admin tomonidan ko‘rib chiqiladi, "
        "ma’qullansa kanalimizga chiroyli ko‘rinishda joylanadi.\n\n"
        "👇 Quyidagi tugmadan foydalaning:"
    )
