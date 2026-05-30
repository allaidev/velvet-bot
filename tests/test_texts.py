from __future__ import annotations

from decimal import Decimal

from bot.texts import format_amount


def test_format_amount_integer() -> None:
    assert format_amount(Decimal("5"), "USDT") == "5 USDT"


def test_format_amount_trailing_zero_trimmed() -> None:
    assert format_amount(Decimal("5.10"), "USDT") == "5.1 USDT"


def test_format_amount_two_decimals() -> None:
    assert format_amount(Decimal("5.05"), "TON") == "5.05 TON"
