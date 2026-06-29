# 群组管理参考

本文件涵盖群组的生命周期管理操作：创建、查询、修改、搜索、加入、退出、解散。

---

## 1. 创建群组

**命令**：`python3 scripts/qq-group-cli.py manage create-group`

### 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| --type | ✅ | 群组类型: Public / Private / ChatRoom / AVChatRoom / Community |
| --name | ✅ | 群名称，最长100字节(UTF-8，1汉字=3字节) |
| --owner-account | ❌ | 群主ID（需已导入账号），不填则群无群主 |
| --group-id | ❌ | 自定义群组ID，便于记忆和传播 |
| --introduction | ❌ | 群简介，最长400字节 |
| --notification | ❌ | 群公告，最长400字节 |
| --face-url | ❌ | 群头像URL，最长500字节 |
| --max-member-num | ❌ | 最大群成员数量，默认为套餐包上限 |
| --apply-join-option | ❌ | 加群方式: FreeAccess(自由) / NeedPermission(需验证) / DisableApply(禁止) |
| --member-list | ❌ | 初始群成员(JSON数组)，最多20人 |

### 示例

```bash
# 基础创建
python3 scripts/qq-group-cli.py manage create-group --type Public --name "技术交流群"

# 完整参数
python3 scripts/qq-group-cli.py manage create-group \
  --type Public \
  --name "技术交流群" \
  --introduction "技术讨论与分享" \
  --notification "入群请看公告" \
  --apply-join-option NeedPermission \
  --max-member-num 500

# 带初始成员
python3 scripts/qq-group-cli.py manage create-group \
  --type Public \
  --name "项目组" \
  --member-list '[{"Member_Account":"user1","Role":"Admin"},{"Member_Account":"user2"}]'
```

### 返回

```json
{
  "ActionStatus": "OK",
  "ErrorCode": 0,
  "GroupId": "@TGS#2J4SZEAEL"
}
```

### 常见错误码

| 错误码 | 说明 |
|--------|------|
| 10002 | 服务器内部错误，请重试 |
| 10004 | 参数非法 |
| 10005 | 初始成员超过20人 |
| 10006 | 频率限制 |
| 10007 | 权限不足（如AVChatRoom不允许拉人入群） |
| 10021 | 群组ID已被占用 |
| 10037 | 群主加入群数超限 |
| 10058 | 体验版超过100个群限制 |

### 注意事项

- AVChatRoom（直播群）创建时不能拉人入群，用户需主动申请
- 如果不指定群主也不设成员列表，创建群数量无限制
- 指定群主或成员后，会自动加入该群

---

## 2. 获取群信息

**命令**：`python3 scripts/qq-group-cli.py manage get-group-info`

### 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| --group-id | ✅ | 群组ID |

### 示例

```bash
python3 scripts/qq-group-cli.py manage get-group-info --group-id "@TGS#2J4SZEAEL"
```

### 返回

包含群名称、类型、简介、公告、成员数、最大成员数、创建时间等。

---

## 3. 获取群列表

**命令**：`python3 scripts/qq-group-cli.py manage get-group-list`

### 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| --limit | ❌ | 一次最多获取的群组数量，默认10000 |
| --group-type | ❌ | 按群组类型过滤 |
| --next | ❌ | 分页签，从上次返回的Next值继续获取 |

### 示例

```bash
# 获取所有群
python3 scripts/qq-group-cli.py manage get-group-list

# 按类型过滤
python3 scripts/qq-group-cli.py manage get-group-list --group-type Public --limit 50

# 翻页
python3 scripts/qq-group-cli.py manage get-group-list --next "下次分页签值"
```

---

## 4. 修改群资料

**命令**：`python3 scripts/qq-group-cli.py manage modify-group-base-info`

### 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| --group-id | ✅ | 群组ID |
| --name | ❌ | 新群名称 |
| --introduction | ❌ | 新群简介 |
| --notification | ❌ | 新群公告 |
| --face-url | ❌ | 新群头像URL |
| --max-member-num | ❌ | 新最大成员数 |
| --apply-join-option | ❌ | 新加群方式 |
| --mute-all-member | ❌ | 全员禁言: On / Off |

### 示例

```bash
# 修改群名和公告
python3 scripts/qq-group-cli.py manage modify-group-base-info \
  --group-id "@TGS#xxx" \
  --name "新群名" \
  --notification "新公告内容"

# 开启全员禁言
python3 scripts/qq-group-cli.py manage modify-group-base-info \
  --group-id "@TGS#xxx" \
  --mute-all-member On
```

### 注意事项

- Public/ChatRoom/Community：所有成员均可修改群名称和简介（除非管理员限制）
- Private：仅群主和管理员可修改
- 修改 MaxMemberNum 不能超过套餐上限

---

## 5. 搜索群组

**命令**：`python3 scripts/qq-group-cli.py manage search-group`

### 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| --keyword | ✅ | 搜索关键字 |
| --group-type | ❌ | 按群组类型过滤 |

### 示例

```bash
python3 scripts/qq-group-cli.py manage search-group --keyword "技术交流"
python3 scripts/qq-group-cli.py manage search-group --keyword "游戏" --group-type Public
```

> 注意：搜索功能依赖腾讯云IM的云端搜索能力，需开通相关服务。

---

## 6. 加入群组

**命令**：`python3 scripts/qq-group-cli.py manage join-group`

### 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| --group-id | ✅ | 群组ID |
| --account | ✅ | 申请加入的用户ID |
| --reason | ❌ | 申请理由 |

### 示例

```bash
python3 scripts/qq-group-cli.py manage join-group \
  --group-id "@TGS#xxx" \
  --account user1 \
  --reason "想加入群聊讨论技术"
```

### 注意事项

- Public 群：根据 ApplyJoinOption 设置，可能需要管理员审批
- Private 群：不支持主动申请，只能被邀请
- AVChatRoom：用户直接进入，无需审批
- 加入群组受用户已加入群数量限制

---

## 7. 退出群组

**命令**：`python3 scripts/qq-group-cli.py manage quit-group`

> ⚠️ **高风险操作**：退出前需确认用户意图。

### 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| --group-id | ✅ | 群组ID |
| --account | ✅ | 退出群组的用户ID |

### 示例

```bash
python3 scripts/qq-group-cli.py manage quit-group --group-id "@TGS#xxx" --account user1
```

---

## 8. 解散群组

**命令**：`python3 scripts/qq-group-cli.py manage dismiss-group`

> ⚠️ **高风险操作**：解散后不可恢复，必须确认用户意图！

### 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| --group-id | ✅ | 群组ID |

### 示例

```bash
python3 scripts/qq-group-cli.py manage dismiss-group --group-id "@TGS#xxx"
```

### 注意事项

- 仅群主可以解散群组
- 解散后群内所有成员将被移出，聊天记录不可恢复
- Private/ChatRoom 类型群组不支持主动解散（群内无成员时自动解散）

---

## 9. 获取加群申请

**命令**：`python3 scripts/qq-group-cli.py manage get-join-application`

### 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| --group-id | ❌ | 群组ID，不填则获取所有加群申请 |

### 示例

```bash
# 获取特定群的加群申请
python3 scripts/qq-group-cli.py manage get-join-application --group-id "@TGS#xxx"

# 获取所有加群申请
python3 scripts/qq-group-cli.py manage get-join-application
```

---

## 操作速查表

| 操作 | 命令 | 风险等级 |
|------|------|----------|
| 创建群 | `manage create-group` | 🟢 低 |
| 获取群信息 | `manage get-group-info` | 🟢 低 |
| 获取群列表 | `manage get-group-list` | 🟢 低 |
| 修改群资料 | `manage modify-group-base-info` | 🟡 中 |
| 搜索群 | `manage search-group` | 🟢 低 |
| 加入群 | `manage join-group` | 🟢 低 |
| 退出群 | `manage quit-group` | 🔴 高 |
| 解散群 | `manage dismiss-group` | 🔴 高 |
| 加群申请 | `manage get-join-application` | 🟢 低 |
