"""Admin-only commands."""

from __future__ import annotations

import logging
from typing import Any

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from shared.schemas import UserOut

from bot.api_client import BackendClient
from bot.api_client.errors import BackendError, UnauthorizedError
from bot.config import BotSettings
from bot.i18n import Translator

logger = logging.getLogger(__name__)

router = Router(name="admin")


class AdminStates(StatesGroup):
    broadcasting = State()


def _is_admin(user_out: UserOut | None, user_id: int, settings: BotSettings) -> bool:
    if user_out is not None and user_out.is_admin:
        return True
    return user_id in settings.bot_admin_ids


def _format_stats(stats: dict[str, Any]) -> str:
    lines = [f"<b>{key}</b>: {value}" for key, value in stats.items()]
    return "\n".join(lines) if lines else "—"


@router.message(Command("stats"))
async def admin_stats(
    message: Message,
    client: BackendClient,
    translator: Translator,
    user_out: UserOut | None,
    settings: BotSettings,
) -> None:
    if message.from_user is None:
        return
    if not _is_admin(user_out, message.from_user.id, settings):
        await message.answer(translator("admin.only"))
        return
    try:
        stats = await client.admin_stats()
    except UnauthorizedError:
        await message.answer(translator("admin.only"))
        return
    except BackendError:
        logger.exception("admin_stats failed")
        await message.answer(translator("common.error"))
        return
    await message.answer(
        translator("admin.stats_title") + "\n" + _format_stats(stats)
    )


@router.message(Command("broadcast"))
async def admin_broadcast_start(
    message: Message,
    state: FSMContext,
    translator: Translator,
    user_out: UserOut | None,
    settings: BotSettings,
) -> None:
    if message.from_user is None:
        return
    if not _is_admin(user_out, message.from_user.id, settings):
        await message.answer(translator("admin.only"))
        return
    await state.set_state(AdminStates.broadcasting)
    await message.answer(translator("admin.broadcast_prompt"))


@router.message(AdminStates.broadcasting, F.text & ~F.text.startswith("/cancel"))
async def admin_broadcast_send(
    message: Message,
    state: FSMContext,
    client: BackendClient,
    translator: Translator,
) -> None:
    text = message.text or ""
    try:
        result = await client.admin_broadcast(text)
    except UnauthorizedError:
        await message.answer(translator("admin.only"))
        await state.clear()
        return
    except BackendError:
        logger.exception("admin_broadcast failed")
        await message.answer(translator("common.error"))
        await state.clear()
        return
    count = int(result.get("count", 0))
    await state.clear()
    await message.answer(translator("admin.broadcast_sent", count=count))
