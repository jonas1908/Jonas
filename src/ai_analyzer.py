"""AI 分析：合并相似帖子，生成 Top10"""

import json
import re
import time
from openai import OpenAI
from .config import AppConfig
from .models import RawDiscordMessage, TopSuggestion, WeeklyReport

SYSTEM_PROMPT = """你是游戏社区分析师。我会发给你一批 Discord 论坛帖子（标题+内容+热度）。

请你：
1. 将相似/重复的建议合并为同一组
2. 按热度总和排序，取 Top 10
3. 对每组给出：标题（简短）、描述概括（1-2句话）、情绪分（1-10，10=极度愤怒）、包含的帖子编号

用 JSON 数组回复，格式：
[
  {
    "title": "简短标题",
    "description": "描述概括",
    "anger_score": 8.5,
    "post_ids": [0, 3, 7]
  }
]

按热度从高到低排列，最多10条。只输出JSON，不要其他说明。"""

def analyze_and_rank(config, posts):
    if not posts:
        print("[AI] 没有帖子，跳过分析")
        return []
    top_posts = posts[:50]
    print("[AI] 准备分析 " + str(len(top_posts)) + " 个帖子...")
    user_content = ""
    for i in range(len(top_posts)):
        p = top_posts[i]
        user_content = user_content + "[" + str(i) + "] 热度:" + str(p.heat_score) + " | " + p.content[:200] + "\n\n"
    if not config.openai.api_key:
        print("[AI] 没有API Key，使用简单排序")
        result = []
        for i in range(min(10, len(top_posts))):
            p = top_posts[i]
            title = p.content.split("\n")[0].replace("【", "").replace("】", "")
            desc = p.content[len(title) + 2:][:100] if len(p.content) > len(title) + 2 else ""
            item = TopSuggestion(rank=i + 1, title=title, description=desc, heat_score=p.heat_score, anger_score=5.0, similar_count=1)
            result.append(item)
        return result
    try