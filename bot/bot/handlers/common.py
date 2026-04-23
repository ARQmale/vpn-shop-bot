"""Miscellaneous commands and catch-alls."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.i18n import Translator

router = Router(name="common")


@router.message(Command("cancel"))
async def cmd_cancel(
    message: Message, state: FSMContext, translator: Translator
) -> None:
    await state.clear()
    await message.answer(translator("common.cancelled"))
