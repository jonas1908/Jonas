"""写入飞书多维表格（支持更新已有记录）"""

import requests
from .feishu_api import get_tenant_access_token

def write_to_bitable(config, suggestions):
    """将 Top 建议列表写入飞书多维表格（已存在则更新，不存在则新增）"""
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

    base_url = "https://open.feishu.cn/open-apis/bitable/v1/apps/" + bitable_app_token + "/tables/" + bitable_table_id

    # 第1步：获取表格中已有记录，建立 帖子链接 → record_id 的映射
    existing_map = _get_existing_records(base_url, headers)
    print("[多维表格] 已有记录数: " + str(len(existing_map)))

    # 第2步：分类——哪些要更新，哪些要新增
    to_create = []
    to_update = []

    for s in suggestions:
        fields = _build_fields(s)
        jump_url = s.jump_url or ""

        if jump_url and jump_url in existing_map:
            # 已存在，更新
            record_id = existing_map[jump_url]
            to_update.append({"record_id": record_id, "fields": fields})
        else:
            # 不存在，新增
            to_create.append({"fields": fields})

    print("[多维表格] 需要新增: " + str(len(to_create)) + " 条")
    print("[多维表格] 需要更新: " + str(len(to_update)) + " 条")

    # 第3步：执行新增
    if to_create:
        _batch_create(base_url, headers, to_create)

    # 第4步：执行更新
    if to_update:
        _batch_update(base_url, headers, to_update)

    print("[多维表格] 全部完成！")

def _build_fields(s):
    """构建一条记录的字段"""
    date_ms = _parse_date_to_ms(s.created_at)
    fields = {
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
    return fields

def _get_existing_records(base_url, headers):
    """获取表格所有记录，返回 {帖子链接URL: record_id} 映射"""
    existing_map = {}
    page_token = ""
    has_more = True

    while has_more:
        url = base_url + "/records?page_size=500"
        if page_token:
            url = url + "&page_token=" + page_token

        try:
            resp = requests.get(url, headers=headers, timeout=30)
            result = resp.json()
            if result.get("code", -1) != 0:
                print("[多维表格] 查询已有记录失败: " + str(result.get("msg", "")))
                break

            data = result.get("data", {})
            items = data.get("items", [])

            for item in items:
                record_id = item.get("record_id", "")
                fields = item.get("fields", {})
                # 帖子链接字段可能是对象格式 {"link": "xxx", "text": "xxx"}
                link_field = fields.get("帖子链接", "")
                link_url = ""
                if isinstance(link_field, dict):
                    link_url = link_field.get("link", "")
                elif isinstance(link_field, str):
                    link_url = link_field

                if link_url and record_id:
                    existing_map[link_url] = record_id

            has_more = data.get("has_more", False)
            page_token = data.get("page_token", "")

        except Exception as e:
            print("[多维表格] 查询异常: " + str(e))
            break

    return existing_map

def _batch_create(base_url, headers, records):
    """批量新增记录"""
    url = base_url + "/records/batch_create"
    body = {"records": records}
    try:
        resp = requests.post(url, headers=headers, json=body, timeout=30)
        result = resp.json()
        code = result.get("code", -1)
        if code == 0:
            print("[多维表格] ✅ 新增成功！" + str(len(records)) + " 条")
        else:
            print("[多维表格] ❌ 新增失败！code=" + str(code) + " msg=" + str(result.get("msg", "")))
            print("[多维表格] 返回: " + str(result)[:500])
    except Exception as e:
        print("[多维表格] ❌ 新增异常: " + str(e))

def _batch_update(base_url, headers, records):
    """批量更新记录"""
    url = base_url + "/records/batch_update"
    body = {"records": records}
    try:
        resp = requests.post(url, headers=headers, json=body, timeout=30)
        result = resp.json()
        code = result.get("code", -1)
        if code == 0:
            print("[多维表格] ✅ 更新成功！" + str(len(records)) + " 条")
        else:
            print("[多维表格] ❌ 更新失败！code=" + str(code) + " msg=" + str(result.get("msg", "")))
            print("[多维表格] 返回: " + str(result)[:500])
    except Exception as e:
        print("[多维表格] ❌ 更新异常: " + str(e))

def _parse_date_to_ms(date_str):
    """将日期字符串转为毫秒时间戳（飞书日期字段需要）"""
    try:
        from datetime import datetime, timezone
        if "+" in date_str or "Z" in date_str:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        else:
            dt = datetime.fromisoformat(date_str)
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1000)
    except Exception as e:
        print("[多维表格] 日期解析失败: " + str(date_str) + " 错误: " + str(e))
        from datetime import datetime, timezone
        return int(datetime.now(timezone.utc).timestamp() * 1000)

def _build_link(url):
    """构建飞书链接字段格式"""
    if not url:
        return ""
    return {"link": url, "text": "查看帖子"}
