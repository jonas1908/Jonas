"""
Discord 相关操作：
- 使用 Bot Token 登录
- 从指定服务器 / 频道，在指定时间范围内拉取消息

当前仅提供函数骨架，后续会补充具体实现。
"""

from datetime import datetime
from typing import List

from .config import AppConfig
from .models import RawDiscordMessage


async def fetch_suggestions_for_period(
    config: AppConfig,
    start_time: datetime,
    end_time: datetime,
) -> List[RawDiscordMessage]:
    """
    从 Discord 指定频道拉取在 [start_time, end_time] 之间的消息。

    后续会在这里：
    - 初始化 discord.Client / Bot
    - 连接到对应 Guild / Channel
    - 过滤只保留“玩家建议”相关的消息（例如带特定前缀或在特定子频道）
    """
    # TODO: 实现真实逻辑
    raise NotImplementedError("Discord 消息拉取功能尚未实现")

