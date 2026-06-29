---
name: qq-group-chat
description: QQ群聊skill（CLI 版）。群聊创建/设置/搜索/加入/退出/解散，成员管理/禁言/移出/角色设置/邀请/转让群主。当用户提到QQ群、群聊、群管理、群成员，且涉及创建群、设置群、搜索群、禁言、踢人、移出成员、群管理等操作时触发。不适用于QQ频道管理（使用 tencent-channel-community）、纯消息收发、好友管理。
homepage: https://cloud.tencent.com/document/product/269
version: 1.0.0
metadata: {"openclaw":{"emoji":"👥"}}
---

所有操作通过 `python3 scripts/qq-group-cli.py <domain> <action>` 调用（脚本位于本 Skill 目录下）。两种传参模式：

- **CLI flag**：`python3 scripts/qq-group-cli.py manage create-group --type Public --name "我的群"`
- **stdin JSON**（复杂参数场景）：`echo '{"member_list":[...]}' | python3 scripts/qq-group-cli.py manage create-group --type Public --name "我的群" --member-list -`

## 场景路由

根据用户意图关键词，读取对应参考文档：

- **`references/manage-group.md`** — 创建群、修改群资料、获取群信息、搜索群、加入群、退出群、解散群、获取加群申请
- **`references/manage-member.md`** — 成员列表、成员信息、禁言、全员禁言、踢人、设置角色、修改群名片、邀请入群、转让群主、在线人数

> 「创建群」「修改群」「搜索群」「加入群」「退出群」「解散群」「群信息」「群设置」→ manage-group.md；「成员」「禁言」「踢人」「移出」「角色」「群名片」「邀请」「转让」「在线」→ manage-member.md

## 全局硬规则

1. **高风险操作**（`dismiss-group` / `kick-member` / `mute-member` / `mute-all` / `set-member-role`(降级为Member) / `transfer-owner` / `quit-group`）：先说明影响 → 等用户同意 → 加 `--yes` 执行（预留确认机制，当前 CLI 直接执行，agent 需在调用前口头确认）
2. **执行阶段敏感信息最小化**：群成员的 QQ 号、手机号等隐私数据默认不展示、不复述，仅在执行必需时保留最小字段；业务敏感数据（如 UserSig、SecretKey）不向用户展示原值
3. **群组 ID 传递**：始终使用 `GroupId`（如 `@TGS#2J4SZEAEL`）进行操作，不混淆群号与群组 ID
4. **鉴权失败**（ErrorCode 非 0 或返回 "未配置凭证" 错误）：按「环境与认证」章节走，引导用户完成登录配置
5. **频率限制**（ErrorCode `10006`）：不报错、不询问用户，直接 sleep 5s 后原样重试一次；若仍失败，告知用户"接口触发频率限制，请稍后再试"
6. **参数查询**：不确定参数时，使用 `python3 scripts/qq-group-cli.py schema <domain>.<action>` 实时查询参数定义

## 环境与认证

本 Skill 支持两种认证方式：

### 方式一：腾讯云 IM（推荐，功能最全）

通过 SDKAppID + SecretKey 认证，支持所有群组管理操作。需在[腾讯云 IM 控制台](https://console.cloud.tencent.com/im)创建应用获取凭证。

```bash
python3 scripts/qq-group-cli.py login
# 选择 1 → 输入 SDKAppID / SecretKey / 管理员账号
```

### 方式二：QQ机器人开放平台

通过 AppID + AppSecret 认证，部分操作受限。需在[QQ开放平台](https://q.qq.com)注册机器人获取凭证。

```bash
python3 scripts/qq-group-cli.py login
# 选择 2 → 输入 AppID / AppSecret
```

### 检查状态

```bash
python3 scripts/qq-group-cli.py login --status   # 查看登录状态
python3 scripts/qq-group-cli.py version           # 查看版本
```

> 未登录时禁止执行任何 manage/member 命令，必须先引导用户完成登录配置。

## 群组类型说明

| 类型 ID | 名称 | 特点 |
|---------|------|------|
| Public | 陌生人社交群 | 可被搜索、需审批或自由加入 |
| Private (Work) | 好友工作群 | 不可被搜索、仅邀请加入 |
| ChatRoom (Meeting) | 会议群 | 可随意进出、无入群审批 |
| AVChatRoom | 直播群 | 海量成员、用户需主动进群 |
| Community | 社群 | 支持话题功能、需旗舰版套餐 |

## 工作流示例

### 示例 1：创建群并邀请成员

用户：「帮我创建一个技术交流群，把张三和李四拉进来」

1. 确认群组类型和名称（如 Public / "技术交流群"）
2. `python3 scripts/qq-group-cli.py manage create-group --type Public --name "技术交流群" --introduction "技术讨论与分享"`
3. 从返回中获取 `GroupId`
4. `python3 scripts/qq-group-cli.py member invite-member --group-id <GroupId> --account zhangsan,lisi`
5. 汇总结果告知用户

### 示例 2：管理群成员

用户：「把群里那个发广告的人禁言1小时，然后踢出去」

1. 先查找成员：`python3 scripts/qq-group-cli.py member get-member-list --group-id <GroupId>` 找到目标用户
2. **高风险操作确认**：告知用户将禁言并移出该成员，等待确认
3. 禁言：`python3 scripts/qq-group-cli.py member mute-member --group-id <GroupId> --account <user_id> --duration 3600`
4. 移出：`python3 scripts/qq-group-cli.py member kick-member --group-id <GroupId> --account <user_id> --reason "发广告"`

## 执行阶段敏感信息策略

1. **用户隐私数据**（QQ号、手机号等）：默认不展示、不复述；命令确需使用时仅保留最小必要字段
2. **业务敏感数据**（UserSig、SecretKey、AccessToken）：默认不展示原值，执行所需字段不得丢失
3. 能用 GroupId 或 Member_Account 定位时，禁止额外传递姓名、QQ号等个人信息
4. 总结和表格中不重新拼接完整敏感信息

## 资源目录

### scripts/
- `qq-group-cli.py` — CLI 工具，封装腾讯云 IM REST API 和 QQ机器人开放平台 API

### references/
- `manage-group.md` — 群组管理操作详细参考
- `manage-member.md` — 成员管理操作详细参考
