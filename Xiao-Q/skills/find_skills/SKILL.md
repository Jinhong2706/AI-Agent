---
name: find_skills
description: Helps users discover and install agent skills when they ask questions like "how do I do X", "find a skill for X", "is there a skill that can...", or express interest in extending capabilities. This skill should be used when the user is looking for functionality that might exist as an installable skill.
version: 0.0.1
author: qqai
user-invocable: false
disable-model-invocation: false
tags: [skill, discovery, search, routing, skill_finder, find_skills]
trigger-phrases:
  - 有哪些技能能做
  - 找个能XX的技能
  - 技能搜索
  - 哪个技能可以
  - 查一下技能库
timeout: 60s
---

# find_skills 技能发现与检索

## Purpose

为 Agent 提供**与 `SkillRun` 实现一致**的标准化技能检索入口：将用户任务或能力描述压缩为检索字符串 `parameters.query`，由 `skill_finder` 服务调用下游技能搜索（分页，每页最多 10 条），聚合为有序候选列表；返回结构中 **`result` 为对象**，内含数组字段 `result`，元素为 `skill_id` / `name` / `desc` / **`path`**（技能根路径前缀，见下）。

本技能**不执行**任何业务工具，仅返回可路由的元数据；选中技能后应 **`skill_read` 拉取正式 SKILL**，再按文档调用对应 `skill_run`。

## Core Rules & Constraints

### 与实现对齐的行为

| 规则 | 说明 |
|------|------|
| **必填 `parameters`** | `req.Parameters` 缺失时失败，`error_code` 为 **2**（参数类）。 |
| **必填 `query` 且为 string** | 必须在 `parameters` 的 `fields` 中提供 `query`，且为 **字符串**；否则失败，典型文案：`missing parameters.query`、`parameters.query must be a string`。当用户未指定具体 Skill 类别时（例如“top”“热门”），`query` 传单个空格 `" "`。 |
| **查询语义** | `query` 概括「用户想做什么」或「需要什么能力」；可与用户原话一致或简短重组。若用户未指定具体 Skill 类别（仅表示想找技能，或说“top/热门 skill”这类泛化请求），使用 `" "` 作为兜底查询。 |
| **结果条数** | 逻辑层使用配置 `need_size`，未配置或 ≤0 时默认 **10**；仓库层按页拉取直至凑够条数或无 `has_more`。 |
| **字段映射** | `skill_id`、`name` 均来自搜索服务返回的技能 **ID**；`desc` 为技能 **description**；**`path`** 来自服务七彩石配置 **`skill_path`**（可热更新），**不是**搜索服务逐条返回的字段。 |
| **`path` 语义** | 同一次成功响应里，每条候选的 `path` **相同**，表示宿主侧 SKILL 所在目录（或挂载根路径）的前缀；与 `skill_id` 组合用于 `skill_read`/安装（具体拼接规则以运行环境约定为准，例如 `{path}/{skill_id}/SKILL.md`）。未配置时可能为空串。 |
| **空结果** | 搜索无命中时返回 **成功** + `result.result == []`，不是业务失败。 |
| **下游错误** | `SearchSkills` 等调用失败时返回 **失败**，`error_code` 为 **1**，`error_message` 为错误信息。 |

## Input Requirements

### 调用方式

**必须通过 `exec` 调用**：本技能只能使用 `exec(...)` 执行 `find_skills` 命令，不要改用函数调用、HTTP、或其他工具入口；否则会无法正确触发检索流程。

```
exec(
  "find_skills --parameters '{
    \"query\": \"文生图、图生图、改图片风格\"
  }'"
)

exec(
  "find_skills --parameters '{
    \"query\": \"定时提醒、闹钟、备忘\"
  }'"
)

exec(
  "find_skills --parameters '{
    \"query\": \"理解图片内容、看图答题\"
  }'"
)
```

### parameters 字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `query` | string | 是 | 传给技能搜索服务的检索用语。 |

### query 最佳实践

| 做法 | 示例 |
|------|------|
| 任务意图概括 | 「用户上传图后要改成吉卜力风格」优于单独一个词「图」 |
| 并列能力关键词 | 「提醒 闹钟 日程」 |
| 未指定类别时 | 传单个空格 `" "`（例如“top skill”“热门 skill”；不要造词或猜测类别） |
| 避免 | 整段对话原样粘贴（除非确有区分度）、纯标点、无含义单字（上述兜底空串场景除外） |

## Output Format

### 成功（有命中）

Gateway / 封装层若将 `SkillRunResponse` 展开为通用 envelope，语义上应对齐 success + `result` 内层结构。**服务侧**成功时 `Status_SUCCESS` 的 `Result`（`structpb`）为：

```json
{
  "result": [
    {
      "skill_id": "generate_image",
      "name": "generate_image",
      "desc": "提供文生图与图生图能力……",
      "path": "/data/skills"
    }
  ]
}
```

其中 `path` 为配置 `skill_path` 的当前值，示例值仅作演示。

无命中：

```json
{
  "result": []
}
```

### 失败

参数或类型错误（`queryFromParameters` 失败）示例：`Status_FAILED`，`ErrorInfo.ErrorCode` **2**，`ErrorMessage` 为具体原因。

下游检索失败示例：`Status_FAILED`，`ErrorInfo.ErrorCode` **1**，`ErrorMessage` 为 `err.Error()`。

构建 `structpb` 失败时，实现可能返回 **Go error**（非仅 `Status_FAILED`），Agent 侧应按网关约定处理。

## Error Handling

| 场景 | error_code（实现） | 可重试 | 处理建议 |
|------|-------------------|--------|----------|
| 缺少 `parameters` | 2 | 否 | 补全 JSON |
| 缺少或非 string 的 `query` | 2 | 否 | 修正 `parameters.fields.query` |
| 下游 `SearchSkills` 失败 | 1 | 视 RPC | 退避重试并记录 |
| 空列表 | —（成功） | 不适用 | 改写或放宽 `query` |

## 与主 Agent 的协作流程

1. **澄清需求**（可选）→ 形成简短能力描述。  
2. **调用 `find_skills`**，传入 `query`（如“top/热门 skill”这类未指定类别请求，传 `" "`）。  
3. **解读 `result.result`**：多条候选时结合 `desc` 与用户语境选型；**用 `path` + `skill_id` 按环境约定定位 SKILL**（`path` 在列表内相同）；空列表则换问法或兜底。  
4. **下游**：对选定项 `skill_read`（路径由 `path` 与 `skill_id` 决定）→ 再 `skill_run` 目标技能（参数以目标 SKILL 为准）。

## 执行前检查清单

- [ ] `parameters` 存在且可被解析为 `Struct`  
- [ ] `query` 存在且为 string（未指定具体 Skill 类别，如“top/热门”，传 `" "`）  
- [ ] 明确本调用只返回候选，不执行业务  
- [ ] 空列表时有备选 query 或用户引导策略  

## Quality Checklist

- [ ] `query` 与用户任务对齐，利于相关技能排序靠前  
- [ ] 不伪造技能列表；完全信任搜索结果  
- [ ] 选型后必须读目标 SKILL 再传参，避免仅凭 `desc` 猜必填字段；**`skill_read` 路径依赖 `path` 与 `skill_id`，勿假设全局固定目录**  
- [ ] 不把「图片里有什么」写进 `query` 来替代用户真实任务（本技能是**文本检索**，不负责读图）  