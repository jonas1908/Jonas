"""
AI 分析模块：
- 调用 OpenAI 对每条建议做分类、总结、打分
- 汇总成周报（整体总结、亮点、统计）
"""

import json
import re
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List

from openai import OpenAI

from .config import AppConfig
from .models import RawDiscordMessage, AnalyzedSuggestion, WeeklyReport


SYSTEM_PROMPT = """你是一个游戏社区运营助手。用户会发来一条来自 Discord 的玩家建议/反馈帖子原文，请用 JSON 格式回复，且只输出这一份 JSON，不要其他说明。

字段要求：
- category: 建议的一级分类（如：玩法、平衡性、UI、剧情、活动、Bug、其他），用中文。
- subcategory: 二级分类或更细标签，用中文，没有可填空字符串。
- summary: 一句话总结（30 字以内）。
- detail: 对建议的简要说明或要点（80 字以内）。
- priority_score: 1～10 的整数，表示优先级（10 最高）。
- sentiment: 情绪倾向：正面/中性/负面 之一。
- tags: 字符串数组，如 ["平衡性", "PVP"]，最多 5 个。

只输出一个 JSON 对象，不要 markdown 代码块包裹。"""


def _parse_analysis_response(text: str) -> Dict[str, Any] | None:
    """从模型回复中解析 JSON。"""
    text = text.strip()
    # 去掉可能的 markdown 代码块
    if text.startswith("```"):
        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```\s*$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def analyze_single_suggestion(
    config: AppConfig,
    message: RawDiscordMessage,
) -> AnalyzedSuggestion:
    """用大模型分析一条 Discord 建议。"""
    if not config.openai.api_key:
        return AnalyzedSuggestion(
            source=message,
            category="未分析",
            subcategory=None,
            summary=message.content[:80] + ("..." if len(message.content) > 80 else ""),
            detail=message.content,
            priority_score=5.0,
            sentiment=None,
            tags=[],
        )

    client = OpenAI(api_key=config.openai.api_key)
    user_content = f"玩家 {message.author_name} 的帖子：\n\n{message.content}"

    try:
        resp = client.chat.completions.create(
            model=config.openai.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            response_format={"type": "json_object"},
        )
        raw = (resp.choices[0].message.content or "").strip()
        data = _parse_analysis_response(raw)
    except Exception:
        data = None

    if not data:
        return AnalyzedSuggestion(
            source=message,
            category="解析失败",
            subcategory=None,
            summary=message.content[:80] + ("..." if len(message.content) > 80 else ""),
            detail=message.content,
            priority_score=5.0,
            sentiment=None,
            tags=[],
        )

    def _str(v: Any) -> str:
        return str(v).strip() if v is not None else ""

    def _float(v: Any) -> float:
        try:
            return float(v) if v is not None else 5.0
        except (TypeError, ValueError):
            return 5.0

    def _list_str(v: Any) -> List[str]:
        if isinstance(v, list):
            return [str(x) for x in v[:5]]
        return []

    return AnalyzedSuggestion(
        source=message,
        category=_str(data.get("category") or "其他"),
        subcategory=_str(data.get("subcategory")) or None,
        summary=_str(data.get("summary")) or message.content[:60],
        detail=_str(data.get("detail")) or message.content[:200],
        priority_score=min(10, max(1, _float(data.get("priority_score")))),
        sentiment=_str(data.get("sentiment")) or None,
        tags=_list_str(data.get("tags")),
    )


def analyze_batch_suggestions(
    config: AppConfig,
    messages: List[RawDiscordMessage],
) -> List[AnalyzedSuggestion]:
    """批量分析；无 API Key 时直接返回占位分析。"""
    if not messages:
        return []
    if not config.openai.api_key:
        return [analyze_single_suggestion(config, m) for m in messages]

    result: List[AnalyzedSuggestion] = []
    for i, msg in enumerate(messages):
        result.append(analyze_single_suggestion(config, msg))
        # 简单限流，避免 OpenAI 限频
        if i < len(messages) - 1:
            import time
            time.sleep(0.5)
    return result


def build_weekly_report(
    config: AppConfig,
    analyzed: List[AnalyzedSuggestion],
    week_start: datetime,
    week_end: datetime,
) -> WeeklyReport:
    """根据分析结果生成周报：总结、亮点、统计。"""
    overall = "本周暂无玩家建议。"
    highlights: List[str] = []
    stats: Dict[str, Any] = {"total": len(analyzed), "by_category": {}}

    if analyzed:
        by_cat = Counter(s.category for s in analyzed)
        stats["by_category"] = dict(by_cat)
        top_cats = by_cat.most_common(3)
        overall = f"共 {len(analyzed)} 条建议，主要涉及：{', '.join(c for c, _ in top_cats)}。"
        sorted_by_score = sorted(analyzed, key=lambda s: s.priority_score, reverse=True)
        highlights = [
            f"[{s.priority_score:.0f}分] {s.summary}"
            for s in sorted_by_score[:5]
        ]

    return WeeklyReport(
        week_start=week_start,
        week_end=week_end,
        suggestions=analyzed,
        overall_summary=overall,
        highlights=highlights,
        stats=stats,
    )
