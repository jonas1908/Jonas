"""Discord HTTP API 拉取论坛帖子（标题 + 第一条内容）"""

import requests
from datetime import datetime, timezone
from typing import List
from .config import AppConfig
from .models import RawDiscordMessage

def _to_snowflake(dt: datetime) -> str:
    """把时间转为 Discord snowflake ID"""
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc)
    epoch = datetime(2015, 1, 1, tzinfo=timezone.utc)
    ms = int((dt.replace(tzinfo=timezone.utc) - epoch).total_seconds() * 1000)
    return str(ms << 22)

def _snowflake_to_time(snowflake_id: int) -> datetime:
    """把 snowflake ID 转为 UTC 时间"""
    ms = (snowflake_id >> 22) + 1420070400000
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)

async def fetch_suggestions_for_period(config: AppConfig, start_time: datetime, end_time: datetime) -> List[RawDiscordMessage]:
    if not config.discord.bot_token or not config.discord.channel_id:
        print("[Discord] 缺少配置，跳过拉取。")
        return []

    print(f"[Discord] 开始拉取论坛帖子...")
    print(f"[Discord] channel_id={config.discord.channel_id}")
    print(f"[Discord] 时间范围: {start_time} ~ {end_time}")

    headers = {"Authorization": f"Bot {config.discord.bot_token}"}
    channel_id = config.discord.channel_id
    guild_id = config.discord.guild_id

    # 转为 UTC 用于比较
    if start_time.tzinfo is not None:
        start_utc = start_time.astimezone(timezone.utc)
    else:
        start_utc = start_time.replace(tzinfo=timezone.utc)
    if end_time.tzinfo is not None:
        end_utc = end_time.astimezone(timezone.utc)
    else:
        end_utc = end_time.replace(tzinfo=timezone.utc)

    # 第1步：获取论坛频道下的所有活跃线程
    fetched = []

    # 拉取活跃线程
    print("[Discord] 拉取活跃线程...")
    active_url = f"https://discord.com/api/v10/guilds/{guild_id}/threads/active"
    resp = requests.get(active_url, headers=headers, timeout=30)
    print(f"[Discord] 活跃线程响应: {resp.status_code}")

    all_threads = []
    if resp.status_code == 200:
        data = resp.json()
        threads = data.get("threads", [])
        for t in threads:
            if str(t.get("parent_id")) == str(channel_id):
                all_threads.append(t)
        print(f"[Discord] 活跃线程中属于该频道的: {len(all_threads)} 个")

    # 拉取已归档线程
    print("[Discord] 拉取已归档线程...")
    archived_url = f"https://discord.com/api/v10/channels/{channel_id}/threads/archived/public"
    resp2 = requests.get(archived_url, headers=headers, timeout=30)
    print(f"[Discord] 归档线程响应: {resp2.status_code}")

    if resp2.status_code == 200:
        data2 = resp2.json()
        archived_threads = data2.get("threads", [])
        for t in archived_threads:
            all_threads.append(t)
        print(f"[Discord] 归档线程: {len(archived_threads)} 个")

    print(f"[Discord] 总共找到 {len(all_threads)} 个线程")

    # 第2步：筛选时间范围内的帖子，拉取第一条消息
    for thread in all_threads:
        thread_id = int(thread["id"])
        thread_name = thread.get("name", "无标题")
        created_at = _snowflake_to_time(thread_id)

        # 筛选时间范围
        if created_at < start_utc or created_at >= end_utc:
            continue

        print(f"[Discord] 处理帖子: {thread_name} (创建于 {created_at})")

        # 拉取帖子的第一条消息
        msg_url = f"https://discord.com/api/v10/channels/{thread_id}/messages"
        params = {"limit": 1, "after": _to_snowflake(datetime(2015, 1, 2, tzinfo=timezone.utc))}
        resp3 = requests.get(msg_url, headers=headers, params=params, timeout=30)

        content = ""
        author_name = "未知"
        author_id = 0

        if resp3.status_code == 200:
            messages = resp3.json()
            if messages:
                first_msg = messages[0]
                content = (first_msg.get("content") or "").strip()
                if not content:
                    content = "[图片/附件]"
                author = first_msg.get("author", {})
                author_name = author.get("username", "未知")
                author_id = int(author.get("id", 0))
        else:
            print(f"[Discord] ⚠️ 拉取帖子内容失败: {resp3.status_code}")

        # 组合：标题 + 内容
        full_content = f"【{thread_name}】\n{content}"

        fetched.append(RawDiscordMessage(
            message