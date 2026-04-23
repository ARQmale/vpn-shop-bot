"""Tiny dict-based i18n helper.

We intentionally avoid a heavy runtime like Fluent/gettext for the MVP: the
bot only needs a couple dozen strings in ru/en and the dictionary below is
straightforward to review and lint.
"""

from __future__ import annotations

from collections.abc import Mapping

from shared.enums import Locale

DEFAULT_LOCALE: Locale = Locale.RU

_Strings = Mapping[str, str]

_RU: _Strings = {
    "menu.buy": "Купить подписку",
    "menu.my_subs": "Мои подписки",
    "menu.help": "Помощь",
    "menu.language": "Язык",
    "menu.admin": "Админ",
    "start.greeting": (
        "Привет, {name}! Это бот для покупки VPN-подписок.\n"
        "Выбери действие в меню ниже."
    ),
    "help.prompt": "Выбери операционную систему, чтобы получить инструкцию.",
    "help.os.android": "Android",
    "help.os.ios": "iOS",
    "help.os.windows": "Windows",
    "help.os.macos": "macOS",
    "language.prompt": "Выбери язык интерфейса.",
    "language.changed": "Язык переключён на русский.",
    "plans.title": "Доступные тарифы:",
    "plans.empty": "Тарифы пока не настроены. Попробуй позже.",
    "plans.button": "{name} — {price} {currency}",
    "plans.details": (
        "<b>{name}</b>\n"
        "Длительность: {duration_days} дн.\n"
        "Трафик: {traffic}\n"
        "Цена: {price} {currency}\n\n"
        "Выбери способ оплаты:"
    ),
    "plans.traffic_unlimited": "безлимит",
    "plans.traffic_gb": "{gb} ГБ",
    "provider.yookassa": "YooKassa",
    "provider.cryptobot": "CryptoBot",
    "provider.telegram_stars": "Telegram Stars",
    "payment.created": (
        "Платёж создан. Оплати по ссылке ниже и вернись в бот:\n{url}"
    ),
    "payment.no_url": "Платёж создан, но ссылка ещё не готова. Попробуй позже.",
    "subs.empty": "У тебя пока нет активных подписок.",
    "subs.item": (
        "<b>Подписка #{id}</b>\n"
        "Статус: {status}\n"
        "Действует до: {expires_at}\n"
    ),
    "subs.link_button": "Показать ссылку",
    "subs.instruction_button": "Инструкция",
    "subs.renew_button": "Продлить",
    "subs.link": "<code>{link}</code>",
    "common.back": "Назад",
    "common.cancel": "Отмена",
    "common.cancelled": "Отменено.",
    "common.error": "Произошла ошибка, попробуй позже.",
    "common.not_found": "Не найдено.",
    "admin.only": "Команда доступна только администраторам.",
    "admin.stats_title": "Статистика:",
    "admin.broadcast_prompt": "Отправь текст рассылки или /cancel.",
    "admin.broadcast_sent": "Рассылка отправлена: {count} получателей.",
}

_EN: _Strings = {
    "menu.buy": "Buy subscription",
    "menu.my_subs": "My subscriptions",
    "menu.help": "Help",
    "menu.language": "Language",
    "menu.admin": "Admin",
    "start.greeting": (
        "Hi, {name}! This bot sells VPN subscriptions.\n"
        "Pick an action from the menu below."
    ),
    "help.prompt": "Choose your operating system to get instructions.",
    "help.os.android": "Android",
    "help.os.ios": "iOS",
    "help.os.windows": "Windows",
    "help.os.macos": "macOS",
    "language.prompt": "Choose interface language.",
    "language.changed": "Language switched to English.",
    "plans.title": "Available plans:",
    "plans.empty": "No plans configured yet. Try again later.",
    "plans.button": "{name} — {price} {currency}",
    "plans.details": (
        "<b>{name}</b>\n"
        "Duration: {duration_days} days\n"
        "Traffic: {traffic}\n"
        "Price: {price} {currency}\n\n"
        "Pick a payment method:"
    ),
    "plans.traffic_unlimited": "unlimited",
    "plans.traffic_gb": "{gb} GB",
    "provider.yookassa": "YooKassa",
    "provider.cryptobot": "CryptoBot",
    "provider.telegram_stars": "Telegram Stars",
    "payment.created": (
        "Payment created. Pay via the link below and come back:\n{url}"
    ),
    "payment.no_url": "Payment created but no link yet. Try again later.",
    "subs.empty": "You have no active subscriptions yet.",
    "subs.item": (
        "<b>Subscription #{id}</b>\n"
        "Status: {status}\n"
        "Valid until: {expires_at}\n"
    ),
    "subs.link_button": "Show link",
    "subs.instruction_button": "Instructions",
    "subs.renew_button": "Renew",
    "subs.link": "<code>{link}</code>",
    "common.back": "Back",
    "common.cancel": "Cancel",
    "common.cancelled": "Cancelled.",
    "common.error": "Something went wrong, try again later.",
    "common.not_found": "Not found.",
    "admin.only": "Admin-only command.",
    "admin.stats_title": "Stats:",
    "admin.broadcast_prompt": "Send broadcast text or /cancel.",
    "admin.broadcast_sent": "Broadcast sent to {count} recipients.",
}

_CATALOG: dict[Locale, _Strings] = {
    Locale.RU: _RU,
    Locale.EN: _EN,
}


def detect_locale(language_code: str | None) -> Locale:
    """Map a Telegram ``language_code`` to a supported :class:`Locale`.

    Russian/Ukrainian/Belarusian users get ``ru``; everyone else gets ``en``.
    """
    if not language_code:
        return DEFAULT_LOCALE
    code = language_code.lower().split("-")[0]
    if code in {"ru", "uk", "be", "kk"}:
        return Locale.RU
    return Locale.EN


class Translator:
    """Callable wrapper that resolves keys into a concrete locale."""

    def __init__(self, locale: Locale) -> None:
        self.locale = locale

    def __call__(self, key: str, /, **kwargs: object) -> str:
        catalog = _CATALOG.get(self.locale, _CATALOG[DEFAULT_LOCALE])
        template = catalog.get(key) or _CATALOG[DEFAULT_LOCALE].get(key)
        if template is None:
            return key
        if not kwargs:
            return template
        return template.format(**kwargs)


def translator_for(locale: Locale) -> Translator:
    return Translator(locale)
