"""Help / OS-specific instructions."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from shared.enums import Locale

from bot.i18n import Translator
from bot.keyboards.inline import os_keyboard
from bot.utils.vpn_instructions import SUPPORTED_OS, instructions_for

router = Router(name="help")


@router.message(Command("help"))
@router.message(F.text.in_({"Помощь", "Help"}))
async def show_help(message: Message, translator: Translator) -> None:
    await message.answer(translator("help.prompt"), reply_markup=os_keyboard(translator))


@router.callback_query(F.data.startswith("help:os:"))
async def show_os_instructions(
    callback: CallbackQuery, translator: Translator, locale: Locale
) -> None:
    if callback.data is None:
        return
    os_name = callback.data.rsplit(":", maxsplit=1)[-1]
    if os_name not in SUPPORTED_OS:
        await callback.answer()
        return
    text = instructions_for(os_name, locale)
    if callback.message is not None and hasattr(callback.message, "edit_text"):
        await callback.message.edit_text(text)
    await callback.answer()
