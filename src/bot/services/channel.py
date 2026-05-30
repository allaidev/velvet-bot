from __future__ import annotations

from datetime import UTC, datetime, timedelta

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from ..logger import log


class ChannelService:
    """Wraps the Telegram API calls related to gating channel access."""

    def __init__(self, bot: Bot, channel_id: int) -> None:
        self.bot = bot
        self.channel_id = channel_id

    async def create_one_time_invite(
        self,
        *,
        expire_minutes: int = 60,
        name: str | None = None,
    ) -> str:
        expire_date = datetime.now(UTC) + timedelta(minutes=expire_minutes)
        link = await self.bot.create_chat_invite_link(
            chat_id=self.channel_id,
            name=name[:32] if name else None,
            expire_date=expire_date,
            member_limit=1,
            creates_join_request=False,
        )
        return link.invite_link

    async def remove_member(self, user_id: int) -> bool:
        """Ban-then-unban kicks the user without keeping them on the banlist.

        Returns ``True`` when the user was successfully removed (or wasn't a member
        to begin with), ``False`` when Telegram refused the operation — usually because
        the bot lacks the needed permissions in the channel.
        """
        try:
            await self.bot.ban_chat_member(chat_id=self.channel_id, user_id=user_id)
            await self.bot.unban_chat_member(
                chat_id=self.channel_id, user_id=user_id, only_if_banned=True
            )
            return True
        except TelegramAPIError as exc:
            log.warning("channel.kick_failed", user_id=user_id, error=str(exc))
            return False
