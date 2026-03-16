"""Discord HTTP API 拉取论坛帖子 + 热度"""

import requests
from datetime import datetime, timezone
from .config import AppConfig
from .models import RawDiscordMessage

def _snowflake_to_time(sid):
    ms = (int(sid) >> 22) + 1420070400000
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)

async def fetch_suggestions_for_period(config, start_time, end_time):
    try:
        if not config.discord.bot_token or not config.discord.channel_id:
            print("[Discord] 缺少配置，跳过。")
            return []
        print("[Discord] 开始拉取论坛帖子...")
        headers = {"Authorization": "Bot " + config.discord.bot_token}
        channel_id = str(config.discord.channel_id)
        guild_id = str(config.discord.guild_id)
        if start_time.tzinfo is not None:
            start_utc = start_time.astimezone(timezone.utc)
        else:
            start_utc = start_time.replace(tzinfo=timezone.utc)
        if end_time.tzinfo is not None:
            end_utc = end_time.astimezone(timezone.utc)
        else:
            end_utc = end_time.replace(tzinfo=timezone.utc)
        print("[Discord] 时间: " + str(start_utc) + " ~ " + str(end_utc))
        all_threads = []
        print("[Discord] 拉取活跃线程...")
        url