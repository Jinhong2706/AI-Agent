# 写入飞书多维表格（Bitable）

本技能只负责把 Discord 消息拉成结构化记录。写入飞书多维表格用 agent 已有的飞书能力完成：在飞书 Aily 里用多维表格连接器，或在 Claude Code / Codex 里调飞书开放平台接口（或挂一个飞书 MCP）。

## 推荐表格结构

| 列名 | 类型 | 来源字段 | 说明 |
|------|------|----------|------|
| message_id | 文本 | `message_id` | **设为唯一标识，用于去重** |
| 作者 | 文本 | `author_global_name` 或 `author_username` | |
| 作者ID | 文本 | `author_id` | |
| 是否机器人 | 复选 | `is_bot` | |
| 内容 | 多行文本 | `content` | |
| 时间 | 日期 | `timestamp` | ISO 8601，飞书可直接解析 |
| 附件数 | 数字 | `attachment_count` | |
| 附件链接 | 文本 | `attachments[].url` | 多个可拼接 |

## 标准编排流程

1. **拉取**：调用本技能脚本，`--format json`，得到 `messages` 数组和 `newest_message_id`。
2. **去重写入**：遍历 `messages`，以 `message_id` 为唯一键写入多维表格的「新增记录」。
   - 飞书多维表格批量新增接口：`POST /open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create`
   - 若你的连接器支持 upsert，用 `message_id` 作为去重键；不支持的话，先查后写，或依赖表格的唯一性约束。
3. **存检查点**：把这次返回的 `newest_message_id` 记下来（存进一张配置表 / 一个变量 / 本地文件）。
4. **增量同步**：下次拉取时把上次的 `newest_message_id` 作为 `--after` 传入，只会拿到更新的消息，避免重复写入。

## 字段映射注意

- `timestamp` 是 ISO 8601 字符串（带时区）。飞书日期列通常接受毫秒时间戳，必要时在写入前转换：解析 ISO 字符串 → 毫秒。
- `content` 可能为空（纯图片/附件消息），按需在表格里允许空值。
- `attachments` 是数组；若表格只放一列链接，可把多个 url 用换行或逗号拼接。

## 增量同步的幂等性

只要满足以下任一条，重复运行就不会产生重复行：
- 多维表格 `message_id` 列设唯一约束；或
- 写入前按 `message_id` 查重；或
- 每次都用上次的 `newest_message_id` 作 `--after`，从源头只取新消息。

三者叠加最稳：用 `--after` 减少拉取量，再用 `message_id` 唯一性兜底。
