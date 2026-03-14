"""周报主流程"""

from datetime import datetime, timedelta
import zoneinfo

from .config import get_config
from .discord_client import fetch_suggestions_for_period
from .ai_analyzer import analyze_batch_suggestions, build_weekly_report
from .feishu_client import send_weekly_report_card

def _get_current_week_range(tz_name):
    tz = zoneinfo.ZoneInfo(tz_name)
    now = datetime.now(tz)
    week_start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = week_start + timedelta(days=7)
    return week_start, week_end

async def run_weekly_pipeline():
    config = get_config()
    week_start, week_end = _get_current_week_range(config.timezone)
    print(f"[周报] 时间范围: {week_start} ~ {week_end}")
    has_discord = bool(config.discord.bot_token and config.discord.guild_id and config.discord.channel_id)
    if not has_discord:
        print("[周报] 未配置 Discord，按 0 条处理。")
    raw_messages = await fetch_suggestions_for_period(config=config, start_time=week_start, end_time=week_end)
    print(f"[周报] Discord 拉取到 {len(raw_messages)} 条消息。")
    analyzed = analyze_batch_suggestions(config=config, messages=raw_messages)
    print(f"[周报] AI 分析完成，共 {len(analyzed)} 条。")
    report = build_weekly_report(config=config, analyzed=analyzed, week_start=week_start, week_end=week_end)
    if not analyzed:
        print("[周报] 本周暂无玩家建议。")
    send_weekly_report_card(config=config, report=report)
    print("[周报] 飞书周报已发送。")

def main():
    import asyncio
    import sys
    print("[周报] ===== 脚本启动 =====")
    try:
        asyncio.run(run_weekly_pipeline())
    except Exception as e:
        print(f"[周报] ❌ 执行失败: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()