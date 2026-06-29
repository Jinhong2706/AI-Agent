---
name: lighthouse-dev-workflow
description: 企微驱动的 Lighthouse 研发全流程 Skill。通过企微给 Knot 一个 TAPD 单，自动完成需求分析、方案设计、代码编写，方案评审时企微通知人工，评审通过后自动续写代码并交付 MR 和 TAPD 链接。
---

# Lighthouse Dev Workflow

## 概述

本 Skill 实现 **企微 → Knot → CodeBuddy → 企微** 的完整闭环研发流程。

**核心交互模式**：
- **输入**：用户在企微 @Knot 发送 TAPD 需求链接
- **执行**：Knot 在云工作区中自动完成需求分析、方案设计、代码编写
- **人工关卡**：方案评审时通过企微通知用户，用户在企微回复"通过"或修改意见
- **输出**：完成后通过企微推送 MR 链接 + TAPD 链接 + 改动摘要

**一句话流程**：
```
企微发 TAPD 链接 → 自动分析+设计 → 企微通知评审 → 企微回复通过/修改 → 自动编码+提交 → 企微推送 MR
```

---

## 前置条件

### 智能体配置要求

| 配置项 | 说明 |
|--------|------|
| **Client 工具** | 开启文件读写、命令执行、代码搜索 |
| **云工作区** | 绑定包含 `beian.tencentyun.com` 项目的工作区 |
| **TAPD MCP** | 配置 TAPD MCP，填入工蜂 token |
| **工蜂 MCP** | 配置工蜂 MCP，填入工蜂个人访问令牌 |
| **Knot 消息通知 MCP** | 配置企微消息通知 MCP，填入群聊 chatid |
| **企微机器人** | 在企微群添加 Knot 消息推送机器人或 Knot 智能机器人 |

### 企微消息通知 MCP 配置方法

1. 在企微群 → 消息推送 → 搜索「Knot消息通知」→ 添加
2. @Knot消息通知机器人 获取 chatid
3. 在 Knot 智能体配置页 → MCP → 添加「Knot消息通知」→ 填入 chatid

---

## 技能激活

当用户消息包含以下任一特征时，激活此技能：

- 包含 `tapd.woa.com` 的 URL
- "完成需求"、"开发需求"、"需求开发"、"帮我开发"
- "分析并开发"、"写代码"、"研发全流程"
- 用户发送 TAPD 需求链接（自动识别）

---

## 执行流程

### 阶段 0: 环境检测（自动，无需用户参与）

```bash
pwd
ls composer.json app/ routes/ config/
git status
git branch -a
```

确认：
- 在 `beian.tencentyun.com` 项目目录中（PHP Laravel 项目）
- Git 状态干净，无未提交更改

如果环境异常，**通过企微通知用户**：
```
⚠️ 工作区环境异常: [问题描述]
请检查后重新发送任务。
```

---

### 阶段 1: 需求分析（自动）

#### 1.1 解析 TAPD 需求

从用户消息中提取 TAPD URL，解析 `workspace_id` 和 `story_id`：

```
URL 格式: https://tapd.woa.com/tapd_fe/{workspace_id}/story/detail/{story_id}
```

调用 TAPD MCP：
- `stories_get` 获取需求标题、描述、状态、自定义字段
- `comments_get` 获取历史评论

#### 1.2 创建功能分支

```bash
git fetch origin master
git checkout master
git pull origin master
git checkout -b feature/{NNN}-{feature-name}
```

分支号 `{NNN}` 从需求名或已有分支递增。**必须从 master 最新代码创建**。

#### 1.3 生成 spec.md

创建 `specs/{branch-name}/spec.md`，包含：
- 需求概述、功能描述、用户场景
- 验收标准（可测试的条目）
- 技术约束
- 标记不明确处为 `[NEEDS CLARIFICATION]`（最多 3 个）

#### 1.4 需求澄清

如有 `[NEEDS CLARIFICATION]`，**通过企微逐个询问**：
```
📋 需求澄清 (1/N)

关于 [具体问题]，请确认：
A. [推荐选项]
B. [备选选项]
C. 其他（请说明）

请直接回复选项或说明。
```

每次只问一个问题，收到回复后更新 spec.md，再问下一个。

#### 1.5 同步 TAPD

- `stories_update` 将 spec.md 内容写入需求描述
- `comments_create` 添加评论: `【需求分析阶段】spec.md 已生成并同步`
- `stories_update` 流转状态到 `status_7`（需求已评审）

**自动进入阶段 2，无需等待。**

---

### 阶段 2: 方案设计（自动）

#### 2.1 分析项目代码

读取相关目录了解现有架构：
- `routes/` - 路由定义
- `app/Http/Controllers/` - 控制器
- `app/Models/` - 模型
- `app/Services/` - 服务层
- `config/` - 配置文件

#### 2.2 生成 plan.md

创建 `specs/{branch-name}/plan.md`，包含：
- 技术架构设计
- 模块划分和文件路径（精确到要修改/新建的文件）
- 数据库变更（如适用）
- API 设计（如适用）
- 实施步骤
- 风险评估

#### 2.3 同步 TAPD

- `stories_update` 流转到 `status_38`（方案设计），填写 `custom_field_67`（迭代目标）
- `stories_update` 将 plan.md 写入 `custom_field_147`（方案设计字段）

#### 2.4 🚧 企微通知方案评审（唯一人工关卡）

**通过企微发送方案评审通知**：

```
🚧 方案评审 - {需求标题}

📌 TAPD: https://tapd.woa.com/tapd_fe/{workspace_id}/story/detail/{story_id}
📄 方案摘要:
{plan.md 的关键要点，3-5 行}

📝 涉及修改:
{列出要修改/新建的文件清单}

请回复:
✅ "通过" - 开始编码
📝 "修改: [修改意见]" - 修改方案后重新评审
```

**然后停止执行，等待用户在企微回复。**

---

### 阶段 2.5: 处理评审反馈

根据用户企微回复：

**如果回复"通过"/"OK"/"可以"等肯定词**：
- `stories_update` 流转到 `status_39`（方案已评审）
- 填写必填字段: `custom_field_82`（开发工作量）、`custom_field_133`（方案评审人）
- 自动进入阶段 3

**如果回复"修改: xxx"或包含修改意见**：
- 根据意见修改 plan.md
- 重新同步到 TAPD
- 再次通过企微发送评审通知（回到阶段 2.4）

---

### 阶段 3: 任务拆分（自动）

#### 3.1 生成 tasks.md

创建 `specs/{branch-name}/tasks.md`，按实施步骤拆分任务，粒度 0.5-3 天。

#### 3.2 创建 TAPD 子任务

调用 `tasks_create` 为每个任务创建 TAPD 子任务，关联父需求。

#### 3.3 流转状态

- `stories_update` 流转到 `planned`（已排期），填写 `custom_field_160`（QTA集成 = "否"）

**自动进入阶段 4。**

---

### 阶段 4: 代码开发（自动）

#### 4.1 流转子任务

将当前子任务流转到 `progressing`（进行中）。

#### 4.2 按任务编码

按 tasks.md 逐任务实施：
1. 读取要修改的现有代码
2. 理解代码风格和结构
3. 编写/修改代码
4. 在 tasks.md 中标记完成

**编码规范**：
- PHP PSR-12 标准 + Laravel 最佳实践
- 禁止字符串拼接 SQL，使用 Eloquent ORM 或参数化查询
- 不硬编码敏感信息，使用环境变量
- 所有用户输入必须验证
- 函数带文档注释，保留 TAPD 需求编号

#### 4.3 提交代码

```bash
git add .
git commit -m "feat: {功能描述} --story={story_id}"
git push origin feature/{NNN}-{feature-name}
```

#### 4.4 创建 MR

调用工蜂 MCP `create_merge_request`：
- source_branch: `feature/{NNN}-{feature-name}`
- target_branch: `master`
- title: `feat: {需求标题} --story={story_id}`
- description: 包含需求链接、改动摘要、测试建议

---

### 阶段 5: 交付通知（通过企微推送）

#### 5.1 同步 TAPD

- 流转所有子任务到 `done`（已完成）
- `comments_create` 添加评论:
  ```
  【开发阶段】代码已提交，MR 已创建
  - 分支: feature/{NNN}-{feature-name}
  - MR: {MR链接}
  - 改动文件: {文件列表}
  ```

#### 5.2 企微推送交付结果

**通过企微发送最终交付通知**：

```
✅ 需求开发完成 - {需求标题}

📌 TAPD: https://tapd.woa.com/tapd_fe/{workspace_id}/story/detail/{story_id}
🔀 MR: {MR链接}
🌿 分支: feature/{NNN}-{feature-name}

📝 改动摘要:
{列出修改/新建的文件及简要说明}

⏭ 后续操作:
1. Code Review MR
2. 本地验证测试
3. 合入 master
```

---

## TAPD 状态流转速查

### 需求状态路径

| 阶段 | 目标状态 | 状态码 | 必填字段 |
|------|----------|--------|----------|
| 阶段 1 完成 | 需求已评审 | `status_7` | - |
| 阶段 2 开始 | 方案设计 | `status_38` | `custom_field_67` |
| 评审通过 | 方案已评审 | `status_39` | `custom_field_82`, `custom_field_133` |
| 阶段 3 完成 | 已排期 | `planned` | `custom_field_160` |

### 任务状态路径

| 阶段 | 状态 | 状态码 |
|------|------|--------|
| 创建 | 未开始 | `open` |
| 开发中 | 进行中 | `progressing` |
| 完成 | 已完成 | `done` |

---

## MCP 工具依赖

| 工具来源 | 工具名 | 用途 |
|----------|--------|------|
| **TAPD MCP** | `stories_get` | 获取需求详情 |
| **TAPD MCP** | `stories_update` | 更新需求状态/字段 |
| **TAPD MCP** | `comments_get` | 获取需求评论 |
| **TAPD MCP** | `comments_create` | 创建评论 |
| **TAPD MCP** | `tasks_create` | 创建子任务 |
| **TAPD MCP** | `tasks_update` | 更新子任务状态 |
| **工蜂 MCP** | `create_branch` | 创建分支 |
| **工蜂 MCP** | `create_merge_request` | 创建 MR |
| **Knot 消息通知 MCP** | `send_message` | 企微群发送消息通知 |
| iWiki MCP（可选） | `getDocument` | 获取 iWiki 文档 |

## Client 工具依赖

| 工具 | 用途 |
|------|------|
| 文件读取 | 读取项目代码文件 |
| 文件写入 | 创建/修改代码文件 |
| 命令执行 | 执行 Git、Shell 命令 |
| 代码搜索 | 搜索项目中的代码模式 |

---

## 企微交互协议

本 Skill 通过企微实现以下交互：

### 主动通知场景

| 时机 | 消息内容 |
|------|----------|
| 环境异常 | ⚠️ 告警 + 修复建议 |
| 需求澄清 | 📋 逐个问题 + 选项 |
| 方案评审 | 🚧 方案摘要 + TAPD链接 + 等待回复 |
| 开发完成 | ✅ MR链接 + TAPD链接 + 改动摘要 |

### 用户回复处理

| 用户回复 | 系统行为 |
|----------|----------|
| "通过" / "OK" / "可以" / "继续" | 方案评审通过，进入编码 |
| "修改: xxx" / 包含修改意见 | 修改方案，重新评审 |
| "A" / "B" / "C" / 具体说明 | 需求澄清回答，更新 spec |

---

## 安全规范

1. **SQL 安全**: 100% 使用 Eloquent ORM 或参数化查询，禁止字符串拼接 SQL
2. **敏感信息**: 不在代码中硬编码密码、Token、密钥，使用环境变量
3. **输入验证**: 所有用户输入必须验证和过滤
4. **分支安全**: 不在 master/main 上直接提交代码
5. **Token 安全**: 个人 Token 不硬编码，使用环境变量

---

## 错误处理

| 错误场景 | 处理方式 |
|----------|----------|
| TAPD 状态流转失败 | 检查必填字段，企微通知用户 |
| 代码冲突 | 自动 merge master，冲突时企微通知 |
| MCP 调用失败 | 重试 1 次，仍失败则企微通知 |
| 工作区离线 | 企微通知用户检查工作区状态 |

---

## 使用示例

### 典型用法（企微）

```
@Knot机器人 帮我开发这个需求 https://tapd.woa.com/tapd_fe/10132091/story/detail/xxx
```

### 指定只分析不编码

```
@Knot机器人 分析这个需求并生成方案，暂不开发 https://tapd.woa.com/tapd_fe/10132091/story/detail/xxx
```

### 评审回复

```
通过
```
或
```
修改: 1. 校验逻辑应该放在 Service 层而不是 Controller 2. 需要增加单元测试
```

---

## Knot 智能体配置清单

在 https://knot.woa.com 创建智能体时，按以下步骤配置：

1. **新建智能体** → 选择「自主规划式」
2. **添加 Client 工具** → 开启文件读写、命令执行、代码搜索
3. **添加 MCP**:
   - TAPD MCP（填入 token）
   - 工蜂 MCP（填入个人访问令牌）
   - Knot 消息通知 MCP（填入企微群 chatid）
   - iWiki MCP（可选，填入 token）
4. **添加 Skills** → 上传本 Skill 包
5. **创建云工作区** → 绑定 `beian.tencentyun.com` 项目目录
6. **配置企微** → 在企微群添加 Knot 消息推送/智能机器人，绑定工作区
7. **发布智能体**

---

**版本**: 2.0.0
**最后更新**: 2026-03-11
**维护者**: DNS Team
