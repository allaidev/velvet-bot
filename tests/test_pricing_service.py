from __future__ import annotations

from decimal import Decimal

import pytest

from bot.services.pricing import PricingService

pytestmark = pytest.mark.asyncio


async def test_effective_plans_returns_defaults_without_overrides(session, settings) -> None:
    pricing = PricingService(settings)
    plans = await pricing.effective_plans(session)
    assert [p.price for p in plans] == [p.price for p in settings.subscription_plans]


async def test_set_price_overrides_for_new_invoices(session, settings) -> None:
    pricing = PricingService(settings)
    updated = await pricing.set_price(session, "1m", Decimal("7.50"))
    assert updated.price == Decimal("7.50")

    plans = {p.id: p for p in await pricing.effective_plans(session)}
    assert plans["1m"].price == Decimal("7.50")
    # other plans unaffected
    default_3m = next(p for p in settings.subscription_plans if p.id == "3m")
    assert plans["3m"].price == default_3m.price


async def test_set_price_is_upsert(session, settings) -> None:
    pricing = PricingService(settings)
    await pricing.set_price(session, "1m", Decimal("7.50"))
    await pricing.set_price(session, "1m", Decimal("9.00"))

    plan = await pricing.effective_plan(session, "1m")
    assert plan is not None
    assert plan.price == Decimal("9.00")


async def test_reset_price_falls_back_to_config(session, settings) -> None:
    pricing = PricingService(settings)
    await pricing.set_price(session, "1m", Decimal("99"))
    after_reset = await pricing.reset_price(session, "1m")

    default = settings.plan_by_id("1m")
    assert after_reset is not None
    assert default is not None
    assert after_reset.price == default.price


async def test_set_price_rejects_unknown_plan(session, settings) -> None:
    pricing = PricingService(settings)
    with pytest.raises(ValueError):
        await pricing.set_price(session, "no-such", Decimal("1"))


async def test_set_price_rejects_non_positive(session, settings) -> None:
    pricing = PricingService(settings)
    with pytest.raises(ValueError):
        await pricing.set_price(session, "1m", Decimal("0"))
    with pytest.raises(ValueError):
        await pricing.set_price(session, "1m", Decimal("-5"))


async def test_effective_plan_unknown_returns_none(session, settings) -> None:
    pricing = PricingService(settings)
    assert await pricing.effective_plan(session, "does-not-exist") is None
