"""Tests for the i18n helper."""

from __future__ import annotations

import pytest
from bot.i18n import DEFAULT_LOCALE, detect_locale, translator_for
from shared.enums import Locale


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        (None, Locale.RU),
        ("", Locale.RU),
        ("ru", Locale.RU),
        ("ru-RU", Locale.RU),
        ("uk", Locale.RU),
        ("be", Locale.RU),
        ("en", Locale.EN),
        ("en-US", Locale.EN),
        ("de", Locale.EN),
    ],
)
def test_detect_locale(code: str | None, expected: Locale) -> None:
    assert detect_locale(code) == expected


def test_translator_fallback_to_default() -> None:
    ru = translator_for(Locale.RU)
    en = translator_for(Locale.EN)
    assert ru("menu.buy") != en("menu.buy")
    assert DEFAULT_LOCALE == Locale.RU


def test_translator_missing_key_returns_key() -> None:
    t = translator_for(Locale.RU)
    assert t("this.key.does.not.exist") == "this.key.does.not.exist"


def test_translator_formats_kwargs() -> None:
    t = translator_for(Locale.EN)
    out = t("plans.button", name="A", price="1", currency="RUB")
    assert "A" in out and "1" in out and "RUB" in out
