"""
入口脚本（当前阶段：先把“飞书机器人发消息”链路跑通）。

你现在的目标是：
- GitHub Actions 每周定时触发
- 用飞书应用机器人（AppID/AppSecret）向指定群 chat_id 发送周报

因此此文件先实现一个“最小可用版本”：
- 不读取 Discord
- 不调用 AI
- 直接生成一份占位周报并发到飞书群

等链路跑通后，再逐步把 Discord 收集与 AI 分析接回来。
"""

from __future__ import annotations

from datetime import datetime, timedelta

import zoneinfo

from .config import get_config
from .feishu_client import send_weekly_report_card
from .models import WeeklyReport


def _get_current_week_range(tz_name: str) -> tuple[datetime, datetime]:
    """
    计算当前周的起止时间（以周一为一周的开始）。
    方便我们按“自然周”统计玩家建议。
    """
    tz = zoneinfo.ZoneInfo(tz_name)
    now = datetime.now(tz)
    week_start = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    week_end = week_start + timedelta(days=7)
    return week_start, week_end


async def run_weekly_pipeline() -> None:
    """
    跑一次周报流程（当前：只发送飞书测试消息）。
    """
    config = get_config()

    week_start, week_end = _get_current_week_range(config.timezone)

    report = WeeklyReport(
        week_start=week_start,
        week_end=week_end,
        suggestions=[],
        overall_summary="（这是测试消息：等接入 Discord + AI 后会自动生成真正的周报内容）",
    )
    send_weekly_report_card(config=config, report=report)


def main() -> None:
    """
    同步入口封装，方便将来用命令行运行：
    `python -m src.main`
    """
    import asyncio

    asyncio.run(run_weekly_pipeline())


if __name__ == "__main__":
    main()

