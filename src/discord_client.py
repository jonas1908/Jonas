"""Discord HTTP API 拉取论坛帖子"""

import requests
from datetime import datetime, timezone
from typing import List
from .config import AppConfig
from .models import RawDiscordMessage

def _to_snowflake(dt):
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc)
    epoch = datetime(2015, 1, 1, tzinfo=timezone.utc)
    ms = int((dt.replace(tzinfo=timezone.utc) - epoch).total_seconds() * 1000)
    return str(ms << 22)

def _snowflake_to_time(sid):
    ms = (sid >> 22) + 1420070400000
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)

async def fetch_suggestions_for_period(config, start_time, end_time):
    if not config.discord.bot_token or not config.discord.channel_id:
        print("[Discord] 缺少配置，跳过拉取。")
        return []
    print("[Discord] 开始拉取论坛帖子...")
    print("[Discord] channel_id=" + str(config.discord.channel_id))
    print("[Discord] 时间范围: " + str(start_time) + " ~ " + str(end_time))
    headers = {"Authorization": "Bot " + config.discord.bot_token}
    channel_id = config.discord.channel_id
    guild_id = config.discord.guild_id
    if start_time.tzinfo is not None:
        start_utc = start_time.astimezone(timezone.utc)
    else:
        start_utc = start_time.replace(tzinfo=timezone.utc)
    if end_time.tzinfo is not None:
        end_utc = end_time.astimezone(timezone.utc)
    else:
        end_utc = end_time.replace(tzinfo=timezone.utc)
    fetched = []
    all_threads = []
    print("[Discord] 拉取活跃线程...")
    active_url = "https://discord.com/api/v10/guilds/" + str(guild_id) + "/threads/active"
    resp = requests.get(active_url, headers=headers, timeout=30)
    print("[Discord] 活跃线程响应: " + str(resp.status_code))
    if resp.status_code == 200:
        data = resp.json()
        threads = data.get("threads", [])
        for t in threads:
            if str(t.get("parent_id")) == str(channel_id):
                all_threads.append(t)
        print("[Discord] 活跃线程中属于该频道的: " + str(len(all_threads)) + " 个")
    print("[Discord] 拉取已归档线程...")
    archived_url = "https://discord.com/api/v10/channels/" + str(channel_id) + "/threads/archived/public"
    resp2 = requests.get(archived_url, headers=headers, timeout=30)
    print("[Discord] 归档线程响应: " + str(resp2.status_code))