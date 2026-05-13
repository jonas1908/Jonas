"""Discord HTTP API 拉取论坛帖子"""

import requests
from datetime import datetime, timezone
from .config import AppConfig
from .models import RawDiscordMessage

def _snowflake_to_time(sid):
    ms = (int(sid) >> 22) + 1420070400000
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)

async def fetch_suggestions_for_period(config, start_time, end_time, channel_id=None):
    if not config.discord.bot_token:
        print("[Discord] 缺少配置，跳过。")
        return []

    target_channel_id = str(channel_id) if channel_id else str(config.discord.channel_id)

    if not target_channel_id or target_channel_id == "0":
        print("[Discord] 缺少频道ID，跳过。")
        return []

    print("[Discord] 开始拉取频道: " + target_channel_id)
    headers = {"Authorization": "Bot " + config.discord.bot_token}
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

    # 1. 拉取活跃线程
    url1 = "https://discord.com/api/v10/guilds/" + guild_id + "/threads/active"
    r1 = requests.get(url1, headers=headers, timeout=30)
    print("[Discord] 活跃线程响应: " + str(r1.status_code))
    if r1.status_code == 200:
        for t in r1.json().get("threads", []):
            if str(t.get("parent_id", "")) == target_channel_id:
                all_threads.append(t)
        print("[Discord] 活跃: " + str(len(all_threads)))

    # 2. 翻页拉取所有归档线程
    archived_count = 0
    before_ts = None
    for page in range(10):  # 最多翻10页，防止死循环
        url2 = "https://discord.com/api/v10/channels/" + target_channel_id + "/threads/archived/public?limit=100"
        if before_ts:
            url2 = url2 + "&before=" + before_ts
        r2 = requests.get(url2, headers=headers, timeout=30)
        print("[Discord] 归档第" + str(page + 1) + "页响应: " + str(r2.status_code))
        if r2.status_code != 200:
            break
        data = r2.json()
        archived = data.get("threads", [])
        if not archived:
            break
        all_threads.extend(archived)
        archived_count = archived_count + len(archived)

        # 检查是否还有更多
        has_more = data.get("has_more", False)
        if not has_more:
            break

        # 用最后一个线程的 archive_timestamp 作为下一页的 before
        last_thread = archived[-1]
        meta = last_thread.get("thread_metadata", {})
        before_ts = meta.get("archive_timestamp", "")
        if not before_ts:
            break

    print("[Discord] 归档总计: " + str(archived_count))
    print("[Discord] 总线程: " + str(len(all_threads)))

    fetched = []
    count = 0
    for thread in all_threads:
        tid = str(thread["id"])
        tname = thread.get("name", "无标题")
        created = _snowflake_to_time(tid)
        if created < start_utc or created >= end_utc:
            continue
        count = count + 1
        mc = int(thread.get("message_count", 0) or 0)
        tms = int(thread.get("total_message_sent", 0) or 0)
        if tms > mc:
            mc = tms
        member_count = int(thread.get("member_count", 0) or 0)
        print("[Discord] 线程: " + tname + " mc=" + str(thread.get("message_count")) + " tms=" + str(thread.get("total_message_sent")) + " members=" + str(member_count))

        url3 = "https://discord.com/api/v10/channels/" + tid + "/messages?limit=1&after=0"
        r3 = requests.get(url3, headers=headers, timeout=30)
        content = ""
        author_name = "未知"
        author_id = 0
        if r3.status_code == 200 and r3.json():
            msg = r3.json()[0]
            content = (msg.get("content") or "").strip()
            if not content:
                content = "[图片/附件]"
            author = msg.get("author", {})
            author_name = author.get("username", "未知")
            author_id = int(author.get("id", 0))

        heat = mc
        full_content = "【" + tname + "】\n" + content
        jump_url = "https://discord.com/channels/" + guild_id + "/" + tid
        print("[Discord] [" + str(count) + "] " + tname + " | 消息:" + str(mc) + " 热度:" + str(heat) + " 参与:" + str(member_count))

        post = RawDiscordMessage(
            message_id=int(tid),
            author_name=author_name,
            author_id=author_id,
            content=full_content,
            created_at=str(created),
            jump_url=jump_url,
            message_count=mc,
            reaction_count=0,
            heat_score=heat,
            member_count=member_count
        )
        fetched.append(post)

    fetched.sort(key=lambda x: x.heat_score, reverse=True)
    print("[Discord] 完成，共 " + str(len(fetched)) + " 个")
    if fetched:
        print("[Discord] 最高热度: " + str(fetched[0].heat_score) + " " + fetched[0].content[:50])
    return fetched
