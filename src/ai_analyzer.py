"""
AI 分析模块：
- 调用大模型，对每条建议做分类、总结、打分
- 支持批量分析一周内所有建议

当前只写好接口和流程骨架，后续会补 prompt 和真实调用。
"""

from typing import List

from .config import AppConfig
from .models import RawDiscordMessage, AnalyzedSuggestion, WeeklyReport


def analyze_single_suggestion(
    config: AppConfig,
    message: RawDiscordMessage,
) -> AnalyzedSuggestion:
    """
    使用大模型分析一条 Discord 建议。

    后续会在这里：
    - 组装 prompt（包含玩家原始文本、上下文信息）
    - 调用 OpenAI / 其他模型 API
    - 解析模型返回的 JSON 结果
    """
    # TODO: 实现真实 AI 调用逻辑
    raise NotImplementedError("单条建议的 AI 分析功能尚未实现")


def analyze_batch_suggestions(
    config: AppConfig,
    messages: List[RawDiscordMessage],
) -> List[AnalyzedSuggestion]:
    """
    批量分析多条建议。
    可以根据需要做：
    - 并行调用
    - 控制速率（避免 API 限流）
    """
    # TODO: 实现批量调用逻辑（目前先留空）
    raise NotImplementedError("批量建议的 AI 分析功能尚未实现")


def build_weekly_report(
    config: AppConfig,
    analyzed: List[AnalyzedSuggestion],
) -> WeeklyReport:
    """
    根据一周内所有的分析结果，生成周报数据结构：
    - 汇总整体结论、亮点、高频需求
    - 统计数量、类别分布、优先级等
    - 为飞书卡片准备好展示文案
    """
    # TODO: 实现周报汇总逻辑
    raise NotImplementedError("周报汇总功能尚未实现")

