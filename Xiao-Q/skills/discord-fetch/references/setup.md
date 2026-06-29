# Discord Bot Token 与 Channel ID 获取指南

## 一、创建应用与 Bot

1. 打开 Discord 开发者后台：https://discord.com/developers/applications
2. 点击 **New Application**，填名称，创建。
3. 左侧进入 **Bot** 页，点击 **Reset Token**（或 Add Bot 后 Reset Token），复制出现的 **Bot Token**。
   - 这串就是脚本要用的 `DISCORD_BOT_TOKEN`。
   - **它只显示一次**，没存好就只能再次 Reset。
   - Token 等同于机器人的完整控制权，泄露后他人可冒充你的 bot。切勿提交到代码仓库、贴进聊天或日志。

## 二、开启 Privileged Gateway Intents（关键）

在 **Bot** 页下方找到 **Privileged Gateway Intents**，开启：
- **Message Content Intent** —— 必须开。不开的话，拉取消息时 `content` 字段会是空字符串，只能拿到消息的壳。
- Server Members Intent / Presence Intent —— 按需，本技能拉消息不强制。

## 三、邀请 Bot 进服务器

1. 左侧 **OAuth2 → URL Generator**。
2. Scopes 勾选 **bot**。
3. Bot Permissions 至少勾选：**View Channel**、**Read Message History**。
4. 复制底部生成的 URL，在浏览器打开，选择目标服务器授权。
   - 你需要对该服务器有「管理服务器」权限才能邀请。

## 四、获取 Channel ID

1. Discord 客户端 → 用户设置 → **高级 → 开启「开发者模式」**。
2. 回到服务器，**右键目标频道 → 复制频道 ID**。
3. 得到一串 17–20 位数字，这就是 `--channel` 要传的值。

## 五、自检

拿到 token 和 channel id 后，先跑：

```bash
DISCORD_BOT_TOKEN=<你的token> python scripts/discord_fetch.py --channel <频道ID> --info
```

- 正常返回频道信息 → 权限与 ID 都对，可以开始拉取。
- 401 → token 错或失效，重新 Reset。
- 403 → bot 没被邀请进该服务器，或缺频道权限。
- 404 → channel id 错，或 bot 看不到这个频道。
