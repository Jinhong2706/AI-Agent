---
name: delete_skill
description: Removes an installed skill for the current user scope by skill name. Use this when the user asks to uninstall, remove, or delete a previously added skill.
version: 0.0.1
author: qqai
user-invocable: false
disable-model-invocation: false
tags: [skill, uninstall, delete, remove, skill_finder, delete_skill]
trigger-phrases:
  - 删除技能
  - 卸载技能
  - 移除技能
  - 取消安装技能
  - 删掉这个skill
timeout: 60s
---

# delete_skill 技能删除

## Purpose

为 Agent 提供与 `SkillRun` 实现一致的技能删除入口：根据当前请求上下文中的 `app_id`、`user_id`，结合参数中的技能名，调用 `skill_finder` 服务执行删除。

该技能仅负责删除动作本身，不返回技能列表；成功时返回固定成功结果对象。

## Core Rules & Constraints

### 与实现对齐的行为

| 规则 | 说明 |
|------|------|
| 技能名提取键 | 从 `parameters.fields` 按顺序匹配 `skill_name`、`skillName`、`skill`，命中第一个即使用。 |
| 默认值 | 若未命中任何键，`skill_name` 会以空字符串传入下游删除逻辑。 |
| 上下文来源 | `app_id` 取 `req.context.app_id`，`user` 取 `req.context.user_id`。 |
| 成功返回 | `Status_SUCCESS`，`result` 固定为 `{ "result": "success" }`。 |
| 失败返回 | 删除失败时返回 `Status_FAILED`，`error_code=500`，`error_message=err.Error()`。 |
| 400 分支说明 | 代码包含 `error_code=400` 分支（参数解析失败），但当前实现 `addSkillParamFromReq` 通常不返回 error。 |

## Input Requirements

### 调用方式

必须通过 `exec` 调用 `delete_skill`：

```
exec(
  "delete_skill --parameters '{
    \"skill_name\": \"generate_image\"
  }'"
)

exec(
  "delete_skill --parameters '{
    \"skillName\": \"skill_add\"
  }'"
)

exec(
  "delete_skill --parameters '{
    \"skill\": \"find_skills\"
  }'"
)
```

### parameters 字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `skill_name` | string | 否（推荐） | 首选字段名。 |
| `skillName` | string | 否 | 兼容字段名。 |
| `skill` | string | 否 | 兼容字段名。 |

> 建议始终显式传 `skill_name`，避免字段冲突与歧义。

## Output Format

### 成功

服务侧成功响应（`Status_SUCCESS`）：

```json
{
  "result": "success"
}
```

### 失败

删除失败（如下游仓库报错）时返回 `Status_FAILED`：

```json
{
  "error": {
    "error_code": 500,
    "error_message": "delete skill failed: xxx"
  }
}
```

## Error Handling

| 场景 | error_code（实现） | 可重试 | 处理建议 |
|------|-------------------|--------|----------|
| 参数解析失败（理论分支） | 400 | 否 | 检查请求结构与字段名 |
| 下游删除失败 | 500 | 视错误而定 | 核对技能名、用户/应用上下文后重试 |

## 与主 Agent 的协作流程

1. 从用户意图中确认要删除的技能名。  
2. 以 `skill_name` 传给 `delete_skill`。  
3. 成功则告知已删除；失败则透传错误并引导用户确认技能名。  

## 执行前检查清单

- [ ] 已拿到明确的目标技能名（优先填 `skill_name`）  
- [ ] 请求上下文包含正确 `app_id` 与 `user_id`  
- [ ] 已告知用户删除成功仅返回 `result=success`，不附带列表  

## Quality Checklist

- [ ] 不猜测技能名；无法确定时先向用户确认  
- [ ] 参数优先使用 `skill_name`，兼容键仅作兜底  
- [ ] 对失败信息保持原样，方便排查下游问题  
