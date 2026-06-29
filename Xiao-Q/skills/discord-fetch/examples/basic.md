# 示例：基础拉取

## 场景：拉取频道最近 200 条消息，输出 JSON

```bash
export DISCORD_BOT_TOKEN=你的BotToken
python scripts/discord_fetch.py --channel 1234567890123456789 --max 200
```

**输出（节选）：**

```json
{
  "channel_id": "1234567890123456789",
  "count": 200,
  "newest_message_id": "1381234567890000000",
  "oldest_message_id": "1370000000000000000",
  "reached_end": false,
  "messages": [
    {
      "message_id": "1370000000000000000",
      "channel_id": "1234567890123456789",
      "author_id": "9876543210987654321",
      "author_username": "alice",
      "author_global_name": "Alice",
      "is_bot": false,
      "content": "Hello, world!",
      "timestamp": "2026-01-15T08:30:00+00:00",
      "edited_timestamp": null,
      "reply_to_message_id": null,
      "attachment_count": 0,
      "attachments": [],
      "embed_count": 0,
      "embeds": []
    }
  ]
}
```

## 场景：按日期范围拉取，导出 CSV

```bash
python scripts/discord_fetch.py \
  --channel 1234567890123456789 \
  --after-date 2026-01-01 \
  --before-date 2026-02-01 \
  --format csv > jan_messages.csv
```

## 场景：一键验证环境配置

```bash
python scripts/discord_fetch.py --channel 1234567890123456789 --check
```

**输出（stderr）：**

```
=== discord-fetch self-check ===
  [OK] Token format: looks valid
  [OK] Channel access: #general in guild 111122223333444455
  [OK] Message Content Intent: content visible
================================
All checks passed. Ready to fetch.
```

## 场景：全流程一条命令（拉取 + 写入飞书）

```bash
python scripts/discord_fetch.py --channel 1234567890123456789 --max 500 \
  | python scripts/feishu_write.py \
      --app-token bascXXXXXXXXXXXX \
      --table-id tblXXXXXXXXXX
```
