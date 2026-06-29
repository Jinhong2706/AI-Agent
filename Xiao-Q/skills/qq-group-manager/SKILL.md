---
name: qq-group-manager
description: >
  QQ 群管理助手，自动审核入群申请并督促新成员修改昵称。
  当用户提到审核入群申请、新成员入群、检查群昵称格式、管理QQ群成员等场景时，必须使用本 skill。
  英文触发词同样适用：QQ group manager, approve join request, check nickname format, group member management。
  不要用于：QQ 频道管理、私聊消息处理、非 QQ 群的聊天平台管理。
compatibility: Requires QQ 官方机器人 API 接入，需要群管理员权限
allowed-tools: exec, read, write, web_fetch
metadata:
  author: User
  version: "1.0.0"
  last-updated: "2026-06-18"
  category: QQ群管理
  tags: "QQ, 群管理, 自动审核, 昵称管理"
---

# QQ 群管理助手

自动审核 QQ 群入群申请并督促新成员按规范修改昵称。

## 功能概述

1. **入群审核**：回答问题正确 **且** QQ 等级 ≥ 10 级 → 通过；否则拒绝
2. **昵称督促**：新成员入群后，检查昵称格式是否为 `昵称-机型`，不符合则发送提醒

---

## When to use

- 用户说"审核入群申请"、"处理加群请求"
- 用户说"新成员进群了"、"检查群昵称"
- 用户说"督促成员改昵称"、"昵称格式不对"

---

## 工作流程

### 任务一：审核入群申请

- [ ] **Step 1**：获取待审核的入群申请列表
  - 调用 QQ 官方机器人 API：`GET /v2/groups/{group_openid}/join-requests`
  - 需要 `group_openid`（群 OpenID）和 `bot_token`（机器人令牌）

- [ ] **Step 2**：逐个审核申请
  - 提取申请人 `user_openid`
  - 调用 API 获取用户 QQ 等级：`GET /v2/users/{user_openid}/profile`
  - 检查回答是否正确（答案由群主预设，可配置）
  - **通过条件**：回答正确 **且** QQ 等级 ≥ 10
  - **拒绝条件**：回答错误 **或** QQ 等级 < 10

- [ ] **Step 3**：执行审核操作
  - 通过：`POST /v2/groups/{group_openid}/join-requests/{request_id}/approve`
  - 拒绝：`POST /v2/groups/{group_openid}/join-requests/{request_id}/reject`
  - 拒绝时附上原因（如"QQ 等级低于 10 级"或"回答错误"）

### 任务二：督促新成员修改昵称

- [ ] **Step 1**：监听群成员增加事件
  - 订阅 QQ 机器人事件：`GROUP_MEMBER_INCREASE`
  - 事件数据包含：`user_openid`、`group_openid`、`join_time`

- [ ] **Step 2**：检查新成员昵称格式
  - 获取成员信息：`GET /v2/groups/{group_openid}/members/{user_openid}`
  - 提取 `nickname` 字段
  - 检查是否符合正则：`^.+-\S+$`（任意字符 + 短横线 + 非空机型名）

- [ ] **Step 3**：发送提醒消息
  - 格式不符合时，向群发送消息：
    ```
    @新成员昵称 欢迎加入本群！
    请按照「昵称-机型」格式修改群昵称，例如：张三-iPhone15
    方便大家识别和交流 😊
    ```
  - 调用 API：`POST /v2/groups/{group_openid}/messages`

---

## 配置说明

在技能根目录创建 `config.json`（不提交到 git）：

```json
{
  "group_openid": "群 OpenID",
  "bot_token": "机器人令牌",
  "required_answer": "预设的入群问题答案（随便设置）",
  "min_qq_level": 10,
  "nickname_pattern": "^.+-\\S+$",
  "welcome_message": "欢迎消息模板，可用 {nickname} 占位"
}
```

---

## Patterns

### Validation Loop（审核循环）

```
do → 获取申请 → 验证等级+答案 → 通过/拒绝 → 记录日志 → 继续下一个
```

### Plan-Validate-Execute（昵称检查）

```
监听事件 → 获取昵称 → 正则匹配 → 不符合 → 发送提醒 → 记录日志
```

---

## Gotchas

- **QQ 等级 API 可能返回 null**：部分用户隐藏了等级信息，此时默认拒绝（安全第一）
- **群 OpenID 获取方式**：从机器人收到的事件消息中提取 `group_openid`，不是群号
- **机器人必须是管理员**：非管理员无法审核入群申请或发送 @ 消息
- **频率限制**：QQ 机器人 API 有调用频率限制（约 50 次/秒），批量审核时需加延迟
- **用户 OpenID 不是 QQ 号**：QQ 机器人使用 OpenID 体系，不直接暴露 QQ 号

---

## References

- QQ 机器人官方文档：https://bot.q.qq.com/wiki/
- 群管理 API：https://bot.q.qq.com/wiki/develop/api-v2/server-inter/group/manage/
- 事件订阅：https://bot.q.qq.com/wiki/develop/api-v2/development/event/overview.html

---

## 测试用例（tests/evals.json）

```json
{
  "skill_name": "qq-group-manager",
  "evals": [
    {
      "id": 1,
      "prompt": "帮我审核当前所有的入群申请，等级低于10级的拒绝",
      "expected_behavior": [
        "调用获取入群申请 API",
        "对每个申请检查 QQ 等级 ≥ 10",
        "拒绝等级不足或回答错误的申请",
        "通过符合所有条件的申请"
      ]
    },
    {
      "id": 2,
      "prompt": "新成员张三进群了，他的昵称是「张三」不是「昵称-机型」格式，提醒他修改",
      "expected_behavior": [
        "检测到新成员入群事件",
        "检查昵称格式不符合「昵称-机型」",
        "向群发送 @ 提醒消息",
        "消息包含修改昵称的格式说明"
      ]
    },
    {
      "id": 3,
      "prompt": "我不想管理群了",
      "expected_behavior": [
        "不触发本 skill",
        "给出兜底建议或询问具体需求"
      ]
    }
  ]
}
```
