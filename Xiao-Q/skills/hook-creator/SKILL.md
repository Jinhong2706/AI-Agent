---
name: hook-creator
description: 创建、修改和诊断 Claude Code hooks 配置。当用户要求添加自动化工作流（如"每次编辑后格式化"、"提交前检查"、"阻止删除文件"）、创建/修改/删除 hook、检查优化现有 hooks 配置、或描述包含"每次"、"自动"、"之前/之后"、"当...时"、"阻止"、"通知我"等关键词时使用。
---

# Hook Creator 技能

**开始时声明：** "使用 hook-creator 技能创建/诊断 hooks 配置。"

## 核心流程

**原则：** 场景识别 → 模板匹配/对话构建 → 确定配置位置 → 验证 → 写入 → 确认生效。

---

## 一、触发关键词

| 类型 | 关键词示例 |
|------|------------|
| 直接触发 | 创建 hook、添加 hook、修改 hook、删除 hook |
| 场景触发 | 每次、自动、之前/之后、当...时、阻止、通知我、提交前、编辑后 |
| 诊断触发 | 检查 hooks、优化 hooks、hooks 有问题、hook 不工作 |

---

## 二、模板库

### 通知类模板

**桌面通知（Notification）**

用户需求："Claude 完成时通知我"、"需要输入时提醒我"

| 平台 | 命令 |
|------|------|
| macOS | osascript -e "display notification \"Claude Code needs your attention\" with title \"Claude Code\"" |
| Linux | notify-send "Claude Code" "Claude Code needs your attention" |
| Windows | powershell.exe -Command "[System.Reflection.Assembly]::LoadWithPartialName(\"System.Windows.Forms\"); [System.Windows.Forms.MessageBox]::Show(\"Claude Code needs your attention\", \"Claude Code\")" |

配置示例：
```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "",
        "hooks": [{ "type": "command", "command": "<平台命令>" }]
      }
    ]
  }
}
```

---

### 格式化类模板

**Prettier 自动格式化（PostToolUse）**

用户需求："编辑后自动格式化"、"每次写文件后格式化"

参数化选项：
- 包管理器：npm / bun / yarn / pnpm
- 匹配器：Edit|Write（默认）或仅 Write

配置示例：
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command", "command": "jq -r \".tool_input.file_path\" | xargs <包管理器> prettier --write" }
        ]
      }
    ]
  }
}
```

---

### 保护类模板

**阻止敏感文件编辑（PreToolUse）**

用户需求："阻止修改 .env"、"防止删除重要文件"

参数化选项：
- 受保护模式列表：.env、package-lock.json、.git/、*.secret 等

需要创建脚本文件 .claude/hooks/protect-files.sh：
```bash
#!/bin/bash
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r ".tool_input.file_path // empty")

PROTECTED_PATTERNS=(".env" "package-lock.json" ".git/")

for pattern in "${PROTECTED_PATTERNS[@]}"; do
  if [[ "$FILE_PATH" == *"$pattern"* ]]; then
    echo "Blocked: $FILE_PATH matches protected pattern \"$pattern\"" >&2
    exit 2
  fi
done
exit 0
```

配置示例：
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/protect-files.sh" }
        ]
      }
    ]
  }
}
```

---

### 上下文类模板

**压缩后注入上下文（SessionStart）**

用户需求："压缩后提醒项目约定"、"每次压缩后注入规则"

参数化选项：
- 注入内容：项目约定、最近工作、提醒事项

配置示例：
```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "compact",
        "hooks": [
          { "type": "command", "command": "echo \"Reminder: use Bun, not npm. Run bun test before committing.\"" }
        ]
      }
    ]
  }
}
```

---

### 审计类模板

**配置更改审计（ConfigChange）**

用户需求："记录配置文件变更"、"审计 settings 修改"

配置示例：
```json
{
  "hooks": {
    "ConfigChange": [
      {
        "matcher": "",
        "hooks": [
          { "type": "command", "command": "jq -c \"{timestamp: now | todate, source: .source, file: .file_path}\" >> ~/claude-config-audit.log" }
        ]
      }
    ]
  }
}
```

---

### 环境类模板

**环境变量自动加载（CwdChanged + SessionStart）**

用户需求："切换目录时加载 .envrc"、"自动加载 direnv"

配置示例：
```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          { "type": "command", "command": "direnv export bash > \"$CLAUDE_ENV_FILE\"" }
        ]
      }
    ],
    "CwdChanged": [
      {
        "hooks": [
          { "type": "command", "command": "direnv export bash > \"$CLAUDE_ENV_FILE\"" }
        ]
      }
    ]
  }
}
```

---

### 权限类模板

**自动批准特定权限（PermissionRequest）**

用户需求："跳过 ExitPlanMode 提示"、"自动批准某些工具"

参数化选项：
- 目标工具：ExitPlanMode、Bash(git *)、Read 等

配置示例：
```json
{
  "hooks": {
    "PermissionRequest": [
      {
        "matcher": "ExitPlanMode",
        "hooks": [
          { "type": "command", "command": "echo \"{\\\"hookSpecificOutput\\\": {\\\"hookEventName\\\": \\\"PermissionRequest\\\", \\\"decision\\\": {\\\"behavior\\\": \\\"allow\\\"}}}\"" }
        ]
      }
    ]
  }
}
```

---

### 高级类模板

**基于提示的验证（Stop）**

用户需求："停止前检查任务是否完成"、"让 Claude 判断是否可以停止"

配置示例：
```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Check if all tasks are complete. If not, respond with {\"ok\": false, \"reason\": \"what remains to be done\"}."
          }
        ]
      }
    ]
  }
}
```

**基于代理的验证（Stop）**

用户需求："停止前验证测试通过"、"多轮检查后才能停止"

配置示例：
```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "agent",
            "prompt": "Verify that all unit tests pass. Run the test suite and check the results. $ARGUMENTS",
            "timeout": 120
          }
        ]
      }
    ]
  }
}
```

**HTTP 回调（PostToolUse）**

用户需求："发送事件到外部服务"、"POST 工具使用记录"

配置示例：
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "hooks": [
          {
            "type": "http",
            "url": "http://localhost:8080/hooks/tool-use",
            "headers": { "Authorization": "Bearer $MY_TOKEN" },
            "allowedEnvVars": ["MY_TOKEN"]
          }
        ]
      }
    ]
  }
}
```

---

## 三、对话式构建流程

当用户需求不匹配模板时，通过问答逐步收集信息。**一次一个问题**。

### 问题序列

**Q1: 触发时机**

"这个 hook 应该在什么时机触发？"

| 选项 | 事件类型 |
|------|----------|
| 工具执行前（可阻止） | PreToolUse |
| 工具执行后 | PostToolUse |
| 工具执行失败后 | PostToolUseFailure |
| Claude 需要输入时 | Notification |
| 会话开始/压缩后 | SessionStart |
| 会话结束时 | SessionEnd |
| 目录切换时 | CwdChanged |
| 文件变更时 | FileChanged |
| 配置文件变更时 | ConfigChange |
| Claude 响应完成时 | Stop |
| 提交 prompt 前 | UserPromptSubmit |
| 权限对话框出现时 | PermissionRequest |
| 压缩前/后 | PreCompact / PostCompact |
| 其他（列出完整事件表） | — |

---

**Q2: 匹配条件**

"需要匹配哪些工具或条件？"

根据事件类型提供选项：

| 事件类型 | matcher 选项 |
|----------|--------------|
| PreToolUse/PostToolUse | Bash、Edit、Write、Read、Glob、Grep、Edit|Write、mcp__.* 等 |
| SessionStart | startup、resume、clear、compact |
| Notification | permission_prompt、idle_prompt、auth_success |
| FileChanged | 文件名列表（如 .envrc|.env） |
| ConfigChange | user_settings、project_settings、local_settings |
| 无匹配器的事件 | 不询问，直接跳过 |

可选追问：if 字段（更精确过滤）
"是否需要按命令参数过滤？例如仅匹配 git * 命令？"

---

**Q3: 执行操作**

"触发后要执行什么操作？"

| 选项 | hook 类型 |
|------|-----------|
| 运行 shell 命令 | command |
| 让 Claude 判断（单轮） | prompt |
| 让 Claude 执行多轮验证 | agent |
| 发送到外部 HTTP 服务 | http |
| 调用 MCP 工具 | mcp_tool |

根据类型追问具体内容：
- command: "具体命令是什么？"
- prompt: "判断条件是什么？返回什么格式？"
- agent: "验证任务是什么？超时时间？"
- http: "URL 是什么？需要哪些 headers？"

---

**Q4: 是否阻断**

"是否需要阻止操作或返回决策？"

| 选项 | 说明 |
|------|------|
| 仅执行，不阻断 | exit 0，操作继续 |
| 阻止操作 | exit 2 或 decision: "block" |
| 返回 JSON 决策 | 允许/拒绝/询问用户 |

---

**Q5: 配置位置**

"这个 hook 应该配置在哪里？"

| 选项 | 文件路径 | 范围 |
|------|----------|------|
| 全局（所有项目） | ~/.claude/settings.json | 个人偏好 |
| 项目（团队共享） | .claude/settings.json | 团队规范 |
| 项目本地（仅本机） | .claude/settings.local.json | 个人项目配置 |

---

## 四、验证与写入流程

### 步骤 0：确定配置位置

根据用户选择，确定目标文件：
- 全局 → ~/.claude/settings.json
- 项目 → .claude/settings.json
- 项目本地 → .claude/settings.local.json

### 步骤 1：去重检查

读取目标文件，检查是否已存在相同 event+matcher 的 hook。

**去重逻辑**：
- 相同 event + 相同 matcher → 提示用户选择：
  - A) 保留现有 hook
  - B) 替换为新 hook
  - C) 添加为并行 hook（多个 hook 组）
- 相同 event + 不同 matcher → 直接追加
- 相同 event + 无 matcher → 检查是否已有无 matcher 的 hook

### 步骤 2：JSON 语法验证

确保生成的配置符合 schema：
- 必须字段：type、command/prompt/url
- matcher 格式正确
- hooks 数组结构正确

### 步骤 3：命令检查

检查命令依赖：
- jq 是否安装（大多数 hook 需要 JSON 解析）
- 格式化工具是否存在
- 脚本文件是否可执行（提示 chmod +x）
- 平台兼容性（如 osascript 仅 macOS）

### 步骤 4：合并写入

**重要**：保留现有配置，追加新 hook。不要替换整个文件。

使用 Edit 工具，在现有 hooks 对象中追加：
```json
{
  "hooks": {
    "ExistingEvent": [...],  // 保留
    "NewEvent": [...]        // 新增
  }
}
```

如果是首次创建 hooks，添加整个 hooks 块。

### 步骤 5：确认生效

写入后提示用户：
```
Hook 已写入 <文件路径>

验证方式：
1. 运行 /hooks 查看配置
2. 触发对应事件测试

注意：如果 hook 未出现在 /hooks 中，可能需要：
- 重启会话（settings watcher 仅监视启动时已有 settings 文件的目录）
- 或打开 /hooks 菜单一次以重新加载配置
```

---

## 五、动态生成

当用户描述不匹配模板的需求时，通过意图识别生成 hook 配置。

### 意图识别示例

| 用户输入 | 提取信息 | 生成方向 |
|----------|----------|----------|
| 每次提交前检查 lint | 触发：git 操作前 → 执行：lint 检查 → 阻断：失败时阻止 | PreToolUse, matcher: Bash, if: Bash(git commit*), command: lint 检查脚本 |
| 当配置文件变了记录日志 | 触发：配置变更 → 执行：写日志 | ConfigChange, command: jq 写入日志 |
| 阻止删除 node_modules | 触发：删除操作 → 阻断：阻止 | PreToolUse, matcher: Bash, if: Bash(rm *node_modules*), exit 2 |
| 每次编辑 ts 文件后运行 tsc | 触发：编辑后 → 条件：ts 文件 → 执行：tsc | PostToolUse, matcher: Edit|Write, if: Edit(*.ts), command: tsc |
| Claude 停止前确认任务完成 | 触发：停止 → 判断：任务完成？ | Stop, type: prompt, prompt: 检查任务 |

### 动态生成步骤

1. 提取关键信息：触发时机、目标工具/条件、执行操作、是否阻断
2. 映射到事件类型：根据触发时机选择事件
3. 构建 matcher/if：根据目标工具/条件
4. 构建命令或 prompt：根据执行操作
5. 询问配置位置：全局/项目/项目本地
6. 验证并写入

---

## 六、诊断功能

当用户说"检查 hooks"、"优化 hooks"、"hook 不工作"时执行诊断。

### 诊断项

| 诊断项 | 操作 | 发现问题时的建议 |
|--------|------|------------------|
| JSON 语法 | 验证 settings 文件 JSON 有效 | 显示错误位置，提示修复 |
| 重复 hook | 检查相同 event+matcher 组合 | 建议合并或删除重复 |
| 命令不可用 | 检查依赖工具（jq、prettier 等） | 提示安装缺失工具 |
| 脚本不可执行 | 检查 .claude/hooks/*.sh 权限 | 提示 chmod +x |
| matcher 不匹配 | 检查 matcher 是否与实际工具名匹配 | 提示正确的 matcher 值 |
| 平台不兼容 | 检查命令是否适配当前平台 | 提示平台替代方案 |

### 优化建议

| 发现 | 建议 |
|------|------|
| 多个相似 hook | 可用 if 字段合并为一个 hook 组 |
| 无 matcher 的 PostToolUse | 添加 matcher 限制触发范围 |
| 长命令字符串 | 建议提取为脚本文件 |
| 缺少 timeout | 建议添加 timeout 防止卡住 |

### 诊断流程

1. 读取所有 settings 文件（全局、项目、项目本地）
2. 合并 hooks 配置进行分析
3. 输出诊断报告和建议列表
4. 用户选择要执行的修复操作

---

## 七、Hook 事件完整列表

| 事件 | 触发时机 | matcher 支持 |
|------|----------|--------------|
| SessionStart | 会话开始或恢复 | startup/resume/clear/compact |
| UserPromptSubmit | 用户提交 prompt 前 | 不支持 |
| UserPromptExpansion | 命令展开为 prompt 前 | 命令名称 |
| PreToolUse | 工具执行前（可阻止） | 工具名称 |
| PermissionRequest | 权限对话框出现 | 工具名称 |
| PermissionDenied | 工具调用被拒绝 | 工具名称 |
| PostToolUse | 工具执行成功后 | 工具名称 |
| PostToolUseFailure | 工具执行失败后 | 工具名称 |
| PostToolBatch | 批量工具调用完成后 | 不支持 |
| Notification | Claude 发送通知 | 通知类型 |
| SubagentStart | 子代理启动 | 代理类型 |
| SubagentStop | 子代理结束 | 代理类型 |
| TaskCreated | 任务创建 | 不支持 |
| TaskCompleted | 任务完成 | 不支持 |
| Stop | Claude 响应完成 | 不支持 |
| StopFailure | API 错误导致停止 | 错误类型 |
| TeammateIdle | 团队成员即将空闲 | 不支持 |
| InstructionsLoaded | CLAUDE.md 加载 | 加载原因 |
| ConfigChange | 配置文件变更 | 配置源 |
| CwdChanged | 工作目录切换 | 不支持 |
| FileChanged | 文件变更 | 文件名 |
| WorktreeCreate | 工作树创建 | 不支持 |
| WorktreeRemove | 工作树移除 | 不支持 |
| PreCompact | 压缩前 | manual/auto |
| PostCompact | 压缩后 | manual/auto |
| Elicitation | MCP 请求用户输入 | 服务器名称 |
| ElicitationResult | 用户响应 MCP 请求 | 服务器名称 |
| SessionEnd | 会话结束 | 结束原因 |

---

## 八、退出代码与 JSON 输出

### 退出代码

| 代码 | 含义 |
|------|------|
| 0 | 操作继续，stdout 内容注入上下文（部分事件） |
| 2 | 阻止操作，stderr 内容反馈给 Claude |
| 其他 | 操作继续，显示 hook error 通知 |

### JSON 输出格式（exit 0 时）

**PreToolUse 决策**：
```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow|deny|ask",
    "permissionDecisionReason": "原因说明",
    "updatedInput": { "file_path": "修改后的参数" }
  }
}
```

**Stop/PostToolUse 阻止**：
```json
{
  "decision": "block",
  "reason": "原因说明",
  "systemMessage": "显示给用户的消息"
}
```

**注入上下文**：
```json
{
  "hookSpecificOutput": {
    "hookEventName": "事件名",
    "additionalContext": "注入到 Claude 上下文的文本"
  }
}
```

---

## 九、常见问题排查

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| hook 不触发 | matcher 不匹配 | 检查工具名称大小写 |
| hook 不触发 | settings watcher 未监视 | 重启会话或打开 /hooks |
| JSON 解析错误 | shell 配置文件有 echo | 包装 echo 在交互式检查中 |
| Stop hook 无限循环 | 未检查 stop_hook_active | 添加 if stop_hook_active: exit 0 |
| 命令找不到 | 路径问题 | 使用绝对路径或 $CLAUDE_PROJECT_DIR |
| jq 找不到 | 未安装 | brew install jq / apt-get install jq |

---

## 十、参考资源

- 官方参考：https://code.claude.com/docs/zh-CN/hooks
