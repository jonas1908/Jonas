# Discord Bot 准备步骤（详细版）

按下面顺序做，每一步都配有说明和要点的位置。

---

## 一、创建 Discord 应用并拿到 Bot Token

### 1. 打开 Discord 开发者门户

- 用浏览器打开：**https://discord.com/developers/applications**
- 用你的 Discord 账号登录（没有就先注册一个）。

### 2. 新建一个应用（如果还没有）

- 页面右上角有个绿色按钮 **「New Application」**（新建应用），点它。
- 弹出框里让你填应用名称，例如填：`周报机器人`，然后点 **「Create」**（创建）。

### 3. 进入「Bot」页面

- 创建好后会进入这个应用的详情页，左侧有一列菜单：
  - **General Information**（基本信息）
  - **OAuth2**（授权）
  - **Bot**（机器人）  ← **点这一项**
- 如果还没创建过 Bot，中间会有一行 **「Add Bot」**，点它；如果已经添加过 Bot，会直接看到 Bot 的头像和用户名。

### 4. 找到并开启「Privileged Gateway Intents」

- 在 **Bot** 这一页里，往下滚动，会看到一个大标题：**「Privileged Gateway Intents」**（ privileged 是“特权”的意思）。
- 下面通常有 3 个开关：
  - **Presence Intent**（在线状态）—— 可不开
  - **Server Members Intent**（服务器成员）—— 可不开
  - **Message Content Intent**（消息内容）—— **这个必须打开**
- 把 **Message Content Intent** 右侧的开关拨到 **ON**（打开）。
- 如果弹出确认框，点 **「Yes, Do It」** 或类似确认。
- 改完后如果页面有 **「Save Changes」**，点一下保存。

> **为什么要开 Message Content Intent？**  
> 不开的话，Bot 只能看到“有人发了消息”，但看不到消息的具体文字，我们的周报就没法分析内容，所以必须开。

### 5. 复制 Bot Token（重要，只显示一次）

- 还是在 **Bot** 页面，最上方有 **「TOKEN」** 这一块。
- 下面有一行灰色内容（你的 Token），右侧有 **「Reset Token」** / **「Copy」** 按钮。
- 点 **「Copy」** 把 Token 复制到剪贴板，粘贴到记事本里先存好。
- **注意**：Token 只在你点 **「Reset Token」** 之后会完整显示一次，平时是打码的。如果你从没复制过，需要点一次 **「Reset Token」**，在弹窗里确认，然后**立刻**把新 Token 复制保存；以后不要再把 Token 发给别人或贴到公开地方。

到这里，**Bot Token** 你已经有了，后面在 GitHub Secrets 里会填成 `DISCORD_BOT_TOKEN`。

---

## 二、把 Bot 邀请进你的 Discord 服务器

### 1. 生成邀请链接

- 还在开发者门户里，左侧点 **「OAuth2」** → 再点下面的 **「URL Generator」**（URL 生成器）。
- **Scopes**（权限范围）里勾选：**「bot」**。
- 下面会多出一块 **「Bot Permissions」**（机器人权限），在里面勾选：
  - **View Channels**（查看频道）
  - **Read Message History**（读取消息历史）
- 页面最下面会生成一行 **「Generated URL」**，右侧点 **「Copy」** 复制这个链接。

### 2. 用浏览器打开链接并选择服务器

- 把复制的链接在浏览器新标签页打开。
- 会进入 Discord 的授权页，让你选「要邀请 Bot 进哪个服务器」。
- 在下拉框里选你要收集建议的那个**服务器**，然后点 **「继续」** / **「Authorize」**。
- 完成人机验证（如果有），Bot 就进到该服务器了。

---

## 三、在 Discord 里开启「开发者模式」并拿到服务器 ID、频道 ID

### 1. 打开 Discord 客户端设置

- 打开 **Discord**（电脑端或网页版都可以）。
- 左下角你的头像旁边有个 **齿轮图标** ⚙️，点它进入 **「用户设置」**（User Settings）。

### 2. 找到「应用设置」里的「高级」

- 左侧有一列：**「我的账号」**、**「隐私与安全」**、**「应用设置」** 等。
- 点 **「应用设置」**（App Settings），下面会再出现子菜单。
- 在子菜单里找到 **「高级」**（Advanced），点进去。

### 3. 开启「开发者模式」

- 在 **「高级」** 页面里，找到 **「开发者模式」**（Developer Mode）。
- 把右侧开关打开（变成绿色）。
- 关掉设置窗口即可，不需要点保存（改完就生效）。

### 4. 复制「服务器 ID」（Guild ID）

- 回到 Discord 主界面，左侧是你加入的服务器列表。
- **右键**你要用来收集建议的**那个服务器**的图标（或服务器名称）。
- 菜单最下面会出现 **「复制服务器 ID」**（Copy Server ID），点它。
- 复制到的是一串**纯数字**，例如：`1234567890123456789`，这就是 **DISCORD_GUILD_ID**，先存到记事本。

### 5. 复制「频道 ID」（Channel ID）

- 在左侧频道列表里，找到你要收集建议的**那个频道**（文字频道）。
- **右键**这个频道名字。
- 菜单里会有 **「复制频道 ID」**（Copy Channel ID），点它。
- 复制到的也是一串**纯数字**，例如：`9876543210987654321`，这就是 **DISCORD_CHANNEL_ID**，存好。

> **注意**：  
> - 必须是 **文字频道**（能发文字消息的），不能是语音频道。  
> - 要收集哪个频道的帖子，就复制那个频道的 ID。

---

## 四、在 GitHub 里填 Discord 相关 Secrets

- 打开你的周报项目仓库 → **Settings** → **Secrets and variables** → **Actions**。
- 点 **「New repository secret」**，按下面三个各建一条：

| Name（名称）           | Value（值）                          |
|------------------------|--------------------------------------|
| `DISCORD_BOT_TOKEN`    | 你在「一、5」里复制的 Bot Token      |
| `DISCORD_GUILD_ID`     | 你在「三、4」里复制的服务器 ID       |
| `DISCORD_CHANNEL_ID`   | 你在「三、5」里复制的频道 ID         |

填好后保存即可，不需要再改代码。

---

## 五、小结检查清单

- [ ] 在开发者门户 **Bot** 里打开了 **Message Content Intent**
- [ ] 已复制并保存 **Bot Token**（填到 `DISCORD_BOT_TOKEN`）
- [ ] 已用 OAuth2 URL Generator 把 Bot 邀请进了目标服务器
- [ ] Discord 里已开启 **开发者模式**
- [ ] 已复制**服务器 ID**（填到 `DISCORD_GUILD_ID`）
- [ ] 已复制**要收集建议的频道 ID**（填到 `DISCORD_CHANNEL_ID`）
- [ ] 在 GitHub 仓库的 Actions Secrets 里已添加上述三个 Secret

做完这些，再在 GitHub Actions 里手动跑一次 **Weekly Report to Feishu**，就可以用 Discord 频道里的帖子生成周报并发到飞书了。
