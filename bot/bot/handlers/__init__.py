"""Aiogram routers, one per feature."""

from __future__ import annotations

from aiogram import Router

from bot.handlers import admin, buy, common, my_subs, start
from bot.handlers import help as help_module


def build_root_router() -> Router:
    """Combine feature routers into a single parent router."""
    router = Router(name="root")
    router.include_router(start.router)
    router.include_router(buy.router)
    router.include_router(my_subs.router)
    router.include_router(help_module.router)
    router.include_router(admin.router)
    router.include_router(common.router)
    return router


__all__ = ["build_root_router"]
