"""Per-OS instructions shown in the Help flow."""

from __future__ import annotations

from shared.enums import Locale

_RU: dict[str, str] = {
    "android": (
        "<b>Android</b>\n"
        "1. Установи v2rayNG или Hiddify из Google Play.\n"
        "2. Скопируй VLESS-ссылку из «Мои подписки».\n"
        "3. В клиенте нажми «+» → Import from clipboard."
    ),
    "ios": (
        "<b>iOS</b>\n"
        "1. Установи FoXray или Happ из App Store.\n"
        "2. Скопируй VLESS-ссылку.\n"
        "3. В клиенте открой профили → Import from clipboard."
    ),
    "windows": (
        "<b>Windows</b>\n"
        "1. Установи Hiddify Desktop.\n"
        "2. Скопируй VLESS-ссылку.\n"
        "3. Импортируй из буфера обмена и включи профиль."
    ),
    "macos": (
        "<b>macOS</b>\n"
        "1. Установи FoXray или Hiddify.\n"
        "2. Скопируй VLESS-ссылку.\n"
        "3. Импортируй профиль из буфера обмена."
    ),
}

_EN: dict[str, str] = {
    "android": (
        "<b>Android</b>\n"
        "1. Install v2rayNG or Hiddify from Google Play.\n"
        "2. Copy the VLESS link from My subscriptions.\n"
        "3. In the client tap + → Import from clipboard."
    ),
    "ios": (
        "<b>iOS</b>\n"
        "1. Install FoXray or Happ from App Store.\n"
        "2. Copy the VLESS link.\n"
        "3. In the client open profiles → Import from clipboard."
    ),
    "windows": (
        "<b>Windows</b>\n"
        "1. Install Hiddify Desktop.\n"
        "2. Copy the VLESS link.\n"
        "3. Import from clipboard and enable the profile."
    ),
    "macos": (
        "<b>macOS</b>\n"
        "1. Install FoXray or Hiddify.\n"
        "2. Copy the VLESS link.\n"
        "3. Import the profile from clipboard."
    ),
}

_CATALOG: dict[Locale, dict[str, str]] = {Locale.RU: _RU, Locale.EN: _EN}

SUPPORTED_OS: tuple[str, ...] = ("android", "ios", "windows", "macos")


def instructions_for(os_name: str, locale: Locale) -> str:
    """Return help text for an OS in the given locale, with a safe fallback."""
    catalog = _CATALOG.get(locale, _CATALOG[Locale.RU])
    return catalog.get(os_name) or _CATALOG[Locale.RU].get(os_name, "")
