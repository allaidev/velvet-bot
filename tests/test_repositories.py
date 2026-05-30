from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from bot.database.models import PaymentStatus
from bot.database.repository import (
    PaymentRepository,
    SubscriptionRepository,
    UserRepository,
)

pytestmark = pytest.mark.asyncio


async def _make_user(session, user_id: int = 42):
    return await UserRepository(session).upsert(
        user_id,
        username="alice",
        first_name="Alice",
        language_code="en",
    )


async def test_user_upsert_idempotent(session) -> None:
    repo = UserRepository(session)
    u1 = await repo.upsert(1, username="a", first_name="A", language_code="en")
    u2 = await repo.upsert(1, username="a", first_name="A", language_code="en")
    assert u1.id == u2.id
    assert await repo.count() == 1


async def test_user_upsert_updates_fields(session) -> None:
    repo = UserRepository(session)
    await repo.upsert(1, username="old", first_name="A", language_code="en")
    await repo.upsert(1, username="new", first_name="A", language_code="ru")
    user = await repo.get(1)
    assert user is not None
    assert user.username == "new"
    assert user.language_code == "ru"


async def test_subscription_create_then_extend(session) -> None:
    await _make_user(session)
    repo = SubscriptionRepository(session)

    sub, extended = await repo.upsert_extension(user_id=42, plan_id="1m", days=30)
    assert not extended
    first_until = sub.expires_at

    sub2, extended2 = await repo.upsert_extension(user_id=42, plan_id="3m", days=90)
    assert extended2
    assert sub2.id == sub.id
    assert sub2.expires_at >= first_until + timedelta(days=89)
    assert sub2.plan_id == "3m"


async def test_subscription_after_expiry_starts_fresh_window(session) -> None:
    await _make_user(session)
    repo = SubscriptionRepository(session)
    sub, _ = await repo.upsert_extension(user_id=42, plan_id="1m", days=30)
    sub.expires_at = datetime.now(UTC) - timedelta(days=2)
    await session.flush()

    sub2, extended = await repo.upsert_extension(user_id=42, plan_id="1m", days=30)
    assert not extended
    assert sub2.expires_at > datetime.now(UTC) + timedelta(days=29)


async def test_subscription_list_expiring_and_expired(session) -> None:
    await _make_user(session, 1)
    await _make_user(session, 2)
    await _make_user(session, 3)
    repo = SubscriptionRepository(session)

    s1, _ = await repo.upsert_extension(user_id=1, plan_id="1m", days=30)
    s2, _ = await repo.upsert_extension(user_id=2, plan_id="1m", days=30)
    s3, _ = await repo.upsert_extension(user_id=3, plan_id="1m", days=30)

    now = datetime.now(UTC)
    s1.expires_at = now + timedelta(days=1)
    s2.expires_at = now + timedelta(hours=12)
    s3.expires_at = now - timedelta(hours=1)
    await session.flush()

    within_three = await repo.list_expiring(3)
    assert {s.user_id for s in within_three} == {1, 2}

    expired = await repo.list_expired()
    assert {s.user_id for s in expired} == {3}


async def test_payment_create_and_mark_paid(session) -> None:
    await _make_user(session, 42)
    repo = PaymentRepository(session)
    payment = await repo.create_pending(
        user_id=42,
        plan_id="1m",
        asset="USDT",
        amount=Decimal("5.00"),
        invoice_id=9999,
        payload="abc",
    )
    assert payment.status == PaymentStatus.pending

    await repo.mark_paid(payment)
    assert payment.status == PaymentStatus.paid
    assert payment.paid_at is not None
    assert await repo.count_paid() == 1


async def test_payment_revenue_by_asset(session) -> None:
    await _make_user(session, 1)
    repo = PaymentRepository(session)
    for invoice_id, asset, amount in [
        (1, "USDT", Decimal("5")),
        (2, "USDT", Decimal("13")),
        (3, "TON", Decimal("2.5")),
    ]:
        p = await repo.create_pending(
            user_id=1, plan_id="1m", asset=asset, amount=amount,
            invoice_id=invoice_id, payload=None,
        )
        await repo.mark_paid(p)

    revenue = await repo.revenue_by_asset()
    assert revenue["USDT"] == Decimal("18")
    assert revenue["TON"] == Decimal("2.5")


async def test_notified_days_serialization(session) -> None:
    await _make_user(session)
    repo = SubscriptionRepository(session)
    sub, _ = await repo.upsert_extension(user_id=42, plan_id="1m", days=30)
    sub.mark_notified(3)
    sub.mark_notified(1)
    sub.mark_notified(3)  # duplicate ignored
    assert sub.notified_days() == {1, 3}
    assert sub.notified_at_days == "3,1"
