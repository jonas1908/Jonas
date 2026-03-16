"""AI 分析：合并相似帖子，生成 Top10"""

import json
import re
import traceback
from openai import OpenAI
from .models import TopSuggestion, WeeklyReport

SYSTEM_PROMPT = """你是游戏社区分析师。我会发给你一批Discord论坛帖子（编号、标题、内容、热度）。
请你：
1. 将相似/重复的建议合并为同一组
2. 按热度总和排序，取Top10
3. 对每组分析：
   - title: 简短中文标题
   - description: 分析玩家的核心诉求和目的（不要引用原话，用中文总结玩家到底想要什么、为什么不满）
   - anger_score: 情绪分1-10，根据帖子用词和语气判断：
     1-3=平和友好 4-6=有些不满但理性 7-8=明显愤怒言辞激烈 9-10=极度愤怒威胁差评退游
   - post_ids: 包含的帖子编号数组

用JSON数组回复：
[{"title":"标题","description":"玩家核心诉求分析","anger_score":7.5,"post_ids":[0,3]}]
最多10条，只输出JSON。"""

def _simple_rank(posts):
    result = []
    for i in range(min(10, len(posts))):
        p = posts[i]
        parts = p.content.split("\n", 1)
        title = parts[0].replace("【", "").replace("】", "")
        desc = parts[1][:100] if len(parts) > 1 else ""
        result.append(TopSuggestion(rank=i + 1, title=title, description=desc, heat_score=p.heat_score, anger_score=5.0, similar_count=1, jump_url=p.jump_url))
    return result

def analyze_and_rank(config, posts):
    if not posts:
        print("[AI] 没有帖子，跳过")
        return []
    top_posts = posts[:50]
    print("[AI] 准备分析 " + str(len(top_posts)) + " 个帖子...")
    if not config.openai.api_key:
        print("[AI] 没有API Key，用简单排序")
        return _simple_rank(top_posts)
    user_content = ""
    for i in range(len(top_posts)):
        p = top_posts[i]
        user_content = user_content + "[" + str(i) + "] 热度:" + str(p.heat_score) + " | " + p.content[:300] + "\n\n"
    print("[AI] 内容长度: " + str(len(user_content)))
    print("[AI] 模型: " + str(config.openai.model))
    print("[AI] API Key前8位: " + config.openai.api_key[:8] + "...")
    try:
        client = OpenAI(api_key=config.openai.api_key)
        print("[AI] 调用 OpenAI...")
        resp = client.chat.completions.create(model=config.openai.model, messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_content}], timeout=120)
        raw = (resp.choices[0].message.content or "").strip()
        print("[AI] 返回长度: " + str(len(raw)))
        print("[AI] 前500字: " + raw[:500])
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
            best_url = ""
            best_heat = 0
            for pid in post_ids:
                if isinstance(pid, int) and pid < len(top_posts):
                    total_heat = total_heat + top_posts[pid].heat_score
                    if top_posts[pid].heat_score > best_heat:
                        best_heat = top_posts[pid].heat_score
                        best_url = top_posts[pid].jump_url
            if total_heat == 0 and idx < len(top_posts):
                total_heat = top_posts[idx].heat_score
                best_url = top_posts[idx].jump_url
            if not best_url and idx < len(top_posts):
                best_url = top_posts[idx].jump_url
            anger = float(item.get("anger_score", 5.0))
            similar = max(1, len(post_ids))
            title = str(item.get("title", "未知"))
            desc = str(item.get("description", ""))
            print("[AI] " + str(idx) + ": " + title + " 热度:" + str(total_heat) + " 情绪:" + str(anger) + " 数:" + str(similar))
            result.append(TopSuggestion(rank=idx + 1, title=title, description=desc, heat_score=total_heat, anger_score=anger, similar_count=similar, jump_url=best_url))
        result.sort(key=lambda x: x.heat_score, reverse=True)
        for i in range(len(result)):
            result[i].rank = i + 1
        print("[AI] Top10 完成")
        return result
    except Exception as e:
        print("[AI] ❌ 出错: " + str(e))
        traceback.print_exc()
        print("[AI] 用简单排序兜底")
        return _simple_rank(top_posts)

def build_weekly_report(config, top_suggestions, week_start, week_end, total_posts):
    return WeeklyReport(week_start=week_start, week_end=week_end, top_suggestions=top_suggestions, total_posts=total_posts)