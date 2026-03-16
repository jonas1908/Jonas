"""飞书发送周报"""

from .config import AppConfig
from .models import WeeklyReport
from .feishu_api import get_tenant_access_token, send_text_message_to_chat

RANK_EMOJI = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

def send_weekly_report_card(config, report):
    app_id = config.feishu.app_id
    app_secret = config.feishu.app_secret
    chat_id = config.feishu.report_chat_id
    if not app_id or not app_secret or not chat_id:
        raise RuntimeError("缺少飞书配置：需要 FEISHU_APP_ID / FEISHU_APP_SECRET / FEISHU_REPORT_CHAT_ID")
    token = get_tenant_access_token(app_id=app_id, app_secret=app_secret)
    lines = []
    lines.append("🏆 本周玩家建议 Top 10")
    lines.append("📅 " + str(report.week_start.strftime("%Y-%m-%d")) + " ~ " + str(report.week_end.strftime("%Y-%m-%d")))
    lines.append("📊 本周共 " + str(report.total_posts) + " 个帖子")
    lines.append("")
    if not report.top_suggestions:
        lines.append("本周暂无玩家建议。")
    else:
        for s in report.top_suggestions:
            emoji = RANK_EMOJI[s.rank - 1] if s.rank <= 10 else str(s.rank)
            lines.append(emoji + " Top" + str(s.rank) + "：" + s.title)
            lines.append(s.description)
            lines.append("🔥 热度: " + str(s.heat_score) + "  😡 情绪分: " + str(s.anger_score) + "/10  📋 建议数: " + str(s.similar_count))
            lines.append("")
    text = "\n".join(lines)
    print("[飞书] 发送内容预览:")
    print(text)
    send_text_message_to_chat(tenant_access_token=token.token, chat_id=chat_id, text=text)