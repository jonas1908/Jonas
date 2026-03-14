"""
配置与环境变量读取模块。

负责从 .env 和系统环境中读取：
- Discord、OpenAI、飞书的密钥
- 频道 / 表格 / 群聊 ID
- 其它通用配置（时区等）
"""

from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"

def load_env() -> None:
    if ENV_PATH.exists():
        load_dotenv(ENV_PATH)

@dataclass
class DiscordConfig:
    bot_token: str
    guild_id: int
    channel_id: int

@dataclass
class OpenAIConfig:
    api_key: str
    model: str = "gpt-4.1-mini"
    base_url: str = ""

@dataclass
class FeishuConfig:
    app_id: str
    app_secret: str
    bitable_app_token: str
    bitable_table_id: str
    report_chat_id: str

@dataclass
class AppConfig:
    discord: DiscordConfig
    openai: OpenAIConfig
    feishu: FeishuConfig
    timezone: str = "Asia/Shanghai"

def get_config() -> AppConfig:
    load_env()

    discord = DiscordConfig(
        bot_token=os.getenv("DISCORD_BOT_TOKEN", ""),
        guild_id=int(os.getenv("DISCORD_GUILD_ID", "0") or 0),
        channel_id=int(os.getenv("DISCORD_CHANNEL_ID", "0") or 0),
    )

    openai_cfg = OpenAIConfig(
        api_key=os.getenv("OPENAI_API_KEY", ""),
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        base_url=os.getenv("AI_BASE_URL", ""),
    )

    feishu = FeishuConfig(
        app_id=os.getenv("FEISHU_APP_ID", ""),
        app_secret=os.getenv("FEISHU_APP_SECRET", ""),
        bitable_app_token=os.getenv("FEISHU_BITABLE_APP_TOKEN", ""),
        bitable_table_id=os.getenv("FEISHU_BITABLE_TABLE_ID", ""),
        report_chat_id=os.getenv("FEISHU_REPORT_CHAT_ID", ""),
    )

    timezone = os.getenv("TIMEZONE", "Asia/Shanghai")

    return AppConfig(
        discord=discord,
        openai=openai_cfg,
        feishu=feishu,
        timezone=timezone,
    )