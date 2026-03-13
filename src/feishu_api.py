"""
飞书 OpenAPI 的最小封装（不依赖 lark-oapi SDK）。

当前用途：
- 用 App ID / App Secret 换取 tenant_access_token
- 查询机器人所在的群列表，获取 chat_id
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx
import json


FEISHU_BASE_URL = "https://open.feishu.cn"


class FeishuAPIError(RuntimeError):
    pass


@dataclass
class FeishuTenantToken:
    token: str
    expire: int


def _raise_if_feishu_error(data: Dict[str, Any], context: str) -> None:
    code = data.get("code")
    if code not in (0, "0", None):
        msg = data.get("msg") or data.get("message") or str(data)
        raise FeishuAPIError(f"{context} failed: code={code}, msg={msg}")


def get_tenant_access_token(app_id: str, app_secret: str) -> FeishuTenantToken:
    """
    使用 App ID / App Secret 获取 tenant_access_token。
    文档关键词：tenant_access_token / internal app.
    """
    url = f"{FEISHU_BASE_URL}/open-apis/auth/v3/tenant_access_token/internal"
    payload = {"app_id": app_id, "app_secret": app_secret}

    with httpx.Client(timeout=30) as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()

    _raise_if_feishu_error(data, "get_tenant_access_token")

    token = data.get("tenant_access_token") or ""
    expire = int(data.get("expire") or 0)
    if not token:
        raise FeishuAPIError("get_tenant_access_token failed: missing tenant_access_token")
    return FeishuTenantToken(token=token, expire=expire)


def list_bot_chats(
    tenant_access_token: str,
    page_size: int = 50,
    page_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    获取用户或机器人所在的群列表（IM Chats）。

    返回原始 JSON，包含：
    - data.items: 群列表（每项包含 chat_id / name 等）
    - data.page_token / data.has_more: 翻页信息
    """
    url = f"{FEISHU_BASE_URL}/open-apis/im/v1/chats"
    # Feishu OpenAPI 的部分 IM 接口要求 user_id_type 参数，否则可能返回 400。
    params: Dict[str, Any] = {"page_size": page_size, "user_id_type": "open_id"}
    if page_token:
        params["page_token"] = page_token

    headers = {"Authorization": f"Bearer {tenant_access_token}"}

    with httpx.Client(timeout=30) as client:
        resp = client.get(url, params=params, headers=headers)
        # 400/403 等错误时，尽量把飞书返回的 JSON 打出来，方便你补权限/参数。
        try:
            data = resp.json()
        except Exception:
            resp.raise_for_status()
            raise
        if resp.status_code >= 400:
            _raise_if_feishu_error(data, "list_bot_chats")
            raise FeishuAPIError(f"list_bot_chats http error: status={resp.status_code}, body={data}")

    _raise_if_feishu_error(data, "list_bot_chats")
    return data


def send_text_message_to_chat(
    tenant_access_token: str,
    chat_id: str,
    text: str,
) -> Dict[str, Any]:
    """
    以“机器人”身份向指定群 chat_id 发送文本消息。

    需要应用具备 IM 发消息权限，并且机器人在该群内。
    """
    url = f"{FEISHU_BASE_URL}/open-apis/im/v1/messages"
    params = {"receive_id_type": "chat_id"}
    headers = {"Authorization": f"Bearer {tenant_access_token}"}
    payload = {
        "receive_id": chat_id,
        "msg_type": "text",
        # 飞书接口要求 content 为 JSON 字符串，而不是对象
        "content": json.dumps({"text": text}, ensure_ascii=False),
    }

    with httpx.Client(timeout=30) as client:
        resp = client.post(url, params=params, headers=headers, json=payload)
        try:
            data = resp.json()
        except Exception:
            resp.raise_for_status()
            raise
        if resp.status_code >= 400:
            _raise_if_feishu_error(data, "send_text_message_to_chat")
            raise FeishuAPIError(
                f"send_text_message_to_chat http error: status={resp.status_code}, body={data}"
            )

    _raise_if_feishu_error(data, "send_text_message_to_chat")
    return data

