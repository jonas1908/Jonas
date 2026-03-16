"""AI 分析：合并相似帖子，生成 Top10"""

import json
import re
import traceback
from openai import OpenAI
from .models import TopSuggestion, WeeklyReport

SYSTEM_PROMPT = """你是一个游戏社区分析师。我会发给你Discord论坛帖子列表。

你的任务：
1. 将相似或重复的建议合并
2. 按热度排序取Top10
3. 对每组输出：
   - title: 简短中文标题（不超过15字）
   - description: 用中文分析玩家的核心诉求，不要引用原话，而是总结他们想要达成什么目的、为什么不满、期望游戏做出什么改变（1-2句话）
   - anger_score: 根据帖子的用词和语气打情绪分（浮点数）：
     1.0-3.0 = 心态平和，友好建议
     3.1-5.0 = 略有不满但表达理性
     5.1-7.0 = 比较不满，言辞较激烈
     7.1-9.0 = 非常愤怒，有攻击性言辞
     9.1-10.0 = 极度愤怒，威胁退游或差评
   - post_ids: 属于这组的帖子编号数组

严格输出JSON数组，不要任何其他文字：
[{"title":"标题","description":"诉求分析","anger_score":6.5,"post_ids":[0,3]}]"""

def _simple_rank(posts):
    print("[AI] 使用简单排序（无AI分析）")
    result = []
    for i in range(min(10, len(posts))):
        p = posts[i]
        parts = p.content.split("\n", 1)
        title = parts[0].replace("【", "").replace("】", "")
        desc = parts[1][:100] if len(parts) > 1 else ""
        result.append(TopSuggestion(rank=i + 1, title=title, description=desc, heat_score=p.heat_score, anger_score=0.0, similar_count=1, jump_url=p.jump_url))
    return result

def analyze_and_rank(config, posts):
    if not posts:
        print("[AI] 没有帖子")
        return []
    top_posts = posts[:50]
    print("[AI] ========== 开始AI分析 ==========")
    print("[AI] 帖子数: " + str(len(top_posts)))
    api_key = config.openai.api_key
    model = config.openai.model
    print("[AI] API Key: " + str(api_key[:8]) + "..." if api_key else "[AI] API Key: 空!")
    print("[AI] Model: " + str(model))
    if not api_key:
        print("[AI] ❌ 没有API Key!")
        return _simple_rank(top_posts)
    user_content = ""
    for i in range(len(top_posts)):
        p = top_posts[i]
        user_content = user_content + "[" + str(i) + "] 热度:" + str(p.heat_score) + " | " + p.content[:300] + "\n\n"
    print("[AI] 发送内容长度: " + str(len(user_content)))
    print("[AI] 内容预览: " + user_content[:200])
    print("[AI] 正在调用OpenAI...")
    raw = ""
    try:
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(model=model, messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_content}], timeout=120)
        raw = (resp.choices[0].message.content or "").strip()
        print("[AI] ✅ OpenAI返回成功")
        print("[AI] 返回长度: " + str(len(raw)))
        print("[AI] 完整返回内容:")
        print(raw)
    except Exception as e:
        print("[AI] ❌ OpenAI调用失败!")
        print("[AI] 错误类型: " + str(type(e).__name__))
        print("[AI] 错误信息: " + str(e))
        traceback.print_exc()
        return _simple_rank(top_posts)
    print("[AI] 开始解析JSON...")
    try:
        clean = raw
        if clean.startswith("```"):
            clean = re.sub(r"^```\w*\n?", "", clean)
            clean = re.sub(r"\n?```\s*$", "", clean)
        parsed = json.loads(clean)
        if not isinstance(parsed, list):
            parsed = parsed.get("results", parsed.get("data", []))
        print("[AI] ✅ JSON解析成功，" + str(len(parsed)) + " 组")
    except Exception as e:
        print("[AI] ❌ JSON解析失败: " + str(e))
        print("[AI] 原始内容: " + raw[:500])
        return _simple_rank(top_posts)
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
        print("[AI] 第" + str(idx + 1) + "组: " + title + " | 热度:" + str(total_heat) + " | 情绪:" + str(anger) + " | 建议数:" + str(similar))
        print("[AI] 描述: " + desc[:100])
        result.append(TopSuggestion(rank=idx + 1, title=title, description=desc, heat_score=total_heat, anger_score=anger, similar_count=similar, jump_url=best_url))
    result.sort(key=lambda x: x.heat_score, reverse=True)
    for i in range(len(result)):
        result[i].rank = i + 1
    print("[AI] ========== AI分析完成 ==========")
    return result

def build_weekly_report(config, top_suggestions, week_start, week_end, total_posts):
    return WeeklyReport(week_start=week_start, week_end=week_end, top_suggestions=top_suggestions, total_posts=total_posts)