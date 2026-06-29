---
name: discord-fetch
description: 从指定 Discord 频道批量拉取/导出聊天消息（自动翻页、突破单次 100 条上限），输出为结构化数据（发言人、时间、正文、附件、embed 等），可选地写入飞书多维表格（Bitable）。只要用户想获取、导出或同步某个 Discord 频道的消息记录，就使用本技能——无论是否提到飞书；典型信号包括提供了 Discord bot token + channel id、说「拉取/获取/导出 Discord 消息」「同步 Discord 频道聊天」「Discord channel messages to 飞书/Bitable」「自动翻页抓频道历史」。支持全量拉取、日期范围过滤与基于消息 ID 的增量同步，可一键输出 JSON/CSV/Markdown。仅适用于 Discord，且为只读拉取：不处理发送消息、构建 bot、Slack/Telegram 等其他平台、或分析已导出的数据。
metadata:
  version: "1.1.0"
  author: joy20260328@gmail.com
  tags: [discord, feishu, bitable, data-sync]
  requirements:
    python: ">=3.9"
---

# Discord 频道消息拉取

把指定 Discord 频道的聊天记录拉成干净的结构化 JSON/CSV，每条消息是一行扁平记录，可直接写入飞书多维表格。拉取逻辑（翻页、限流退避、去重）封装在 `scripts/discord_fetch.py` 里，写入逻辑封装在 `scripts/feishu_write.py` 里，**执行脚本即可，不要自己重写 HTTP 调用**。

## 前置条件（首次使用必读）

用户需要在 Discord 端准备好（详见 `references/setup.md`）：
1. 一个 **Bot Token**（开发者后台 → 应用 → Bot → Reset Token）。
2. 已把 bot **邀请进目标服务器**。
3. **开启 Message Content Intent**，否则拉到的消息正文 `content` 会是空的——这是最常见的坑。
4. bot 在目标频道有 "View Channel" + "Read Message History" 权限。
5. 一个 **Channel ID**（Discord 开启开发者模式 → 右键频道 → 复制频道 ID）。

如需写入飞书，还需要：飞书应用的 `FEISHU_APP_ID` 和 `FEISHU_APP_SECRET`，以及目标多维表格的 `app_token` 和 `table_id`。

## Token 的提供方式（按安全优先级）

1. **环境变量 `DISCORD_BOT_TOKEN`（推荐）**：不进对话上下文、不入日志，最安全。
2. **`--token` 参数**：仅在多 token 临时切换时使用。

**绝不要把完整 token 写进回复正文或反复回显**。脚本内部只会显示首尾各 4 位的指纹。

## 操作步骤

### 第零步：环境自检（推荐首次运行）

```bash
python scripts/discord_fetch.py --channel <CHANNEL_ID> --check
```

一次性验证：token 有效 + bot 能访问频道 + Message Content Intent 已开启。出错时有明确提示。

### 第一步（可选）：确认能看到频道

```bash
python scripts/discord_fetch.py --channel <CHANNEL_ID> --info
```

### 第二步：拉取消息

全量（最新 N 条，自动翻页）：

```bash
python scripts/discord_fetch.py --channel <CHANNEL_ID> --max 200 --format json
```

按日期范围过滤：

```bash
python scripts/discord_fetch.py --channel <CHANNEL_ID> \
  --after-date 2026-01-01 --before-date 2026-02-01
```

增量同步（只拉比检查点更新的消息）：

```bash
python scripts/discord_fetch.py --channel <CHANNEL_ID> --after <上次的_newest_message_id>
```

导出 CSV：

```bash
python scripts/discord_fetch.py --channel <CHANNEL_ID> --max 500 --format csv > messages.csv
```

输出 JSON 结构：

```json
{
  "channel_id": "...",
  "count": 123,
  "newest_message_id": "...",
  "oldest_message_id": "...",
  "reached_end": true,
  "messages": [
    {
      "message_id": "...", "channel_id": "...",
      "author_id": "...", "author_username": "...", "author_global_name": "...",
      "is_bot": false, "content": "消息正文",
      "timestamp": "2026-01-01T00:00:00+00:00", "edited_timestamp": null,
      "reply_to_message_id": null,
      "attachment_count": 0, "attachments": [], "embed_count": 0, "embeds": []
    }
  ]
}
```

### 第三步：写入飞书多维表格

```bash
# 一条命令完成拉取 + 写入
python scripts/discord_fetch.py --channel <CHANNEL_ID> --max 500 \
  | python scripts/feishu_write.py \
      --app-token <BITABLE_APP_TOKEN> \
      --table-id <TABLE_ID>
```

先 dry-run 预览不写入：

```bash
python scripts/discord_fetch.py --channel <CHANNEL_ID> --max 10 \
  | python scripts/feishu_write.py \
      --app-token <BITABLE_APP_TOKEN> --table-id <TABLE_ID> --dry-run
```

**关键约定**：多维表格里的 `message_id` 列设为唯一标识去重；每次拉取后存下 `newest_message_id`，下次作为 `--after` 传入做增量同步。

详细字段映射与增量同步编排见 `references/feishu-bitable.md`，更多用法示例见 `examples/`。

## 注意事项

- 消息正文为空，几乎都是没开 Message Content Intent，先去后台开启（或运行 `--check`）。
- `--max` 上限 5000，频道很大时建议分批 + 增量同步。
- 触发 429（限流）脚本会自动退避重试，一般无需干预。
- 脚本进度和日志输出到 stderr，stdout 只有干净的 JSON/CSV，可以直接管道到下游。
