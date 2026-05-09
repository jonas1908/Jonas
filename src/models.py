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
    member_count: int = 0  # 参与人数

@dataclass
class TopSuggestion:
    rank: int
    title: str
    description: str
    heat_score: int
    anger_score: float
    similar_count: int
    jump_url: str = ""
    module_category: str = ""  # 模块分类
    sub_category: str = ""  # 二级分类
    member_count: int = 0  # 参与人数
    message_count: int = 0  # 回复数
    created_at: str = ""  # 帖子日期
    original_content: str = ""  # 玩家原始内容（具体建议）

@dataclass
class WeeklyReport:
    week_start: object
    week_end: object
    top_suggestions: list
    total_posts: int
