"""数据结构定义"""

from dataclasses import dataclass

@dataclass
class RawDiscordMessage:
    message_id: int
    author_name: str
    author_id: int
    content: str
    created_at: str
    jump_url: str = ""
    message_count: int = 0
    reaction_count: int = 0
    heat_score: int = 0

@dataclass
class TopSuggestion:
    rank: int
    title: str
    description: str
    heat_score: int
    anger_score: float
    similar_count: int
    jump_url: str = ""

@dataclass
class WeeklyReport:
    week_start: object
    week_end: object
    top_suggestions: list
    total_posts: int