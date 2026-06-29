# Script Contracts

Backend Forge v0.1.0 起提供最小可执行脚本闭环。本文定义脚本职责、稳定输出和降级路径。

## 约定

所有 `scripts/` 引用都相对于 `backend-forge` skill 安装目录，不是用户项目目录。

发布前必须运行：

```text
bash scripts/validate_release.sh
```

运行时脚本缺失、不可执行或失败时，不得静默忽略；必须说明降级原因，并回到手动扫描、LLM 判断和明确确认。

## 已落地脚本

### detect_project_root_state.py

输入：

```text
detect_project_root_state.py <project_root>
```

输出：

```text
JSON: {"root_type": "...", "forge_enabled": true/false, "evidence": [...]}
```

降级：使用 `rg --files`、依赖文件和入口文件手动判断。

### classify_task.sh

输入：

```text
classify_task.sh "<user_request>"
```

输出：

JSON:

- `mode`
- `policy`
- `confidence`
- `guardrails_check`

降级：按 [task_routing.md](task_routing.md) 手动路由。

### bf_session.sh

输入：

```text
bf_session.sh --project-root <project_root> init|update|read|reset|validate
```

职责：

- 记录当前阶段、模式、执行策略。
- 记录目标、架构、数据、安全、测试闭环确认状态。
- 记录当前子单元、改动契约和验证状态。

### gate_check.py

输入：

```text
gate_check.py --project-root <project_root> --target-path <file>
```

输出 JSON：

- `decision`: `allow` / `block` / `would_block`
- `gate`
- `reason`
- `target_kind`

核心阻断：

- G01：session 不存在。
- G05：未进入实现阶段。
- G10：目标/架构/数据/安全/测试闭环未确认。
- G11：当前子单元未冻结。
- G15：改动契约缺失或未确认。

### validate_output.sh

输入：

```text
validate_output.sh [--require-complete] < output.txt
```

输出：

- 检查 `[backend-forge]` 状态行。
- 检查进入日志。
- `--require-complete` 时检查完成日志。

### route_golden_tests.py

输入：

```text
route_golden_tests.py
```

职责：读取 `tests/route_golden_cases.json`，回归常见路由。

### validate_release.sh

职责：发布验收入口，串联版本、项目检测、路由、session/gate 和输出协议。
