from __future__ import annotations

import itertools
from unittest.mock import AsyncMock, MagicMock

import pytest

from bot.middlewares.throttling import ThrottlingMiddleware

pytestmark = pytest.mark.asyncio


def _callback(user_id: int, data: str = "buy:plan_id=1m") -> MagicMock:
    call = MagicMock()
    call.from_user = MagicMock(id=user_id)
    call.data = data
    call.answer = AsyncMock()
    return call


def _clock(start: float = 0.0, step: float = 1.0):
    ticks = itertools.count(start=start, step=step)
    return lambda: next(ticks)


async def test_admins_bypass_throttling(settings) -> None:
    mw = ThrottlingMiddleware(settings, clock=_clock(step=0.0))
    handler = AsyncMock(return_value="ok")
    call = _callback(user_id=settings.admin_ids[0])
    for _ in range(20):
        assert await mw(handler, call, {}) == "ok"
    assert handler.await_count == 20


async def test_buy_quota_enforced(settings) -> None:
    mw = ThrottlingMiddleware(settings, clock=_clock())
    handler = AsyncMock(return_value="ok")
    call = _callback(user_id=5555)

    allowed = blocked = 0
    for _ in range(settings.throttle_buy_per_minute + 3):
        res = await mw(handler, call, {})
        if res == "ok":
            allowed += 1
        else:
            blocked += 1
    assert allowed == settings.throttle_buy_per_minute
    assert blocked == 3


async def test_global_flood_guard(settings) -> None:
    # Two calls 0.1 seconds apart — second should be blocked.
    times = iter([0.0, 0.1])
    mw = ThrottlingMiddleware(settings, clock=lambda: next(times))
    handler = AsyncMock(return_value="ok")
    call = _callback(user_id=12345, data="menu:action=back")

    assert await mw(handler, call, {}) == "ok"
    assert await mw(handler, call, {}) is None


async def test_non_buy_actions_not_quota_limited(settings) -> None:
    mw = ThrottlingMiddleware(settings, clock=_clock())
    handler = AsyncMock(return_value="ok")
    call = _callback(user_id=9999, data="menu:action=info")
    for _ in range(settings.throttle_buy_per_minute * 3):
        assert await mw(handler, call, {}) == "ok"
