"""
列出“机器人所在的群”，用于获取 chat_id。

使用方式（本地终端）：
  export FEISHU_APP_ID="..."
  export FEISHU_APP_SECRET="..."
  python -m src.tools.feishu_list_chats
"""

from __future__ import annotations

import os

from ..feishu_api import get_tenant_access_token, list_bot_chats, FeishuAPIError


def main() -> None:
    app_id = os.getenv("FEISHU_APP_ID", "").strip()
    app_secret = os.getenv("FEISHU_APP_SECRET", "").strip()

    if not app_id or not app_secret:
        raise SystemExit(
            "缺少环境变量：FEISHU_APP_ID / FEISHU_APP_SECRET。\n"
            "请先在终端里执行：\n"
            '  export FEISHU_APP_ID="在这里填你的AppID"\n'
            '  export FEISHU_APP_SECRET="在这里填你的AppSecret"\n'
        )

    try:
        token = get_tenant_access_token(app_id=app_id, app_secret=app_secret)
        print(f"tenant_access_token 获取成功（expire={token.expire}s）")

        page_token = None
        idx = 1
        while True:
            data = list_bot_chats(tenant_access_token=token.token, page_size=50, page_token=page_token)
            items = (data.get("data") or {}).get("items") or []
            if not items and idx == 1:
                print("没有查到任何群。请确认：机器人已经被添加进群，并且应用已发布且具备所需权限。")
                return

            for item in items:
                chat_id = item.get("chat_id", "")
                name = item.get("name", "")
                description = item.get("description", "")
                print(f"{idx}. name={name!r} chat_id={chat_id} desc={description!r}")
                idx += 1

            has_more = bool((data.get("data") or {}).get("has_more"))
            page_token = (data.get("data") or {}).get("page_token")
            if not has_more:
                break

    except FeishuAPIError as e:
        raise SystemExit(f"飞书接口调用失败：{e}")


if __name__ == "__main__":
    main()

