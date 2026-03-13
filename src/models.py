"""
统一定义项目中用到的数据结构，方便在不同模块之间传递。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class RawDiscordMessage:
    """原始的 Discord 消息（建议帖）。"""

    message_id: int
    author_name: str
    author_id: int
    content: str
    created_at: datetime
    jump_url: Optional[str] = None


@dataclass
class AnalyzedSuggestion:
    """AI 分析后的单条建议结果。"""

    source: RawDiscordMessage
    category: str
    subcategory: Optional[str]
    summary: str
    detail: str
    priority_score: float
    sentiment: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class WeeklyReport:
    """一整周的汇总信息，用于生成周报卡片。"""

    week_start: datetime
    week_end: datetime
    suggestions: List[AnalyzedSuggestion]
    overall_summary: str
    highlights: List[str] = field(default_factory=list)
    stats: dict = field(default_factory=dict)

