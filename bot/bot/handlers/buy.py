"""Buy flow: choose plan -> choose provider -> create payment."""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from shared.enums import PaymentProvider
from shared.schemas import PaymentCreate

from bot.api_client import BackendClient
from bot.api_client.errors import BackendError, NotFoundError
from bot.i18n import Translator
from bot.keyboards.inline import plans_keyboard, providers_keyboard
from bot.states.buy import BuyStates

logger = logging.getLogger(__name__)

router = Router(name="buy")


def _format_traffic(traffic_gb: int, translator: Translator) -> str:
    if traffic_gb <= 0:
        return translator("plans.traffic_unlimited")
    return translator("plans.traffic_gb", gb=traffic_gb)


@router.message(F.text.in_({"Купить подписку", "Buy subscription", "/buy"}))
async def start_buy(
    message: Message,
    state: FSMContext,
    client: BackendClient,
    translator: Translator,
) -> None:
    await state.clear()
    try:
        plans = await client.list_plans()
    except BackendError:
        logger.exception("list_plans failed")
        await message.answer(translator("common.error"))
        return
    active = [p for p in plans if p.is_active]
    if not active:
        await message.answer(translator("plans.empty"))
        return
    await state.set_state(BuyStates.choosing_plan)
    await message.answer(
        translator("plans.title"),
        reply_markup=plans_keyboard(active, translator),
    )


@router.callback_query(F.data == "buy:restart")
async def restart_buy(
    callback: CallbackQuery,
    state: FSMContext,
    client: BackendClient,
    translator: Translator,
) -> None:
    await state.clear()
    try:
        plans = await client.list_plans()
    except BackendError:
        await callback.answer(translator("common.error"), show_alert=True)
        return
    active = [p for p in plans if p.is_active]
    if not active:
        await callback.answer(translator("plans.empty"), show_alert=True)
        return
    await state.set_state(BuyStates.choosing_plan)
    if callback.message is not None and hasattr(callback.message, "edit_text"):
        await callback.message.edit_text(
            translator("plans.title"),
            reply_markup=plans_keyboard(active, translator),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("buy:plan:"))
async def choose_plan(
    callback: CallbackQuery,
    state: FSMContext,
    client: BackendClient,
    translator: Translator,
) -> None:
    if callback.data is None:
        return
    try:
        plan_id = int(callback.data.rsplit(":", maxsplit=1)[-1])
    except ValueError:
        await callback.answer()
        return
    try:
        plan = await client.get_plan(plan_id)
    except NotFoundError:
        await callback.answer(translator("common.not_found"), show_alert=True)
        return
    except BackendError:
        await callback.answer(translator("common.error"), show_alert=True)
        return
    await state.set_state(BuyStates.choosing_provider)
    await state.update_data(plan_id=plan_id)
    text = translator(
        "plans.details",
        name=plan.name,
        duration_days=plan.duration_days,
        traffic=_format_traffic(plan.traffic_gb, translator),
        price=plan.price,
        currency=plan.currency.value,
    )
    if callback.message is not None and hasattr(callback.message, "edit_text"):
        await callback.message.edit_text(
            text, reply_markup=providers_keyboard(plan_id, translator)
        )
    await callback.answer()


@router.callback_query(F.data.startswith("buy:provider:"))
async def choose_provider(
    callback: CallbackQuery,
    state: FSMContext,
    client: BackendClient,
    translator: Translator,
) -> None:
    if callback.data is None or callback.from_user is None:
        return
    parts = callback.data.split(":")
    if len(parts) != 4:
        await callback.answer()
        return
    try:
        plan_id = int(parts[2])
        provider = PaymentProvider(parts[3])
    except (ValueError, KeyError):
        await callback.answer()
        return
    dto = PaymentCreate(
        telegram_id=callback.from_user.id,
        plan_id=plan_id,
        provider=provider,
    )
    try:
        payment = await client.create_payment(dto)
    except BackendError:
        logger.exception("create_payment failed")
        await callback.answer(translator("common.error"), show_alert=True)
        return
    await state.clear()
    message_text = (
        translator("payment.created", url=payment.payment_url)
        if payment.payment_url
        else translator("payment.no_url")
    )
    if callback.message is not None and hasattr(callback.message, "edit_text"):
        await callback.message.edit_text(message_text, disable_web_page_preview=False)
    await callback.answer()


@router.callback_query(F.data == "buy:cancel")
async def cancel_buy(
    callback: CallbackQuery, state: FSMContext, translator: Translator
) -> None:
    await state.clear()
    if callback.message is not None and hasattr(callback.message, "edit_text"):
        await callback.message.edit_text(translator("common.cancelled"))
    await callback.answer()
