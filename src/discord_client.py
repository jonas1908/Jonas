"""Discord HTTP API 拉取消息（不用 WebSocket，不会卡住）"""

import os
import requests
from datetime import datetime, timezone
from typing import List
from .config import AppConfig
from .models import RawDiscordMessage

def _to_snowflake(dt: datetime) -> str:
    """把时间转为 Discord snowflake ID（用于 after 参数）"""
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc)
    epoch = datetime(2015, 1, 1, tzinfo=timezone.utc)
    ms = int((dt.replace(tzinfo=timezone.utc) - epoch).total_seconds() * 1000)
    return str(ms << 22)

async def fetch_suggestions_for_period(config: AppConfig, start_time: datetime, end_time: datetime) -> List[RawDiscordMessage]:
    if not config.discord.bot_token or not config.discord.channel_id:
        print("[Discord] 缺少配置，跳过拉取。")
        return []

    print(f"[Discord] 开始拉取消息...")
    print(f"[Discord] channel_id={config.discord.channel_id}")
    print(f"[Discord] 时间范围: {start_time} ~ {end_time}")

    headers = {"Authorization": f"Bot {config.discord.bot_token}"}
    base_url = f"https://discord.com/api/v10/channels/{config.discord.channel_id}/messages"
    after_id = _to_snowflake(start_time)
    end_snowflake = int(_to_snowflake(end_time))
    fetched = []

    while True:
        params = {"after": after_id, "limit": 100}
        print(f"[Discord] 请求中... after={after_id}")
        resp = requests.get(base_url, headers=headers, params=params, timeout=30)
        print(f"[Discord] 响应状态: {resp.status_code}")

        if resp.status_code != 200:
            print(f"[Discord] ❌ API 错误: {resp.status_code} {resp.text[:200]}")
            break

        messages = resp.json()
        if not messages:
            print("[Discord] 没有更多消息了")
            break

        # Discord 返回的是倒序，需要反转
        messages.reverse()

        for msg in messages:
            msg_id = int(msg["id"])
            if msg_id >= end_snowflake:
                continue
            content = (msg.get("content") or "").strip()
            if not content:
                content = "[图片/附件]"
            author = msg.get("author", {})
            fetched.append(RawDiscordMessage(
                message_id=msg_id,
                author_name=author.get("username", "未知"),
                author_id=int(author.get("id", 0)),
                content=content,
                created_at=msg.get("timestamp", ""),
                jump_url=f"https://discord.com/channels/{config.discord.guild_id}/{config.discord.channel_id}/{msg_id}",
            ))
            after_id = str(msg_id)

        if len(messages) < 100:
            break

    print(f"[Discord] ✅ 拉取完成，共 {len(fetched)} 条")
    return fetched