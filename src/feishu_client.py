"""飞书发送周报（支持多个群）"""

import os
from .config import AppConfig
from .models import WeeklyReport
from .feishu_api import get_tenant_access_token, send_text_message_to_chat

RANK_EMOJI = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

def _build_text(report):
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
            if s.jump_url:
                lines.append("🔗 " + s.jump_url)
            lines.append("")
    return "\n".join(lines)

def send_weekly_report_card(config, report):
    app_id = config.feishu.app_id
    app_secret = config.feishu.app_secret
    if not app_id or not app_secret:
        raise RuntimeError("缺少飞书配置")
    token = get_tenant_access_token(app_id=app_id, app_secret=app_secret)
    text = _build_text(report)
    print("[飞书] 发送内容:")
    print(text)
    chat_ids = []
    chat_id_1 = config.feishu.report_chat_id
    chat_id_2 = os.getenv("FEISHU_REPORT_CHAT_ID_2", "")
    if chat_id_1:
        chat_ids.append(chat_id_1)
    if chat_id_2:
        chat_ids.append(chat_id_2)
    if not chat_ids:
        raise RuntimeError("没有配置任何飞书群 chat_id")
    for cid in chat_ids:
        print("[飞书] 发送到群: " + cid)
        try:
            send_text_message_to_chat(tenant_access_token=token.token, chat_id=cid, text=text)
            print("[飞书] ✅ 发送成功: " + cid)
        except Exception as e:
            print("[飞书] ❌ 发送失败: " + cid + " 错误: " + str(e))
    print("[飞书] 全部发送完成")