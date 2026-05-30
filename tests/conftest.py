from __future__ import annotations

import json
import os
from collections.abc import AsyncIterator
from decimal import Decimal
from typing import Any

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

# Environment variables must be set before pydantic_settings reads the env file.
os.environ.setdefault("BOT_TOKEN", "123:test-token-value")
os.environ.setdefault("CHANNEL_ID", "-1001234567890")
os.environ.setdefault("ADMIN_IDS", "111,222")
os.environ.setdefault("CRYPTO_PAY_TOKEN", "test-crypto-token-value")
os.environ.setdefault("CRYPTO_PAY_BASE_URL", "https://testnet-pay.crypt.bot")
os.environ.setdefault("CRYPTO_PAY_ASSETS", "USDT,TON")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault(
    "SUBSCRIPTION_PLANS",
    json.dumps(
        [
            {"id": "1m", "title": "1 месяц", "days": 30, "price": "5.00"},
            {"id": "3m", "title": "3 месяца", "days": 90, "price": "13.00"},
        ]
    ),
)
os.environ.setdefault("REMINDER_DAYS", "3,1")
os.environ.setdefault("WELCOME_IMAGE", "")
os.environ.setdefault("LOG_LEVEL", "WARNING")
os.environ.setdefault("WEBHOOK_ENABLED", "false")

from bot.config import Settings, load_settings
from bot.database import create_engine_and_session, dispose_engine
from bot.database.session import open_session


@pytest.fixture(scope="session")
def settings() -> Settings:
    load_settings.cache_clear()
    return load_settings()


@pytest_asyncio.fixture()
async def session_factory() -> AsyncIterator[Any]:
    engine, factory = await create_engine_and_session(
        "sqlite+aiosqlite:///:memory:", create_tables=True
    )
    try:
        yield factory
    finally:
        await dispose_engine(engine)


@pytest_asyncio.fixture()
async def session(session_factory) -> AsyncIterator[AsyncSession]:
    async with open_session(session_factory) as s:
        yield s


@pytest.fixture()
def usdt() -> str:
    return "USDT"


@pytest.fixture()
def amount() -> Decimal:
    return Decimal("5.00")
