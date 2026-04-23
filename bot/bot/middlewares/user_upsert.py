"""Middleware that upserts the Telegram user into backend on every event."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
from shared.enums import Locale
from shared.schemas import UserOut, UserUpsert

from bot.api_client import BackendClient
from bot.api_client.errors import BackendError
from bot.i18n import DEFAULT_LOCALE, Translator, detect_locale, translator_for

logger = logging.getLogger(__name__)


class UserUpsertMiddleware(BaseMiddleware):
    """Attach ``user_out``, ``locale`` and ``translator`` to handler data.

    The middleware sends ``POST /users`` on every event. If the backend is
    unreachable we still allow the update to be handled with default locale
    so that /help or admin debug commands can work.
    """

    def __init__(self, client: BackendClient) -> None:
        self._client = client

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user: User | None = data.get("event_from_user")
        user_out: UserOut | None = None
        locale: Locale = DEFAULT_LOCALE

        if user is not None and not user.is_bot:
            locale = detect_locale(user.language_code)
            dto = UserUpsert(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                language_code=user.language_code,
            )
            try:
                user_out = await self._client.upsert_user(dto)
                locale = user_out.locale
            except BackendError:
                logger.exception("upsert_user failed for telegram_id=%s", user.id)

        translator: Translator = translator_for(locale)
        data["locale"] = locale
        data["translator"] = translator
        data["user_out"] = user_out
        return await handler(event, data)
