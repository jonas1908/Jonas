"""
飞书相关操作：
- 使用 App ID / Secret 获取 tenant_access_token
- 向指定群 chat_id 发送周报消息（先做最小可用版本）

当前为骨架实现，后续会根据你实际的飞书应用配置补充细节。
"""

from typing import List

from .config import AppConfig
from .models import AnalyzedSuggestion, WeeklyReport
from .feishu_api import get_tenant_access_token, send_text_message_to_chat


def write_suggestions_to_bitable(
    config: AppConfig,
    analyzed: List[AnalyzedSuggestion],
) -> None:
    """
    把分析结果写入飞书多维表格。

    后续会在这里：
    - 初始化 lark-oapi Client
    - 按字段映射构造记录（玩家 ID、原文、分类、总结、分数等）
    - 批量插入或更新记录
    """
    # TODO: 实现写入多维表格逻辑
    raise NotImplementedError("写入飞书多维表格的功能尚未实现")


def send_weekly_report_card(
    config: AppConfig,
    report: WeeklyReport,
) -> None:
    """
    发送周报到飞书群（先发文本，后续再升级为“漂亮卡片”）。

    后续会在这里：
    - 设计卡片 JSON（标题、一周概览、关键数据、TOP 建议等）
    - 调用飞书卡片消息发送接口
    """
    app_id = config.feishu.app_id
    app_secret = config.feishu.app_secret
    chat_id = config.feishu.report_chat_id

    if not app_id or not app_secret or not chat_id:
        raise RuntimeError(
            "缺少飞书配置：需要 FEISHU_APP_ID / FEISHU_APP_SECRET / FEISHU_REPORT_CHAT_ID"
        )

    token = get_tenant_access_token(app_id=app_id, app_secret=app_secret)

    title = "📋 Discord 玩家建议周报"
    lines = [
        title,
        f"📅 时间：{report.week_start:%Y-%m-%d} ~ {report.week_end:%Y-%m-%d}",
        f"📊 条目数：{len(report.suggestions)}",
        "",
        "【本周概览】",
        report.overall_summary or "（暂无）",
    ]
    if report.highlights:
        lines.append("")
        lines.append("【高优先级建议 TOP5】")
        for i, h in enumerate(report.highlights, 1):
            lines.append(f"{i}. {h}")
    if report.stats.get("by_category"):
        lines.append("")
        lines.append("【分类统计】")
        for cat, count in report.stats["by_category"].items():
            lines.append(f"- {cat}：{count} 条")
    text = "\n".join(lines)

    send_text_message_to_chat(
        tenant_access_token=token.token,
        chat_id=chat_id,
        text=text,
    )

