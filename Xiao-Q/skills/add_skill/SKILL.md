---
name: add_skill
description: 为用户安装技能。通过 skill_name 绑定已有技能，或通过 url 传入 .zip / skill.md 链接自动注册技能。
version: 0.0.3
author: qqai
user-invocable: false
disable-model-invocation: false
tags: [skill, install, add, bind, url, upload, zip]
trigger-phrases:
  - 安装技能
  - 添加技能
  - 给我开通技能
  - 帮我绑定技能
  - 通过链接安装技能
timeout: 30s
---

# add_skill

安装或绑定技能到用户账号。支持两种方式：

1. **skill_name** — 直接绑定已有技能
2. **url** — 传入 `.zip` 或 `skill.md` 的下载链接，服务端自动解析并注册

两个参数**至少提供一个**，`url` 非空时优先使用 URL 模式（`skill_name` 可省略）。

> 无需预先读取或校验 URL 内容，直接传入即可，服务端会自行校验并返回错误信息。

## 调用方式

必须通过 `exec` 调用。

### 按名称安装

```
exec("add_skill --parameters '{\"skill_name\": \"code_review\"}'")
```

### 按 URL 安装

```
exec("add_skill --parameters '{\"url\": \"http://example.com/xxx/my_skill.zip\"}'")
```

```
exec("add_skill --parameters '{\"url\": \"http://example.com/xxx/skill.md\"}'")
```

## parameters

| 字段 | 类型 | 说明 |
|------|------|------|
| `skill_name` / `skillName` / `skill` | string | 要安装的技能名称，二选一 |
| `url` | string | 技能资源下载链接（`.zip` 或 `.md`），二选一 |

## 成功响应

```json
{ "status": "SUCCESS", "result": { "result": "success" } }
```

## 失败处理

失败时返回 `Status_FAILED`，`ErrorCode` 为 1，`ErrorMessage` 包含具体原因（参数缺失、URL 不可访问、zip 格式错误、skill.md 缺少元信息等）。按 `error_message` 提示用户即可。

## 协作流程

- 若用户给了技能名 → 直接用 `skill_name` 调用
- 若用户给了链接 → 直接用 `url` 调用，不需要先读取链接内容
- 若不确定技能名 → 先调用 `find_skills` 搜索，再用返回的 `skill_id` 安装