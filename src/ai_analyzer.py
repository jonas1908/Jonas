"""AI 分析：合并相似帖子，生成 Top10"""

import json
import re
from openai import OpenAI
from .config import AppConfig
from .models import TopSuggestion, WeeklyReport

SYSTEM_PROMPT = """你是游戏社区分析师。我会发给你一批Discord论坛帖子（标题+内容+热度）。
请你：
1. 将相似/重复的建议合并为同一组
2. 按热度总和排序，取Top10
3. 对每组给出：标题（简短）、描述概括（1-2句话）、情绪分（1-10，10=极度愤怒）、包含的帖子编号
用JSON数组回复，格式：
[{"title":"简短标题","description":"描述概括","anger_score":8.5,"post_ids":[0,3,7]}]
按热度从高到低排列，最多10条。只输出JSON不要其他说明。"""

def _simple_rank(posts):
    result = []
    for i in range(min(10, len(posts))):
        p = posts[i]
        parts = p.content.split("\n", 1)
        title = parts[0].replace("【", "").replace("】", "")
        desc = parts[1][:100] if len(parts) > 1 else ""
        result.append(TopSuggestion(rank=i + 1, title=title, description=desc, heat_score=p.heat_score, anger_score=5.0, similar_count=1))
    return result

def analyze_and_rank(config, posts):
    if not posts:
        print("[AI] 没有帖子，跳过分析")
        return []
    top_posts = posts[:50]
    print("[AI] 准备分析 " + str(len(top_posts)) + " 个帖子...")
    if not config.openai.api_key:
        print("[AI] 没有API Key，使用简单排序")
        return _simple_rank(top_posts)
    user_content = ""
    for i in range(len(top_posts)):
        p = top_posts[i]
        user_content = user_content + "[" + str(i) + "] 热度:" + str(p.heat_score) + " | " + p.content[:200] + "\n\n"
    try:
        client = OpenAI(api_key=config.openai.api_key)
        print("[AI] 调用 OpenAI 分析中...")
        resp = client.chat.completions.create(model=config.openai.model, messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_content}], timeout=120)
        raw = (resp.choices[0].message.content or "").strip()
        print("[AI] 返回长度: " + str(len(raw)))
        if raw.startswith("```"):
            raw = re.sub(r"^```\w*\n?", "", raw)
            raw = re.sub(r"\n?```\s*$", "", raw)
        parsed = json.loads(raw)
        if not isinstance(parsed, list):
            parsed = parsed.get("results", parsed.get("data", []))
        print("[AI] 解析到 " + str(len(parsed)) + " 组")
        result = []
        for idx in range(min(10, len(parsed))):
            item = parsed[idx]
            post_ids = item.get("post_ids", [])
            total_heat = 0
            for pid in post_ids:
                if isinstance(pid, int) and pid < len(top_posts):
                    total_heat = total_heat + top_posts[pid].heat_score
            if total_heat == 0:
                total_heat = top_posts[idx].heat_score if idx < len(top_posts) else 0
            result.append(TopSuggestion(rank=idx + 1, title=str(item.get("title", "未知")), description=str(item.get("description", "")), heat_score=total_heat, anger_score=float(item.get("anger_score", 5.0)), similar_count=len(post_ids)))
        result.sort(key=lambda x: x.heat_score, reverse=True)
        for i in range(len(result)):
            result[i].rank = i + 1
        print("[AI] Top10 完成")
        return result
    except Exception as e:
        print("[AI] 出错: " + str(e) + "，使用简单排序")
        return _simple_rank(top_posts)

def build_weekly_report(config, top_suggestions, week_start, week_end, total_posts):
    return WeeklyReport(week_start=week_start, week_end=week_end, top_suggestions=top_suggestions, total_posts=total_posts)