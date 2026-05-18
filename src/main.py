"""周报主流程"""

from datetime import datetime, timedelta
import zoneinfo
from .config import get_config
from .discord_client import fetch_suggestions_for_period
from .ai_analyzer import analyze_and_rank, build_weekly_report
from .feishu_client import send_weekly_report_card
from .bitable_writer import write_to_bitable

def _get_current_week_range(tz_name):
    tz = zoneinfo.ZoneInfo(tz_name)
    now = datetime.now(tz)
    # 本周一
    this_monday = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    # 上周一
    last_monday = this_monday - timedelta(days=7)
    # 拉取上周一 ~ 本周一的数据
    week_start = last_monday
    week_end = this_monday
    return week_start, week_end

async def run_weekly_pipeline():
    config = get_config()
    week_start, week_end = _get_current_week_range(config.timezone)
    print("[周报] 时间范围: " + str(week_start) + " ~ " + str(week_end))

    channels = config.discord.channels
    if not channels:
        print("[周报] 没有配置任何频道，退出。")
        return

    for ch in channels:
        print("")
        print("=" * 50)
        print("[周报] 开始处理频道: " + ch.label + " (ID: " + str(ch.channel_id) + ")")
        print("=" * 50)

        raw_posts = await fetch_suggestions_for_period(
            config=config,
            start_time=week_start,
            end_time=week_end,
            channel_id=ch.channel_id
        )
        raw_posts = raw_posts or []
        print("[周报] Discord 拉取到 " + str(len(raw_posts)) + " 个帖子。")

        top10 = analyze_and_rank(config=config, posts=raw_posts)
        print("[周报] Top10 生成完成，共 " + str(len(top10)) + " 条。")

        report = build_weekly_report(
            config=config,
            top_suggestions=top10,
            week_start=week_start,
            week_end=week_end,
            total_posts=len(raw_posts)
        )

        # 发送到飞书群
        send_weekly_report_card(config=config, report=report, channel_label=ch.label)
        print("[周报] 频道 " + ch.label + " 飞书周报已发送。")

        # 写入多维表格（只针对第一个频道 DISCORD_CHANNEL_ID）
        if ch.channel_id == config.discord.channel_id:
            print("[周报] 开始写入多维表格...")
            write_to_bitable(config=config, suggestions=top10)
            print("[周报] 多维表格写入完成。")

    print("")
    print("[周报] ===== 全部频道处理完毕 =====")

def main():
    import asyncio
    print("[周报] ===== 脚本启动 =====")
    asyncio.run(run_weekly_pipeline())

if __name__ == "__main__":
    main()
