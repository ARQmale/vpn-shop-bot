"""Entrypoint: ``python -m bot`` starts Telegram long polling."""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.api_client import BackendClient
from bot.config import BotSettings, load_settings
from bot.handlers import build_root_router
from bot.middlewares.user_upsert import UserUpsertMiddleware

logger = logging.getLogger(__name__)


def _configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def build_dispatcher(settings: BotSettings, client: BackendClient) -> Dispatcher:
    """Assemble a :class:`Dispatcher` with routers, storage and middlewares."""
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher["client"] = client
    dispatcher["settings"] = settings

    upsert = UserUpsertMiddleware(client)
    dispatcher.message.middleware(upsert)
    dispatcher.callback_query.middleware(upsert)

    dispatcher.include_router(build_root_router())
    return dispatcher


async def _run() -> None:
    settings = load_settings()
    _configure_logging(settings.log_level)

    bot = Bot(
        token=settings.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    client = BackendClient(
        base_url=settings.backend_base_url,
        bot_token=settings.bot_api_token.get_secret_value(),
        admin_token=(
            settings.admin_api_token.get_secret_value() if settings.admin_api_token else None
        ),
        timeout=settings.backend_request_timeout,
    )
    dispatcher = build_dispatcher(settings, client)
    logger.info("Starting bot polling (env=%s)", settings.environment)
    try:
        await dispatcher.start_polling(bot)
    finally:
        await client.aclose()
        await bot.session.close()


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
