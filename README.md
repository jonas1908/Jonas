**Discord 玩家建议周报机器人**
📌 项目简介
自动从 Discord 论坛频道拉取玩家建议帖子，通过 AI 分析合并相似建议并排名 Top10，每周定时：

将周报发送到飞书群
将详细数据写入飞书多维表格（支持增量更新）

**项目结构**
├── src/
│   ├── __init__.py
│   ├── config.py              # 配置读取
│   ├── models.py              # 数据结构定义
│   ├── discord_client.py      # Discord API 拉取帖子
│   ├── ai_analyzer.py         # AI 分析合并 + 分类
│   ├── feishu_api.py          # 飞书 token 获取
│   ├── feishu_client.py       # 飞书群消息发送
│   ├── bitable_writer.py      # 飞书多维表格写入
│   └── main.py                # 主流程入口
├── .github/
│   └── workflows/
│       └── weekly-report.yml  # GitHub Actions 定时任务
├── requirements.txt
└── README.md


**配置说明**
**GitHub Secrets（必填）**
Secret名称	说明
DISCORD_BOT_TOKEN	Discord 机器人 Token
DISCORD_GUILD_ID	Discord 服务器 ID
DISCORD_CHANNEL_ID	Discord 论坛频道 ID
DISCORD_CHANNEL_LABEL	频道标签名（如 玩家建议），显示在周报标题中
OPENAI_API_KEY	AI API Key
OPENAI_MODEL	AI 模型名（如 gpt-4o）
AI_BASE_URL	AI API 地址（如用中转站则填，否则留空）
FEISHU_APP_ID	飞书应用 App ID
FEISHU_APP_SECRET	飞书应用 App Secret
FEISHU_REPORT_CHAT_ID	飞书群 chat_id（周报发送目标群）
FEISHU_BITABLE_APP_TOKEN	飞书多维表格 app_token
FEISHU_BITABLE_TABLE_ID	飞书多维表格 table_id

**GitHub Secrets（可选，扩展第二频道）**
Secret 名称	说明
DISCORD_CHANNEL_ID_2	第二个 Discord 频道 ID
DISCORD_CHANNEL_LABEL_2	第二个频道标签名
FEISHU_REPORT_CHAT_ID_2	第二个频道对应的飞书群 chat_id

**运行流程**
GitHub Actions 定时触发（每周一次）
        ↓
Discord API 拉取本周所有帖子
        ↓
按热度排序，取前50条发给 AI
        ↓
AI 合并相似建议，生成 Top10
  - 输出：标题、描述、模块分类、二级分类、情绪分
        ↓
发送飞书群周报卡片
        ↓
写入飞书多维表格（增量更新）
  - 帖子链接已存在 → 更新该行
  - 帖子链接不存在 → 新增一行
  - 旧记录未出现 → 保留不动

**多维表格字段说明**
字段名	类型	数据来源
日期	日期	帖子创建时间
AI短标题	文本	AI 生成的简短标题（≤15字）
模块分类	单选	AI 分类（日常活动/商业化/系统功能/活动玩法/养成系统/战斗系统/数值奖励/经济系统/程序优化/赛季玩法/日常玩法/其他）
二级分类	单选	AI 根据内容细分（如匹配系统、翻译系统等）
热度分	数字	帖子回复数累计
情绪分	数字	AI 打分（1.0-10.0）
参与人数	数字	帖子线程参与人数（Discord member_count）
回复数	数字	帖子总消息数（message_count）
AI核心总结	文本	AI 生成的玩家核心诉求分析
具体建议	文本	玩家原始帖子内容
帖子链接	链接	Discord 帖子 URL（也作为去重唯一标识）

**飞书配置前置**
飞书应用权限：需开通 bitable:app（查看、评论、编辑和管理多维表格）
多维表格协作者：打开表格 → 分享 → 搜索机器人应用名 → 添加为「可编辑」
飞书群：机器人需已加入目标飞书群

**注意事项**
多维表格写入仅针对第一个频道（DISCORD_CHANNEL_ID）
写入免费，飞书开放平台不收费
每次跑完最多新增/更新 10 条记录（Top10）
表格数据会持续累积，不会删除历史记录
