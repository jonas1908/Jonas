"""
Discord 相关操作：
- 使用 Bot Token 登录
- 从指定服务器 / 频道，在指定时间范围内拉取消息
"""

from datetime import datetime, timezone
from typing import List

import asyncio
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
    if not config.discord.bot_token or not config.discord.guild_id or not config.discord.channel_id:
        print("[Discord] 缺少配置，跳过拉取。")
        return []

    start_utc = _to_utc(start_time)
    end_utc = _to_utc(end_time)
    fetched: List[RawDiscordMessage] = []

    intents = discord.Intents.default()
    intents.message_content = True
    intents.guilds = True

    client = discord.Client(intents=intents)

    # 打印配置信息（脱敏）
    print(f"[Discord] guild_id={config.discord.guild_id} (type={type(config.discord.guild_id).__name__})")
    print(f"[Discord] channel_id={config.discord.channel_id} (type={type(config.discord.channel_id).__name__})")
    print(f"[Discord] 时间范围: {start_utc} ~ {end_utc}")

    async def on_ready() -> None:
        nonlocal fetched
        try:
            print(f"[Discord] Bot 已登录: {client.user}")
            print(f"[Discord] Bot 所在服务器: {[g.name for g in client.guilds]}")

            guild = client.get_guild(int(config.discord.guild_id))
            if not guild:
                print(f"[Discord] ❌ 找不到服务器 guild_id={config.discord.guild_id}")
                print(f"[Discord] Bot 可见的服务器ID: {[g.id for g in client.guilds]}")
                await client.close()
                return

            print(f"[Discord] ✅ 找到服务器: {guild.name}")

            channel = guild.get_channel(int(config.discord.channel_id))
            if not channel:
                print(f"[Discord] ❌ 找不到频道 channel_id={config.discord.channel_id}")
                print(f"[Discord] 可见频道: {[(c.name, c.id) for c in guild.channels[:20]]}")
                await client.close()
                return

            print(f"[Discord] ✅ 找到频道: {channel.name}")

            # 拉取消息
            total = 0
            after_dt = start_utc
            while True:
                batch: List[discord.Message] = [
                    m async for m in channel.history(limit=100, after=after_dt, before=end_utc)
                ]
                total += len(batch)
                print(f"[Discord] 本批拉取 {len(batch)} 条，累计 {total} 条")

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

            print(f"[Discord] ✅ 拉取完成，共 {len(fetched)} 条消息")
        except Exception as e:
            print(f"[Discord] ❌ 出错: {e}")
        finally:
            await client.close()

    client.event(on_ready)

    # 加超时保护，最多等 120 秒
    try:
        await asyncio.wait_for(client.start(config.discord.bot_token), timeout=120)
    except asyncio.TimeoutError:
        print("[Discord] ❌ 超时（120秒），强制关闭")
        await client.close()
    except discord.LoginFailure:
        print("[Discord] ❌ Bot Token 无效，登录失败！")
    except Exception as e:
        print(f"[Discord] ❌ 连接异常: {e}")

    return fetched