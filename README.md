# Discord 飞书周报工具

每周从 Discord 指定频道拉取玩家建议 → 用 OpenAI 分析（分类、总结、打分）→ 生成周报发到飞书群。

## 流程

1. **Discord**：Bot 从指定服务器/频道拉取本周内的消息  
2. **AI**：OpenAI 对每条做分类、总结、优先级打分  
3. **飞书**：应用机器人把周报（概览 + TOP5 + 分类统计）发到指定群

## 本地运行

```bash
cd "/Users/zhangyong/Desktop/周报工具"
source .venv/bin/activate

# 设置环境变量（或使用 .env）
export FEISHU_APP_ID="..."
export FEISHU_APP_SECRET="..."
export FEISHU_REPORT_CHAT_ID="oc_..."
export DISCORD_BOT_TOKEN="..."
export DISCORD_GUILD_ID="123456789"
export DISCORD_CHANNEL_ID="123456789"
export OPENAI_API_KEY="sk-..."
# 可选：OPENAI_MODEL=gpt-4.1-mini

python -m src.main
```

## GitHub Actions 每周定时

- 工作流文件：`.github/workflows/weekly-report.yml`  
- 默认：每周一北京时间 10:00 执行  
- 可在仓库 **Actions** 里 **Run workflow** 手动触发测试  

### 需要在仓库里配置的 Secrets

| 名称 | 说明 |
|------|------|
| `FEISHU_APP_ID` | 飞书应用 App ID |
| `FEISHU_APP_SECRET` | 飞书应用 App Secret |
| `FEISHU_REPORT_CHAT_ID` | 发周报的飞书群 chat_id（如 `oc_xxx`） |
| `DISCORD_BOT_TOKEN` | Discord Bot Token |
| `DISCORD_GUILD_ID` | Discord 服务器 ID |
| `DISCORD_CHANNEL_ID` | 要收集建议的 Discord 频道 ID |
| `OPENAI_API_KEY` | OpenAI API Key |
| `OPENAI_MODEL` | 可选，默认 `gpt-4.1-mini` |

## Discord Bot 准备

1. [Discord Developer Portal](https://discord.com/developers/applications) 创建应用，在 **Bot** 里添加 Bot，复制 **Token**  
2. 在 **Bot** 里开启 **Message Content Intent**（否则读不到消息内容）  
3. 把 Bot 邀请进服务器，并赋予「查看频道」「读取消息历史」权限  
4. 服务器 ID、频道 ID：在 Discord 里开启「开发者模式」，右键服务器/频道即可「复制 ID」

## 飞书

- 自建应用需开启「机器人」能力  
- 权限：发消息、获取群信息等（见飞书开放平台文档）  
- 获取群 `chat_id`：可运行 `python -m src.tools.feishu_list_chats`（需先设置 `FEISHU_APP_ID`、`FEISHU_APP_SECRET`）

## 目录结构

- `src/main.py`：入口，串联 Discord → AI → 飞书  
- `src/discord_client.py`：拉取 Discord 频道消息  
- `src/ai_analyzer.py`：OpenAI 分析 + 周报汇总  
- `src/feishu_client.py`：飞书发周报  
- `src/feishu_api.py`：飞书 OpenAPI（token、发消息）  
- `src/tools/feishu_list_chats.py`：列出机器人所在群，查 chat_id  
