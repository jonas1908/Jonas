"""AI 分析模块：批量分析 + 生成周报"""

import json
import re
import time
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List

from openai import OpenAI

from .config import AppConfig
from .models import RawDiscordMessage, AnalyzedSuggestion, WeeklyReport

BATCH_SYSTEM_PROMPT = """你是一个游戏社区运营助手。用户会发来多条 Discord 玩家消息，请对每条做分析。

用 JSON 数组格式回复，每个元素包含：
- id: 消息编号（和输入中的编号对应）
- category: 分类（玩法/平衡性/UI/剧情/活动/Bug/闲聊/其他）
- summary: 一句话总结（20字以内）
- priority_score: 1-10整数（10最高，闲聊给1-2分）
- sentiment: 正面/中性/负面
- tags: 标签数组，最多3个

只输出 JSON 数组，不要其他说明。"""

def _parse_batch_response(text: str) -> List[Dict[str, Any]]:
    """解析批量分析的 JSON 数组"""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```\s*$", "", text)
    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
        return []
    except json.JSONDecodeError:
        return []

def _filter_messages(messages: List[RawDiscordMessage]) -> List[RawDiscordMessage]:
    """过滤掉明显无意义的消息"""
    filtered = []
    for msg in messages:
        content = msg.content.strip()
        # 跳过太短的、纯图片的、机器人的
        if content == "[图片/附件]":
            continue
        if len(content) < 5:
            continue
        filtered.append(msg)
    print(f"[AI] 过滤后剩余 {len(filtered)} 条（原 {len(messages)} 条）")
    return filtered

def analyze_batch_suggestions(
    config: AppConfig,
    messages: List[RawDiscordMessage],
) -> List[AnalyzedSuggestion]:
    """批量分析：每 20 条一组发给 OpenAI"""
    if not messages:
        return []

    # 先过滤无意义消息
    messages = _filter_messages(messages)
    if not messages:
        return []

    if not config.openai.api_key:
        print("[AI] 没有 OpenAI API Key，跳过分析")
        return [
            AnalyzedSuggestion(
                source=msg,
                category="未分析",
                subcategory=None,
                summary=msg.content[:60],
                detail=msg.content[:200],
                priority_score=5.0,
                sentiment=None,
                tags=[],
            )
            for msg in messages
        ]

    client = OpenAI(api_key=config.openai.api_key)
    result: List[AnalyzedSuggestion] = []
    batch_size = 20
    total_batches = (len(messages) + batch_size - 1) // batch_size

    for batch_idx in range(0, len(messages), batch_size):
        batch = messages[batch_idx:batch_idx + batch_size]
        batch_num = batch_idx // batch_size + 1
        print(f"[AI] 分析第 {batch_num}/{total_batches} 批（{len(batch)} 条）...")

        # 构建批量输入
        user_content = ""
        for i, msg in enumerate(batch):
            user_content += f"[{i}] {msg.author_name}: {msg.content[:200]}\n\n"

        try:
            resp = client.chat.completions.create(
                model=config.openai.model,
                messages=[
                    {"role": "system", "content": BATCH_SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                response_format={"type": "json_object"},
                timeout=60,
            )
            raw = (resp.choices[0].message.content or "").strip()
            # response_format=json_object 可能返回 {"results": [...]}
            parsed = json.loads(raw) if raw else {}
            if isinstance(parsed, dict):
                analyses = parsed.get("results", parsed.get("data", []))
                if not isinstance(analyses, list):
                    analyses = []
            else:
                analyses = parsed if isinstance(parsed, list) else []

            print(f"[AI] 第 {batch_num} 批解析到 {len(analyses)} 条结果")

        except Exception as e:
            print(f"[AI] ❌ 第 {batch_num} 批失败: {e}")
            analyses = []

        # 匹配分析结果到消息
        analyses_map = {}
        for a in analyses:
            if isinstance(a, dict) and "id" in a:
                analyses_map[a["id"]] = a

        for i, msg in enumerate(batch):
            a = analyses_map.get(i, {})
            result.append(
                AnalyzedSuggestion(
                    source=msg,
                    category=str(a.get("category", "其他")),
                    subcategory=None,
                    summary=str(a.get("summary", msg.content[:60])),
                    detail=msg.content[:200],
                    priority_score=min(10, max(1, float(a.get("priority_score", 5)))),
                    sentiment=str(a.get("sentiment", "中性")),
                    tags=[str(t) for t in a.get("tags", [])][:3],
                )
            )

        # 批次间等待，避免限速
        if batch_num < total_batches:
            time.sleep(1)

    print(f"[AI] ✅ 分析完成，共 {len(result)} 条")
    return result

def build_weekly_report(
    config: AppConfig,
    analyzed: List[AnalyzedSuggestion],
    week_start: datetime,
    week_end: datetime,
) -> WeeklyReport:
    """根据分析结果生成周报"""
    overall = "本周暂无玩家建议。"
    highlights: List[str] = []
    stats: Dict[str, Any] = {"total": len(analyzed), "by_category": {}}

    if analyzed:
        # 过滤掉闲聊类
        meaningful = [s for s in analyzed if s.category not in ("闲聊", "其他")]
        by_cat = Counter(s.category for s in analyzed)
        stats["by_category"] = dict(by_cat)
        top_cats = by_cat.most_common(3)
        overall = f"共 {len(analyzed)} 条建议，主要涉及：{', '.join(c for c, _ in top_cats)}。"

        # 按优先级取 Top 5
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