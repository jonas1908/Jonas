"""
周报主流程：Discord 拉取 → AI 分析 → 飞书发送。

- 从 Discord 指定频道拉取本周消息
- 用 OpenAI 对每条做分类、总结、打分
- 生成周报并发送到飞书群
"""


from datetime import datetime, timedelta
import zoneinfo

from .config import get_config
from .discord_client import fetch_suggestions_for_period
from .ai_analyzer import analyze_batch_suggestions, build_weekly_report
from .feishu_client import send_weekly_report_card

def _get_current_week_range(tz_name: str) -> tuple[datetime, datetime]:
    """当前周的起止时间（周一 0 点 ~ 下周一 0 点），带时区。"""
    tz = zoneinfo.ZoneInfo(tz_name)
    now = datetime.now(tz)
    week_start = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    week_end = week_start + timedelta(days=7)
    return week_start, week_end

async def run_weekly_pipeline() -> None:
    """跑一次完整流程：拉取 Discord → AI 分析 → 发飞书。"""
    config = get_config()
    week_start, week_end = _get_current_week_range(config.timezone)

    # 1. 从 Discord 拉取本周消息
    has_discord = bool(
        config.discord.bot_token and config.discord.guild_id and config.discord.