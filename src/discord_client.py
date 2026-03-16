"""Discord HTTP API 拉取论坛帖子"""

import requests
from datetime import datetime, timezone
from .config import AppConfig
from .models import RawDiscordMessage

def _to_snowflake(dt):
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc)
    epoch = datetime(2015, 1, 1, tzinfo=timezone.utc)
    ms = int((dt.replace(tzinfo=timezone.utc) - epoch).total_seconds() * 1000)
    return str(ms << 22)

def _snowflake_to_time(sid):
    ms = (int(sid) >> 22) + 1420070400000
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)

async def fetch_suggestions_for_period(config, start_time, end_time):
    try:
        if not config.discord.bot_token or not config.discord.channel_id:
            print("[Discord] 缺少配置，跳过拉取。")
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
        print("[Discord] 时间范围: " + str(start_utc) + " ~ " + str(end_utc))
        all_threads = []
        print("[Discord] 拉取活跃线程...")
        active_url = "https://discord.com/api/v10/guilds/" + guild_id + "/threads/active"
        resp = requests.get(active_url, headers=headers, timeout=30)
        print("[Discord] 活跃线程响应: " + str(resp.status_code))
        if resp.status_code == 200:
            data = resp.json()
            for t in data.get("threads", []):
                if str(t.get("parent_id", "")) == channel_id:
                    all_threads.append(t)
            print("[Discord] 活跃线程中属于该频道: " + str(len(all_threads)) + " 个")
        print("[Discord] 拉取已归档线程...")
        archived_url = "https://discord.com/api/v10/channels/" + channel_id + "/threads/archived/public"
        resp2 = requests.get(archived_url, headers=headers, timeout=30)
        print("[Discord] 归档线程响应: " + str(resp2.status_code))
        if resp2.status_code == 200:
            data2 = resp2.json()
            archived = data2.get("threads", [])
            if archived is not None:
                for t in archived:
                    all_threads.append(t)
                print("[Discord] 归档线程: " + str(len(archived)) + " 个")
        print("[Discord] 总共: " + str(len(all_threads)) + " 个线程")
        fetched = []
        count = 0
        for thread in all_threads:
            try:
                thread_id = str(thread["id"])
                thread_name = thread.get("name", "无标题")
                created_at = _snowflake_to_time(thread_id)
                if created_at < start_utc or created_at >= end_utc:
                    continue
                count = count + 1
                print("[Discord] [" + str(count) + "] " + thread_name)
                msg_url = "https://discord.com/api/v10/channels/" + thread_id + "/messages?limit=1"
                resp3 = requests.get(msg_url, headers=headers, timeout=30)
                content = ""
                author_name = "未知"
                author_id = 0
                if resp3.status_code == 200:
                    messages = resp3.json()
                    if messages and len(messages) > 0:
                        first_msg = messages[0]
                        content = (first_msg.get("content") or "").strip()
                        if not content:
                            content = "[图片/附件]"
                        author = first_msg.get("author", {})
                        author_name = author.get("username", "未知")
                        author_id = int(author.get("id", 0))
                full_content = "【" + thread_name + "】\n" + content
                msg = RawDiscordMessage(message_id=int(thread_id), author_name=author_name, author_id=author_id, content=full_content, created_at=str(created_at), jump_url="https://discord.com/channels/" + guild_id + "/" + thread_id)
                fetched.append(msg)
            except Exception as e:
                print("[Discord] 处理帖子出错: " + str(e))
                continue
        print("[Discord] 拉取完成，共 " + str(len(fetched)) + " 个帖子")
        return fetched
    except Exception as e:
        print("[Discord] 整体出错: " + str(e))
        return []