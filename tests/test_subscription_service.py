from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from bot.config import Settings
from bot.database.models import PaymentStatus
from bot.database.repository import (
    PaymentRepository,
    SubscriptionRepository,
    UserRepository,
)
from bot.services.cryptobot import Invoice
from bot.services.subscription import SubscriptionService

pytestmark = pytest.mark.asyncio


def _invoice(invoice_id: int = 1, status: str = "active") -> Invoice:
    return Invoice(
        invoice_id=invoice_id,
        status=status,
        asset="USDT",
        amount=Decimal("5.00"),
        pay_url="https://example/pay",
        bot_invoice_url="https://example/bot",
        mini_app_invoice_url="https://example/miniapp",
        web_app_invoice_url=None,
        payload="xyz",
        created_at=datetime.now(UTC),
        paid_at=datetime.now(UTC) if status == "paid" else None,
    )


def _fake_service(
    settings: Settings,
    *,
    create_invoice_result: Invoice | None = None,
    get_invoice_result: Invoice | None = None,
) -> SubscriptionService:
    crypto = MagicMock()
    crypto.create_invoice = AsyncMock(return_value=create_invoice_result or _invoice())
    crypto.get_invoice = AsyncMock(return_value=get_invoice_result)

    channel = MagicMock()
    channel.create_one_time_invite = AsyncMock(return_value="https://t.me/+invite")
    channel.remove_member = AsyncMock(return_value=True)

    return SubscriptionService(settings=settings, crypto=crypto, channel=channel)


async def _bootstrap_user(session, user_id: int = 77) -> None:
    await UserRepository(session).upsert(
        user_id, username=None, first_name="x", language_code=None
    )


async def test_create_checkout_persists_pending_payment(session, settings) -> None:
    await _bootstrap_user(session)
    service = _fake_service(settings, create_invoice_result=_invoice(invoice_id=100))

    result = await service.create_checkout(
        session, user_id=77, plan=settings.plan_by_id("1m"), asset="USDT"
    )
    assert result.payment.status == PaymentStatus.pending
    assert result.payment.invoice_id == 100

    fetched = await PaymentRepository(session).get_by_invoice(100)
    assert fetched is not None
    assert fetched.user_id == 77


async def test_create_checkout_rejects_unknown_plan(session, settings) -> None:
    from bot.config import Plan

    await _bootstrap_user(session)
    service = _fake_service(settings)
    ghost = Plan(id="nope", title="Ghost", days=1, price=Decimal("1"))
    with pytest.raises(ValueError):
        await service.create_checkout(session, user_id=77, plan=ghost, asset="USDT")


async def test_create_checkout_rejects_unsupported_asset(session, settings) -> None:
    await _bootstrap_user(session)
    service = _fake_service(settings)
    with pytest.raises(ValueError):
        await service.create_checkout(
            session, user_id=77, plan=settings.plan_by_id("1m"), asset="BTC"
        )


async def test_activate_creates_subscription_and_invite_link(session, settings) -> None:
    await _bootstrap_user(session)
    service = _fake_service(settings, create_invoice_result=_invoice(invoice_id=200))
    await service.create_checkout(session, user_id=77, plan=settings.plan_by_id("1m"), asset="USDT")

    result = await service.activate_paid_invoice(session, 200)
    assert result is not None
    assert not result.was_extension
    assert result.invite_link == "https://t.me/+invite"
    assert result.payment.status == PaymentStatus.paid
    service.channel.create_one_time_invite.assert_awaited_once()


async def test_activate_is_idempotent(session, settings) -> None:
    await _bootstrap_user(session)
    service = _fake_service(settings, create_invoice_result=_invoice(invoice_id=300))
    await service.create_checkout(session, user_id=77, plan=settings.plan_by_id("1m"), asset="USDT")

    first = await service.activate_paid_invoice(session, 300)
    assert first is not None
    second = await service.activate_paid_invoice(session, 300)
    assert second is None


async def test_activate_extension_skips_invite_link(session, settings) -> None:
    await _bootstrap_user(session)
    service = _fake_service(settings, create_invoice_result=_invoice(invoice_id=400))

    await service.create_checkout(session, user_id=77, plan=settings.plan_by_id("1m"), asset="USDT")
    first = await service.activate_paid_invoice(session, 400)
    assert first is not None and not first.was_extension

    payments = PaymentRepository(session)
    await payments.create_pending(
        user_id=77, plan_id="3m", asset="USDT",
        amount=Decimal("13.00"), invoice_id=401, payload="next",
    )
    service.channel.create_one_time_invite.reset_mock()

    second = await service.activate_paid_invoice(session, 401)
    assert second is not None
    assert second.was_extension
    assert second.invite_link is None
    service.channel.create_one_time_invite.assert_not_awaited()


async def test_reconcile_marks_expired(session, settings) -> None:
    await _bootstrap_user(session)
    expired = _invoice(invoice_id=500, status="expired")
    service = _fake_service(
        settings,
        create_invoice_result=_invoice(invoice_id=500),
        get_invoice_result=expired,
    )
    await service.create_checkout(session, user_id=77, plan=settings.plan_by_id("1m"), asset="USDT")

    result = await service.reconcile_invoice(session, 500)
    assert result is None

    payment = await PaymentRepository(session).get_by_invoice(500)
    assert payment is not None
    assert payment.status == PaymentStatus.expired
    assert await SubscriptionRepository(session).get_for_user(77) is None
