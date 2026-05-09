"""写入飞书多维表格"""

import requests
from .feishu_api import get_tenant_access_token

def write_to_bitable(config, suggestions):
    """将 Top 建议列表写入飞书多维表格"""
    app_id = config.feishu.app_id
    app_secret = config.feishu.app_secret
    bitable_app_token = config.feishu.bitable_app_token
    bitable_table_id = config.feishu.bitable_table_id

    if not bitable_app_token or not bitable_table_id:
        print("[多维表格] 缺少 bitable_app_token 或 bitable_table_id，跳过写入。")
        return

    if not suggestions:
        print("[多维表格] 没有建议数据，跳过写入。")
        return

    token = get_tenant_access_token(app_id=app_id, app_secret=app_secret)
    headers = {
        "Authorization": "Bearer " + token.token,
        "Content-Type": "application/json"
    }

    url = "https://open.feishu.cn/open-apis/bitable/v1/apps/" + bitable_app_token + "/tables/" + bitable_table_id + "/records/batch_create"

    records = []
    for s in suggestions:
        # 解析日期为时间戳（毫秒）
        date_ms = _parse_date_to_ms(s.created_at)

        record = {
            "fields": {
                "日期": date_ms,
                "AI短标题": s.title,
                "模块分类": s.module_category,
                "二级分类": s.sub_category,
                "热度分": s.heat_score,
                "情绪分": s.anger_score,
                "参与人数": s.member_count,
                "回复数": s.message_count,
                "AI核心总结": s.description,
                "具体建议": s.original_content[:2000] if s.original_content else "",
                "帖子链接": _build_link(s.jump_url)
            }
        }
        records.append(record)

    print("[多维表格] 准备写入 " + str(len(records)) + " 条记录")

    # 飞书batch_create最多500条，我们这里最多10条，不用分批
    body = {"records": records}

    try:
        resp = requests.post(url, headers=headers, json=body, timeout=30)
        result = resp.json()
        code = result.get("code", -1)
        if code == 0:
            print("[多维表格] ✅ 写入成功！共 " + str(len(records)) + " 条")
        else:
            print("[多维表格] ❌ 写入失败！code=" + str(code) + " msg=" + str(result.get("msg", "")))
            print("[多维表格] 返回: " + str(result)[:500])
    except Exception as e:
        print("[多维表格] ❌ 请求异常: " + str(e))

def _parse_date_to_ms(date_str):
    """将日期字符串转为毫秒时间戳（飞书日期字段需要）"""
    try:
        from datetime import datetime, timezone
        # created_at 格式类似 "2026-05-04 12:00:00+00:00"
        if "+" in date_str or "Z" in date_str:
            # 带时区
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        else:
            dt = datetime.fromisoformat(date_str)
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1000)
    except Exception as e:
        print("[多维表格] 日期解析失败: " + str(date_str) + " 错误: " + str(e))
        # 返回当前时间
        from datetime import datetime, timezone
        return int(datetime.now(timezone.utc).timestamp() * 1000)

def _build_link(url):
    """构建飞书链接字段格式"""
    if not url:
        return ""
    # 飞书链接字段可以直接用字符串，也可以用对象格式
    # 用对象格式更规范
    return {"link": url, "text": "查看帖子"}
