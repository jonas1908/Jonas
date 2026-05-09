"""配置与环境变量读取"""

from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"

def load_env():
    if ENV_PATH.exists():
        load_dotenv(ENV_PATH)

@dataclass
class ChannelConfig:
    channel_id: int
    label: str  # 频道标签，用于报告标题区分

@dataclass
class DiscordConfig:
    bot_token: str
    guild_id: int
    channel_id: int  # 保留兼容
    channels: List[ChannelConfig] = field(default_factory=list)

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

def get_config():
    load_env()

    # 解析多频道配置
    channels = []
    # 频道1
    ch1_id = os.getenv("DISCORD_CHANNEL_ID", "0") or "0"
    ch1_label = os.getenv("DISCORD_CHANNEL_LABEL", "频道1")
    if int(ch1_id) != 0:
        channels.append(ChannelConfig(channel_id=int(ch1_id), label=ch1_label))
    # 频道2
    ch2_id = os.getenv("DISCORD_CHANNEL_ID_2", "0") or "0"
    ch2_label = os.getenv("DISCORD_CHANNEL_LABEL_2", "频道2")
    if int(ch2_id) != 0:
        channels.append(ChannelConfig(channel_id=int(ch2_id), label=ch2_label))

    discord = DiscordConfig(
        bot_token=os.getenv("DISCORD_BOT_TOKEN", ""),
        guild_id=int(os.getenv("DISCORD_GUILD_ID", "0") or 0),
        channel_id=int(ch1_id),
        channels=channels
    )
    openai_cfg = OpenAIConfig(
        api_key=os.getenv("OPENAI_API_KEY", ""),
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        base_url=os.getenv("AI_BASE_URL", "")
    )
    feishu = FeishuConfig(
        app_id=os.getenv("FEISHU_APP_ID", ""),
        app_secret=os.getenv("FEISHU_APP_SECRET", ""),
        bitable_app_token=os.getenv("FEISHU_BITABLE_APP_TOKEN", ""),
        bitable_table_id=os.getenv("FEISHU_BITABLE_TABLE_ID", ""),
        report_chat_id=os.getenv("FEISHU_REPORT_CHAT_ID", "")
    )
    timezone = os.getenv("TIMEZONE", "Asia/Shanghai")
    return AppConfig(discord=discord, openai=openai_cfg, feishu=feishu, timezone=timezone)
