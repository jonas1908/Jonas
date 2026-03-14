"""Discord HTTP API 拉取消息（不用 WebSocket，不会卡住）"""

import requests
from datetime import datetime, timezone
from typing import List

from .config import AppConfig
from .models import RawDiscordMessage

# 防止拉取过多导致长时间运行，最多拉 20 页
MAX_PAGES = 20


def _to_snowflake(dt: datetime) -> int:
    """把时间转为 Discord snowflake 数值（用于比较）。"""
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc)
    epoch = datetime(2015, 1, 1, tzinfo=timezone.utc)
    ms = int((dt.replace(tzinfo=timezone.utc) - epoch).total_seconds() * 1000)
    return ms << 22


def _parse_discord_ts(ts: str) -> datetime:
    """解析 Discord 返回的 ISO 时间字符串为 datetime。"""
    if not ts:
        return datetime.now(timezone.utc)
    try:
        ts = ts.replace("Z", "+00:00")
        return datetime.fromisoformat(ts)
    except Exception:
        return datetime.now(timezone.utc)


async def fetch_suggestions_for_period(
    config: AppConfig, start_time: datetime, end_time: datetime
) -> List[RawDiscordMessage]:
    if not config.discord.bot_token or not config.discord.guild_id or not config.discord.channel_id:
        print("[Discord] 缺少配置（DISCORD_BOT_TOKEN/GUILD_ID/CHANNEL_ID），跳过拉取。")
        return []

    print("[Discord] 开始拉取消息...")
    print(f"[Discord] channel_id={config.discord.channel_id}, 时间范围: {start_time} ~ {end_time}")

    headers = {"Authorization": f"Bot {config.discord.bot_token}"}
    base_url = f"https://discord.com/api/v10/channels/{config.discord.channel_id}/messages"
    after_id = str(_to_snowflake(start_time))
    end_snowflake = _to_snowflake(end_time)
    fetched: List[RawDiscordMessage] = []
    page = 0

    while page < MAX_PAGES:
        page += 1
        params = {"after": after_id, "limit": 100}
        try:
            resp = requests.get(base_url, headers=headers, params=params, timeout=30)
        except Exception as e:
            print(f"[Discord] ❌ 请求异常: {e}")
            break

        if resp.status_code != 200:
            print(f"[Discord] ❌ API 错误: {resp.status_code} {resp.text[:300]}")
            break

        messages = resp.json()
        if not messages:
            print("[Discord] 没有更多消息。")
            break

        messages.reverse()
        for msg in messages:
            msg_id = int(msg["id"])
            if msg_id >= end_snowflake:
                continue
            content = (msg.get("content") or "").strip()
            if not content:
                content = "[图片/附件]"
            author = msg.get("author", {})
            ts = msg.get("timestamp", "")
            fetched.append(
                RawDiscordMessage(
                    message_id=msg_id,
                    author_name=author.get("username", "未知"),
                    author_id=int(author.get("id", 0)),
                    content=content,
                    created_at=_parse_discord_ts(ts),
                    jump_url=f"https://discord.com/channels/{config.discord.guild_id}/{config.discord.channel_id}/{msg_id}",
                )
            )
            after_id = str(msg_id)

        if len(messages) < 100:
            break

    print(f"[Discord] ✅ 拉取完成，共 {len(fetched)} 条")
    return fetched