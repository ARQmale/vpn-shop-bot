"""Inline keyboard builders."""

from __future__ import annotations

from collections.abc import Iterable

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from shared.enums import Locale, PaymentProvider
from shared.schemas import PlanOut, SubscriptionOut

from bot.i18n import Translator
from bot.utils.vpn_instructions import SUPPORTED_OS


def plans_keyboard(plans: Iterable[PlanOut], translator: Translator) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for plan in plans:
        label = translator(
            "plans.button",
            name=plan.name,
            price=plan.price,
            currency=plan.currency.value,
        )
        rows.append(
            [InlineKeyboardButton(text=label, callback_data=f"buy:plan:{plan.id}")]
        )
    rows.append(
        [InlineKeyboardButton(text=translator("common.cancel"), callback_data="buy:cancel")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def providers_keyboard(plan_id: int, translator: Translator) -> InlineKeyboardMarkup:
    providers: list[PaymentProvider] = [
        PaymentProvider.YOOKASSA,
        PaymentProvider.CRYPTOBOT,
        PaymentProvider.TELEGRAM_STARS,
    ]
    rows: list[list[InlineKeyboardButton]] = []
    for provider in providers:
        rows.append(
            [
                InlineKeyboardButton(
                    text=translator(f"provider.{provider.value}"),
                    callback_data=f"buy:provider:{plan_id}:{provider.value}",
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text=translator("common.back"), callback_data="buy:restart"
            ),
            InlineKeyboardButton(
                text=translator("common.cancel"), callback_data="buy:cancel"
            ),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def subscription_actions(
    subscription: SubscriptionOut, translator: Translator
) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=translator("subs.link_button"),
                callback_data=f"sub:link:{subscription.id}",
            ),
            InlineKeyboardButton(
                text=translator("subs.instruction_button"),
                callback_data=f"sub:help:{subscription.id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text=translator("subs.renew_button"),
                callback_data=f"sub:renew:{subscription.id}",
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def os_keyboard(translator: Translator) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=translator(f"help.os.{os_name}"),
                callback_data=f"help:os:{os_name}",
            )
        ]
        for os_name in SUPPORTED_OS
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def language_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="Русский", callback_data=f"lang:set:{Locale.RU.value}"),
            InlineKeyboardButton(text="English", callback_data=f"lang:set:{Locale.EN.value}"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)
