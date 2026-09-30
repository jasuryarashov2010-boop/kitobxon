from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.config import Settings
from app.db.repositories import (
    claim_for_approval,
    finalize_approval,
    get_recommendation,
    pending_count,
    reject_recommendation,
    revert_publish_claim,
)
from app.db.session import Database
from app.services.admin_notify import mark_admin_message_done
from app.services.publisher import publish_recommendation

logger = logging.getLogger(__name__)
router = Router(name="admin")


def is_admin(user_id: int, settings: Settings) -> bool:
    return user_id in settings.admin_ids


@router.message(Command("admin"))
async def admin_home(message: Message, settings: Settings, db: Database) -> None:
    if not is_admin(message.from_user.id, settings):
        return
    async with db.session_factory() as session:
        count = await pending_count(session)
    await message.answer(
        "👑 <b>Admin panel</b>\n\n"
        f"📥 Kutilayotgan tavsiyalar: <b>{count}</b>\n\n"
        "Yangi tavsiyalar admin chatiga avtomatik yuboriladi."
    )


@router.callback_query(F.data.startswith("moderate:"))
async def moderate(callback: CallbackQuery, settings: Settings, db: Database) -> None:
    if not is_admin(callback.from_user.id, settings):
        await callback.answer("⛔ Bu tugma faqat admin uchun.", show_alert=True)
        return

    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("Noto‘g‘ri so‘rov.", show_alert=True)
        return

    action = parts[1]
    try:
        recommendation_id = int(parts[2])
    except ValueError:
        await callback.answer("Noto‘g‘ri tavsiya ID.", show_alert=True)
        return

    async with db.session_factory() as session:
        recommendation = await get_recommendation(session, recommendation_id)
        if recommendation is None:
            await callback.answer("Tavsiya topilmadi.", show_alert=True)
            return

        if action == "reject":
            updated = await reject_recommendation(
                session,
                recommendation_id,
                callback.from_user.id,
            )
            if updated is None:
                await callback.answer("Bu tavsiya allaqachon ko‘rib chiqilgan.", show_alert=True)
                return
            await callback.answer("❌ Tavsiya rad etildi.")
            await mark_admin_message_done(callback.message, approved=False)
            try:
                await callback.bot.send_message(
                    recommendation.user_id,
                    "❌ <b>Tavsiyangiz bu safar kanalga joylanmadi.</b>\n\n"
                    f"📖 {recommendation.title}",
                )
            except Exception:
                logger.exception("Could not notify user about rejection: %s", recommendation.user_id)
            return

        if action == "approve":
            claimed = await claim_for_approval(
                session,
                recommendation_id,
                callback.from_user.id,
            )
            if not claimed:
                await callback.answer("Bu tavsiya allaqachon ko‘rib chiqilgan.", show_alert=True)
                return

            try:
                message_id = await publish_recommendation(
                    callback.bot,
                    settings,
                    settings.channel_id,
                    recommendation,
                )
                updated = await finalize_approval(
                    session,
                    recommendation_id,
                    message_id,
                )
                if updated is None:
                    raise RuntimeError("Could not finalize approval")
            except Exception:
                logger.exception("Could not publish recommendation #%s", recommendation_id)
                await revert_publish_claim(session, recommendation_id)
                await callback.answer(
                    "⚠️ Kanalga joylashda xatolik yuz berdi. Tavsiya qayta kutish holatiga qaytarildi.",
                    show_alert=True,
                )
                return

            await callback.answer("✅ Kanalga joylandi!")
            await mark_admin_message_done(callback.message, approved=True)
            try:
                await callback.bot.send_message(
                    recommendation.user_id,
                    "✅ <b>Tavsiyangiz kanalga joylandi!</b>\n\n"
                    f"📖 {recommendation.title}\n"
                    f"🔗 <a href=\"https://t.me/{settings.channel_username.lstrip('@')}\">Kanalni ochish</a>",
                    disable_web_page_preview=True,
                )
            except Exception:
                logger.exception("Could not notify user about approval: %s", recommendation.user_id)
            return

    await callback.answer("Noma’lum amal.", show_alert=True)
