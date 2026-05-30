from __future__ import annotations

import pytest
from pydantic import ValidationError

from bot.config import Plan, Settings


def test_settings_load(settings: Settings) -> None:
    assert settings.bot_token
    assert settings.channel_id == -1001234567890
    assert settings.admin_ids == [111, 222]
    assert settings.crypto_pay_assets == ["USDT", "TON"]
    assert settings.reminder_days == [3, 1]
    assert len(settings.subscription_plans) == 2


def test_plan_lookup(settings: Settings) -> None:
    plan = settings.plan_by_id("1m")
    assert plan is not None
    assert plan.days == 30
    assert settings.plan_by_id("unknown") is None


def test_is_admin(settings: Settings) -> None:
    assert settings.is_admin(111)
    assert not settings.is_admin(333)


def test_duplicate_plan_ids_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "SUBSCRIPTION_PLANS",
        '[{"id":"x","title":"a","days":30,"price":"1"},'
        ' {"id":"x","title":"b","days":60,"price":"2"}]',
    )
    with pytest.raises(ValidationError) as exc_info:
        Settings()  # type: ignore[call-arg]
    assert "duplicate plan id" in str(exc_info.value)


def test_plan_model_coerces_price() -> None:
    plan = Plan(id="1", title="t", days=30, price="9.99")  # type: ignore[arg-type]
    assert str(plan.price) == "9.99"
