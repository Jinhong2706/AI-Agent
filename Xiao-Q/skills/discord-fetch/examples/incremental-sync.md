# 示例：增量同步

## 场景：定期同步，避免重复写入

首次拉取时保存 `newest_message_id`，后续每次只拉新消息。

**第一次（全量）：**

```bash
python scripts/discord_fetch.py --channel 123... --max 1000 --format json > first_run.json

# 查看检查点 ID
python -c "import json; d=json.load(open('first_run.json')); print(d['newest_message_id'])"
# 输出：1381234567890000000
```

**后续（增量）：**

```bash
python scripts/discord_fetch.py \
  --channel 123... \
  --after 1381234567890000000 \
  | python scripts/feishu_write.py \
      --app-token bascXXX --table-id tblXXX
```

## 场景：预览不写入（dry-run）

```bash
python scripts/discord_fetch.py --channel 123... --max 50 \
  | python scripts/feishu_write.py \
      --app-token bascXXX --table-id tblXXX \
      --dry-run
```

**输出（节选）：**

```json
{
  "dry_run": true,
  "count": 50,
  "sample": [
    {
      "message_id": "138...",
      "author_username": "alice",
      "content": "Hello!",
      ...
    }
  ]
}
```

## 检查点管理建议

把 `newest_message_id` 存入飞书多维表格的"配置表"，每次同步后更新，下次读取后传给 `--after`，实现全自动增量同步。
