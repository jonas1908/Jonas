"""
Discord 相关操作：
- 使用 Bot Token 登录
- 从指定服务器 / 频道，在指定时间范围内拉取消息
"""

from datetime import datetime, timezone
from typing import List

import discord

from .config import AppConfig
from .models import RawDiscordMessage


def _to_utc(dt: datetime) -> datetime:
    """转为 naive UTC，供 discord.py 使用。"""
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc)
    return dt.replace(tzinfo=None)


async def fetch_suggestions_for_period(
    config: AppConfig,
    start_time: datetime,
    end_time: datetime,
) -> List[RawDiscordMessage]:
    """
    从 Discord 指定频道拉取在 [start_time, end_time] 之间的消息。
    需要 Bot 具备「查看频道」「读取消息历史」权限，且已开启 message_content intent。
    """
    if not config.discord.bot_token or not config.discord.guild_id or not config.discord.channel_id:
        return []

    start_utc = _to_utc(start_time)
    end_utc = _to_utc(end_time)
    fetched: List[RawDiscordMessage] = []

    intents = discord.Intents.default()
    intents.message_content = True
    intents.guilds = True

    client = discord.Client(intents=intents)

    async def on_ready() -> None:
        nonlocal fetched
        guild = client.get_guild(config.discord.guild_id)
        if not guild:
            await client.close()
            return
        channel = guild.get_channel(config.discord.channel_id)
        if not channel:
            await client.close()
            return
        after_dt = start_utc
        while True:
            batch: List[discord.Message] = [
                m async for m in channel.history(limit=100, after=after_dt, before=end_utc)
            ]
            for msg in batch:
                content = msg.content.strip() if msg.content else ""
                if not content and (msg.attachments or msg.embeds):
                    content = "[图片/附件]"
                fetched.append(
                    RawDiscordMessage(
                        message_id=msg.id,
                        author_name=msg.author.name if msg.author else "未知",
                        author_id=msg.author.id if msg.author else 0,
                        content=content,
                        created_at=msg.created_at,
                        jump_url=msg.jump_url,
                    )
                )
            if len(batch) < 100:
                break
            after_dt = batch[-1].created_at

        await client.close()

    client.event(on_ready)
    await client.start(config.discord.bot_token)
    return fetched
