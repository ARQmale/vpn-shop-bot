"""/start and language-switch handlers."""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from shared.enums import Locale
from shared.schemas import UserOut, UserUpsert

from bot.api_client import BackendClient
from bot.api_client.errors import BackendError
from bot.config import BotSettings
from bot.i18n import Translator, translator_for
from bot.keyboards.inline import language_keyboard
from bot.keyboards.reply import main_menu

logger = logging.getLogger(__name__)

router = Router(name="start")


def _is_admin(user_out: UserOut | None, user_id: int, settings: BotSettings) -> bool:
    if user_out is not None and user_out.is_admin:
        return True
    return user_id in settings.bot_admin_ids


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    translator: Translator,
    user_out: UserOut | None,
    settings: BotSettings,
) -> None:
    if message.from_user is None:
        return
    name = message.from_user.first_name or message.from_user.username or "friend"
    is_admin = _is_admin(user_out, message.from_user.id, settings)
    await message.answer(
        translator("start.greeting", name=name),
        reply_markup=main_menu(translator, is_admin=is_admin),
    )


@router.message(F.text.in_({"🌐", "Язык", "Language"}))
async def show_language(message: Message, translator: Translator) -> None:
    await message.answer(translator("language.prompt"), reply_markup=language_keyboard())


@router.callback_query(F.data.startswith("lang:set:"))
async def set_language(
    callback: CallbackQuery,
    state: FSMContext,
    client: BackendClient,
    user_out: UserOut | None,
    settings: BotSettings,
) -> None:
    if callback.data is None or callback.from_user is None:
        return
    raw = callback.data.rsplit(":", maxsplit=1)[-1]
    try:
        locale = Locale(raw)
    except ValueError:
        await callback.answer("bad locale", show_alert=False)
        return
    # Persist via upsert with patched language_code so backend can store it.
    dto = UserUpsert(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
        last_name=callback.from_user.last_name,
        language_code=locale.value,
    )
    try:
        user_out = await client.upsert_user(dto)
    except BackendError:
        logger.warning("failed to persist locale preference for %s", callback.from_user.id)
    translator = translator_for(locale)
    await state.clear()
    await callback.answer(translator("language.changed"))
    is_admin = _is_admin(user_out, callback.from_user.id, settings)
    if callback.message is not None and hasattr(callback.message, "answer"):
        await callback.message.answer(
            translator("language.changed"),
            reply_markup=main_menu(translator, is_admin=is_admin),
        )
