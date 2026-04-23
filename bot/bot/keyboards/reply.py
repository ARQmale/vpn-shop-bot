"""Reply keyboards — main menu."""

from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from bot.i18n import Translator


def main_menu(translator: Translator, *, is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Build the persistent main menu keyboard."""
    rows: list[list[KeyboardButton]] = [
        [
            KeyboardButton(text=translator("menu.buy")),
            KeyboardButton(text=translator("menu.my_subs")),
        ],
        [
            KeyboardButton(text=translator("menu.help")),
            KeyboardButton(text=translator("menu.language")),
        ],
    ]
    if is_admin:
        rows.append([KeyboardButton(text=translator("menu.admin"))])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
