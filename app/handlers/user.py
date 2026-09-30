from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.config import Settings
from app.db.base import Recommendation
from app.db.repositories import create_recommendation, upsert_user
from app.db.session import Database
from app.keyboards.user import (
    cancel_keyboard,
    confirm_recommendation_keyboard,
    main_menu_keyboard,
    skip_photo_keyboard,
    subscription_keyboard,
)
from app.services.admin_notify import send_recommendation_to_admins
from app.services.formatting import start_text, subscription_required_text
from app.services.subscription import is_subscribed
from app.states import RecommendationForm

logger = logging.getLogger(__name__)
router = Router(name="user")


async def show_subscription_gate(message: Message, settings: Settings) -> None:
    await message.answer(
        subscription_required_text(settings.channel_username),
        reply_markup=subscription_keyboard(settings.channel_url),
        disable_web_page_preview=True,
    )


async def user_has_access(message: Message, settings: Settings) -> bool:
    return await is_subscribed(message.bot, settings, message.from_user.id)


@router.message(Command("start"))
async def cmd_start(message: Message, settings: Settings, db: Database, state: FSMContext) -> None:
    await state.clear()
    async with db.session_factory() as session:
        await upsert_user(session, message.from_user)

    if not await user_has_access(message, settings):
        await show_subscription_gate(message, settings)
        return

    await message.answer(start_text(), reply_markup=main_menu_keyboard(), disable_web_page_preview=True)


@router.callback_query(F.data == "subscription:check")
async def check_subscription(callback: CallbackQuery, settings: Settings) -> None:
    if not await is_subscribed(callback.bot, settings, callback.from_user.id):
        await callback.answer("❌ Hali kanalga obuna bo‘lmagansiz.", show_alert=True)
        return

    await callback.answer("✅ Obuna tasdiqlandi!")
    if callback.message:
        await callback.message.edit_text(
            start_text(),
            reply_markup=main_menu_keyboard(),
            disable_web_page_preview=True,
        )


@router.callback_query(F.data == "recommendation:start")
async def recommendation_start(callback: CallbackQuery, settings: Settings, state: FSMContext) -> None:
    if not await is_subscribed(callback.bot, settings, callback.from_user.id):
        await callback.answer("Avval kanalga obuna bo‘ling.", show_alert=True)
        if callback.message:
            await callback.message.answer(
                subscription_required_text(settings.channel_username),
                reply_markup=subscription_keyboard(settings.channel_url),
            )
        return

    await state.clear()
    await state.set_state(RecommendationForm.waiting_title)
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            "📖 <b>1/4 — Kitob nomi</b>\n\n"
            "Tavsiya qilmoqchi bo‘lgan kitobingiz nomini yuboring.",
            reply_markup=cancel_keyboard(),
        )


@router.callback_query(F.data == "recommendation:cancel")
async def recommendation_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer("Bekor qilindi.")
    if callback.message:
        await callback.message.answer(
            "❌ Tavsiya yuborish bekor qilindi.\n\nQuyidan qaytadan boshlashingiz mumkin:",
            reply_markup=main_menu_keyboard(),
        )


@router.message(RecommendationForm.waiting_title)
async def recommendation_title(message: Message, settings: Settings, state: FSMContext) -> None:
    if not await user_has_access(message, settings):
        await show_subscription_gate(message, settings)
        return
    if not message.text:
        await message.answer("📖 Iltimos, kitob nomini matn ko‘rinishida yuboring.", reply_markup=cancel_keyboard())
        return
    title = message.text.strip()
    if not 2 <= len(title) <= 200:
        await message.answer("⚠️ Kitob nomi 2–200 belgidan iborat bo‘lsin.", reply_markup=cancel_keyboard())
        return
    await state.update_data(title=title)
    await state.set_state(RecommendationForm.waiting_author)
    await message.answer(
        "✍️ <b>2/4 — Muallif</b>\n\nKitob muallifining ismini yuboring.",
        reply_markup=cancel_keyboard(),
    )


@router.message(RecommendationForm.waiting_author)
async def recommendation_author(message: Message, settings: Settings, state: FSMContext) -> None:
    if not await user_has_access(message, settings):
        await show_subscription_gate(message, settings)
        return
    if not message.text:
        await message.answer("✍️ Iltimos, muallif nomini matn ko‘rinishida yuboring.", reply_markup=cancel_keyboard())
        return
    author = message.text.strip()
    if not 2 <= len(author) <= 200:
        await message.answer("⚠️ Muallif nomi 2–200 belgidan iborat bo‘lsin.", reply_markup=cancel_keyboard())
        return
    await state.update_data(author=author)
    await state.set_state(RecommendationForm.waiting_reason)
    await message.answer(
        "💭 <b>3/4 — Nega tavsiya qilasiz?</b>\n\n"
        "Kitob sizga nimasi bilan yoqqanini yoki boshqalarga nega tavsiya qilishingizni yozing.\n\n"
        "<i>Masalan: Juda ta’sirli asar. Inson hayoti va tanlovlari haqida chuqur o‘ylashga undaydi.</i>",
        reply_markup=cancel_keyboard(),
    )


@router.message(RecommendationForm.waiting_reason)
async def recommendation_reason(message: Message, settings: Settings, state: FSMContext) -> None:
    if not await user_has_access(message, settings):
        await show_subscription_gate(message, settings)
        return
    if not message.text:
        await message.answer("💭 Fikringizni matn ko‘rinishida yuboring.", reply_markup=cancel_keyboard())
        return
    reason = message.text.strip()
    if not 10 <= len(reason) <= 900:
        await message.answer("⚠️ Tavsiya matni 10–900 belgidan iborat bo‘lsin.", reply_markup=cancel_keyboard())
        return
    await state.update_data(reason=reason)
    await state.set_state(RecommendationForm.waiting_photo)
    await message.answer(
        "🖼 <b>4/4 — Kitob rasmi</b>\n\n"
        "Kitob muqovasi rasmini yuboring yoki rasmsiz davom eting.",
        reply_markup=skip_photo_keyboard(),
    )


@router.message(RecommendationForm.waiting_photo, F.photo)
async def recommendation_photo(message: Message, settings: Settings, state: FSMContext) -> None:
    if not await user_has_access(message, settings):
        await show_subscription_gate(message, settings)
        return
    photo = message.photo[-1]
    await state.update_data(photo_file_id=photo.file_id)
    await send_preview(message, state)


@router.callback_query(RecommendationForm.waiting_photo, F.data == "recommendation:skip_photo")
async def recommendation_skip_photo(callback: CallbackQuery, settings: Settings, state: FSMContext) -> None:
    if not await is_subscribed(callback.bot, settings, callback.from_user.id):
        await callback.answer("Avval kanalga obuna bo‘ling.", show_alert=True)
        return
    await state.update_data(photo_file_id=None)
    await callback.answer()
    if callback.message:
        await send_preview(callback.message, state)


async def send_preview(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    title = data["title"]
    author = data["author"]
    reason = data["reason"]
    preview = (
        "📋 <b>Tavsiyangiz tayyor</b>\n\n"
        f"📖 <b>Kitob:</b> {title}\n"
        f"✍️ <b>Muallif:</b> {author}\n\n"
        f"💭 <b>Fikringiz:</b>\n{reason}\n\n"
        "Hammasi to‘g‘rimi? Admin ko‘rib chiqqandan so‘ng ma’qullansa kanalga joylanadi."
    )
    if data.get("photo_file_id"):
        await message.answer_photo(
            photo=data["photo_file_id"],
            caption=preview,
            reply_markup=confirm_recommendation_keyboard(),
        )
    else:
        await message.answer(preview, reply_markup=confirm_recommendation_keyboard())


@router.callback_query(RecommendationForm.waiting_photo, F.data == "recommendation:submit")
async def recommendation_submit(
    callback: CallbackQuery,
    settings: Settings,
    db: Database,
    state: FSMContext,
) -> None:
    if not await is_subscribed(callback.bot, settings, callback.from_user.id):
        await callback.answer("Avval kanalga obuna bo‘ling.", show_alert=True)
        return

    data = await state.get_data()
    required = {"title", "author", "reason"}
    if not required.issubset(data):
        await state.clear()
        await callback.answer("Sessiya tugagan. Qaytadan boshlang.", show_alert=True)
        if callback.message:
            await callback.message.answer("📚 Qaytadan boshlang:", reply_markup=main_menu_keyboard())
        return

    await callback.answer("⏳ Tavsiyangiz yuborilmoqda...")
    async with db.session_factory() as session:
        user = await upsert_user(session, callback.from_user)
        recommendation = await create_recommendation(
            session,
            user_id=user.id,
            title=data["title"],
            author=data["author"],
            reason=data["reason"],
            photo_file_id=data.get("photo_file_id"),
        )
        admin_message_ids = await send_recommendation_to_admins(
            callback.bot,
            settings.admin_ids,
            recommendation,
        )
        if admin_message_ids:
            recommendation.admin_message_id = admin_message_ids[0]
            await session.commit()

    await state.clear()
    if callback.message:
        await callback.message.answer(
            "✅ <b>Tavsiyangiz qabul qilindi!</b>\n\n"
            "Avval admin ko‘rib chiqadi. Ma’qullansa, kanalga joylanadi.\n\n"
            f"🆔 Tavsiya ID: <code>#{recommendation.id}</code>",
            reply_markup=main_menu_keyboard(),
        )


@router.message(StateFilter(None))
async def fallback_message(message: Message, settings: Settings) -> None:
    if not await user_has_access(message, settings):
        await show_subscription_gate(message, settings)
        return
    await message.answer(start_text(), reply_markup=main_menu_keyboard())
