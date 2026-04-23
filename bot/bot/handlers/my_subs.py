"""My subscriptions view + per-subscription actions."""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from shared.schemas import SubscriptionRenew

from bot.api_client import BackendClient
from bot.api_client.errors import BackendError, NotFoundError
from bot.i18n import Translator
from bot.keyboards.inline import os_keyboard, subscription_actions

logger = logging.getLogger(__name__)

router = Router(name="my_subs")


@router.message(F.text.in_({"Мои подписки", "My subscriptions", "/subs"}))
async def show_subscriptions(
    message: Message,
    client: BackendClient,
    translator: Translator,
) -> None:
    if message.from_user is None:
        return
    try:
        subs = await client.user_subscriptions(message.from_user.id)
    except BackendError:
        logger.exception("user_subscriptions failed")
        await message.answer(translator("common.error"))
        return
    if not subs:
        await message.answer(translator("subs.empty"))
        return
    for sub in subs:
        text = translator(
            "subs.item",
            id=sub.id,
            status=sub.status.value,
            expires_at=sub.expires_at.strftime("%Y-%m-%d %H:%M"),
        )
        await message.answer(text, reply_markup=subscription_actions(sub, translator))


@router.callback_query(F.data.startswith("sub:link:"))
async def show_link(
    callback: CallbackQuery,
    client: BackendClient,
    translator: Translator,
) -> None:
    if callback.data is None:
        return
    try:
        sub_id = int(callback.data.rsplit(":", maxsplit=1)[-1])
    except ValueError:
        await callback.answer()
        return
    try:
        sub = await client.get_subscription(sub_id)
    except NotFoundError:
        await callback.answer(translator("common.not_found"), show_alert=True)
        return
    except BackendError:
        await callback.answer(translator("common.error"), show_alert=True)
        return
    if callback.message is not None and hasattr(callback.message, "answer"):
        await callback.message.answer(translator("subs.link", link=sub.vless_link))
    await callback.answer()


@router.callback_query(F.data.startswith("sub:help:"))
async def show_instructions(callback: CallbackQuery, translator: Translator) -> None:
    if callback.message is not None and hasattr(callback.message, "answer"):
        await callback.message.answer(
            translator("help.prompt"), reply_markup=os_keyboard(translator)
        )
    await callback.answer()


@router.callback_query(F.data.startswith("sub:renew:"))
async def renew_subscription(
    callback: CallbackQuery,
    client: BackendClient,
    translator: Translator,
) -> None:
    if callback.data is None:
        return
    try:
        sub_id = int(callback.data.rsplit(":", maxsplit=1)[-1])
    except ValueError:
        await callback.answer()
        return
    try:
        sub = await client.get_subscription(sub_id)
        payment = await client.renew_subscription(sub_id, SubscriptionRenew(plan_id=sub.plan_id))
    except NotFoundError:
        await callback.answer(translator("common.not_found"), show_alert=True)
        return
    except BackendError:
        logger.exception("renew_subscription failed for id=%s", sub_id)
        await callback.answer(translator("common.error"), show_alert=True)
        return
    text = (
        translator("payment.created", url=payment.payment_url)
        if payment.payment_url
        else translator("payment.no_url")
    )
    if callback.message is not None and hasattr(callback.message, "answer"):
        await callback.message.answer(text)
    await callback.answer()
