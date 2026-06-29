# 成员管理参考

本文件涵盖群成员相关的管理操作：成员查询、禁言、踢人、角色管理、邀请、转让等。

---

## 1. 获取群成员列表

**命令**：`python3 scripts/qq-group-cli.py member get-member-list`

### 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| --group-id | ✅ | 群组ID |
| --limit | ❌ | 一次最多获取的成员数量，默认6000 |
| --offset | ❌ | 偏移量，默认0 |
| --role-filter | ❌ | 按角色过滤: Owner / Admin / Member |

### 示例

```bash
# 获取全部成员
python3 scripts/qq-group-cli.py member get-member-list --group-id "@TGS#xxx"

# 分页获取
python3 scripts/qq-group-cli.py member get-member-list --group-id "@TGS#xxx" --limit 100 --offset 0

# 只看管理员
python3 scripts/qq-group-cli.py member get-member-list --group-id "@TGS#xxx" --role-filter Admin
```

### 返回字段

| 字段 | 说明 |
|------|------|
| Member_Account | 用户ID |
| Role | 角色: Owner / Admin / Member |
| JoinTime | 加群时间 |
| MsgSeq | 最后发言消息序号 |
| MsgFlag | 消息屏蔽标志 |
| NameCard | 群名片 |
| MuteUntil | 禁言截止时间(0=未禁言) |

---

## 2. 获取指定成员信息

**命令**：`python3 scripts/qq-group-cli.py member get-member-info`

### 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| --group-id | ✅ | 群组ID |
| --account | ✅ | 用户ID（多个用逗号分隔） |

### 示例

```bash
# 查询单个成员
python3 scripts/qq-group-cli.py member get-member-info --group-id "@TGS#xxx" --account user1

# 查询多个成员
python3 scripts/qq-group-cli.py member get-member-info --group-id "@TGS#xxx" --account user1,user2,user3
```

---

## 3. 禁言成员

**命令**：`python3 scripts/qq-group-cli.py member mute-member`

> ⚠️ **高风险操作**：禁言前需告知用户影响并确认。

### 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| --group-id | ✅ | 群组ID |
| --account | ✅ | 要禁言的用户ID（多个用逗号分隔，最多500） |
| --duration | ❌ | 禁言时长(秒)，默认1800(30分钟)，0=取消禁言 |

### 常用禁言时长

| 时长 | 秒数 |
|------|------|
| 5分钟 | 300 |
| 10分钟 | 600 |
| 30分钟 | 1800 |
| 1小时 | 3600 |
| 1天 | 86400 |
| 取消禁言 | 0 |

### 示例

```bash
# 禁言1小时
python3 scripts/qq-group-cli.py member mute-member --group-id "@TGS#xxx" --account user1 --duration 3600

# 批量禁言
python3 scripts/qq-group-cli.py member mute-member --group-id "@TGS#xxx" --account user1,user2 --duration 600

# 取消禁言
python3 scripts/qq-group-cli.py member mute-member --group-id "@TGS#xxx" --account user1 --duration 0
```

### 注意事项

- 仅群主和管理员可以对普通成员禁言
- 管理员不能禁言群主和其他管理员
- 禁言时长最长30天（2592000秒）

---

## 4. 全员禁言

**命令**：`python3 scripts/qq-group-cli.py member mute-all`

> ⚠️ **高风险操作**：影响群内所有普通成员，需确认。

### 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| --group-id | ✅ | 群组ID |
| --mute-all-member | ✅ | On=开启全员禁言 / Off=关闭全员禁言 |

### 示例

```bash
# 开启全员禁言
python3 scripts/qq-group-cli.py member mute-all --group-id "@TGS#xxx" --mute-all-member On

# 关闭全员禁言
python3 scripts/qq-group-cli.py member mute-all --group-id "@TGS#xxx" --mute-all-member Off
```

### 注意事项

- 全员禁言时，管理员和群主仍可发言
- 也可通过 `manage modify-group-base-info --mute-all-member On/Off` 实现

---

## 5. 踢出成员

**命令**：`python3 scripts/qq-group-cli.py member kick-member`

> ⚠️ **高风险操作**：移出成员需确认意图。

### 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| --group-id | ✅ | 群组ID |
| --account | ✅ | 要踢出的用户ID（多个用逗号分隔） |
| --reason | ❌ | 踢出原因 |

### 示例

```bash
# 踢出单个成员
python3 scripts/qq-group-cli.py member kick-member --group-id "@TGS#xxx" --account user1 --reason "违规发言"

# 批量踢出
python3 scripts/qq-group-cli.py member kick-member --group-id "@TGS#xxx" --account user1,user2
```

### 注意事项

- 群主可踢出任何人（包括管理员）
- 管理员只能踢出普通成员
- 普通成员无权踢人
- AVChatRoom 类型不支持通过 REST API 踢人

---

## 6. 设置成员角色

**命令**：`python3 scripts/qq-group-cli.py member set-member-role`

> ⚠️ **降级操作(设为Member)为高风险**，需确认。

### 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| --group-id | ✅ | 群组ID |
| --account | ✅ | 用户ID |
| --role | ✅ | 目标角色: Admin(管理员) / Member(普通成员) |

### 示例

```bash
# 设为管理员
python3 scripts/qq-group-cli.py member set-member-role --group-id "@TGS#xxx" --account user1 --role Admin

# 取消管理员
python3 scripts/qq-group-cli.py member set-member-role --group-id "@TGS#xxx" --account user1 --role Member
```

### 注意事项

- 群主可设置/取消管理员
- 管理员不能修改其他管理员或群主的角色
- Public 群最多10个管理员，Private 群无限制

---

## 7. 修改成员信息

**命令**：`python3 scripts/qq-group-cli.py member modify-member-info`

### 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| --group-id | ✅ | 群组ID |
| --account | ✅ | 用户ID |
| --name-card | ❌ | 群名片 |
| --custom-data | ❌ | 自定义字段(JSON数组) |

### 示例

```bash
# 修改群名片
python3 scripts/qq-group-cli.py member modify-member-info \
  --group-id "@TGS#xxx" \
  --account user1 \
  --name-card "张三-技术负责人"

# 设置自定义字段
python3 scripts/qq-group-cli.py member modify-member-info \
  --group-id "@TGS#xxx" \
  --account user1 \
  --custom-data '[{"Key":"Department","Value":"Tech"}]'
```

---

## 8. 邀请入群

**命令**：`python3 scripts/qq-group-cli.py member invite-member`

### 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| --group-id | ✅ | 群组ID |
| --account | ✅ | 要邀请的用户ID（多个用逗号分隔） |

### 示例

```bash
# 邀请单个用户
python3 scripts/qq-group-cli.py member invite-member --group-id "@TGS#xxx" --account user1

# 批量邀请
python3 scripts/qq-group-cli.py member invite-member --group-id "@TGS#xxx" --account user1,user2,user3
```

### 注意事项

- Private 群：仅群主和管理员可邀请
- Public 群：仅群主和管理员可邀请，被邀请人直接入群
- Community 群：仅群主和管理员可邀请
- AVChatRoom：不支持邀请，用户需主动申请
- InviteJoinOption 控制是否需要审批（详见群设置）

---

## 9. 转让群主

**命令**：`python3 scripts/qq-group-cli.py member transfer-owner`

> ⚠️ **高风险操作**：转让后原群主变为普通成员，不可逆！

### 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| --group-id | ✅ | 群组ID |
| --account | ✅ | 新群主的用户ID |

### 示例

```bash
python3 scripts/qq-group-cli.py member transfer-owner --group-id "@TGS#xxx" --account newowner
```

### 注意事项

- 仅群主可转让
- 新群主必须是群内成员
- 转让后原群主变为普通成员
- Private/ChatRoom 类型不支持转让

---

## 10. 获取在线人数

**命令**：`python3 scripts/qq-group-cli.py member get-online-count`

### 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| --group-id | ✅ | 群组ID |

### 示例

```bash
python3 scripts/qq-group-cli.py member get-online-count --group-id "@TGS#xxx"
```

> 仅 AVChatRoom 类型返回准确的在线人数，其他群类型返回0或近似值。

---

## 操作速查表

| 操作 | 命令 | 风险等级 |
|------|------|----------|
| 成员列表 | `member get-member-list` | 🟢 低 |
| 成员信息 | `member get-member-info` | 🟢 低 |
| 禁言成员 | `member mute-member` | 🔴 高 |
| 全员禁言 | `member mute-all` | 🔴 高 |
| 踢出成员 | `member kick-member` | 🔴 高 |
| 设置角色 | `member set-member-role` | 🟡 中（降级🔴） |
| 修改信息 | `member modify-member-info` | 🟢 低 |
| 邀请入群 | `member invite-member` | 🟢 低 |
| 转让群主 | `member transfer-owner` | 🔴 高 |
| 在线人数 | `member get-online-count` | 🟢 低 |
