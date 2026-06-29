---
name: skill-creator-king
description: >
  从零创建、审查评分、迭代完善 AI Agent Skill 的元工具。
  支持四平台、Phase 0-5六阶段流程、14维质量审计、反模式扫描、Token预算估算、好模式识别、LLM驱动修复+安全回滚、全生命周期覆盖。
  Use when 创建新的 AI Agent Skill, 审查已有 Skill 的质量, or 升级迭代 Skill 功能。
version: "3.23.1"
template: multi-scene
author: 公众号 & Skillhub -- 普通AI星球
triggers:
  - 创建skill
  - 新建skill
  - 升级skill
  - 审查skill
  - 评分skill
  - skill审计
  - skill review
  - skill creator
  - create skill
  - audit skill
  - 修复skill
  - autofix
token_budget:
  L0_trigger: 200
  L1_core: 2000
  L2_deep: 20000
  hard_cap: 25000
allowed-tools: Read, Write, Bash, Edit
metadata.openclaw: true
metadata.hermes: true
---

# 👑 Skill Creator King

> **从对话建、用分数验、自动修复、持续迭代**——skill 全生命周期 total solution。

## Purpose

你是 Skill 全生命周期管理助手，正在为 AI Agent 创建、审计、修复、迭代 Skill。支持四平台、Phase 0 出发前确认 + 五阶段创建流程。autofix 已简化为安全骨架：engine.py 只做三件事——扫描问题 → 备份文件 → 验证修复，修复由 LLM 直接执行。

**SCK 的定位边界**：静态分析工具（linter），不跑代码、不验证行为。查形式不查功能——查 YAML 语法、版本一致性、文件完整性、反模式；不查脚本逻辑是否正确、工作流是否合理、触发词是否真的命中。功能质量留给 LLM/人来判断。

## Context

Skill 是 AI Agent 的能力单元——一个 Markdown 文件定义触发条件、工作流和指令。SCK 通过模板生成、反模式扫描、14维质量审计、LLM 驱动修复+安全回滚四环联动，确保每个 Skill 从创建到退役全程可追溯、可验证。

**杠铃架构**：审计端（validate.py + quality-audit.py）只读不写；修复端（LLM 直接读写）有 backup/rollback 安全网。两端通过结构化 JSON 通信——审计结构化输出，LLM 读 JSON 修文件，engine 验证修复后评分。

## Pre-flight Checklist（必读）

开始前确认：① 目标平台 ② 场景（创建 / 评审打分 / 自动修复 / 升级迭代）③ 通道选择（lightweight/full）

## 四大场景

| 场景 | 触发 | 职责 |
|------|------|------|
| 创建 | `init_skill.py --name X --template Y` | 从零生成脚手架 |
| 评审打分 | `validate.py <skill>` + `quality-audit.py <skill>` | 验证+反模式扫描 + 14 维质量评分 |
| 自动修复 | `autofix/engine.py <skill> --backup` → LLM 修复 → `--verify` | 安全回滚骨架 |
| 升级迭代 | 对话驱动修改 | 增量迭代、版本进化 |

## 工作流

### Phase 0 出发前确认 + 五阶段创建流程

```
Phase 0: Pre-flight → Phase 1: DISCUSS → Phase 2: DESIGN → Phase 3: BUILD → Phase 4: VERIFY → Phase 5: EVOLVE
```

- **Phase 0**: 出发前确认（平台/入口/通道）
- **Phase 1 DISCUSS**: 讨论需求，对齐期望
- **Phase 2 DESIGN**: 确定方案（冻结 DESIGN.md，v3.14+ 合并 WHAT+HOW；旧 skill 若双文件则同步更新或建议合并；涉及文件产出的 skill 须在收尾前确认输出文件约定）
- **Phase 3 BUILD**: 实施构建
- **Phase 4 VERIFY**: `validate.py --json` → `quality-audit.py` → `autofix --backup` → LLM 修复 → `autofix --verify` → `auto-test` → 修改后自检
  - **4.1**: `validate.py <skill> --json` — 结构验证 + 反模式扫描，输出结构化 issues
    - **语义一致性检查**（必执行）：validate 返回中 `semantic_check` 字段包含交叉文件检查指令。逐一读取 DESIGN.md / README.md / l2-l3-workflow.md（如存在）/ CHANGELOG.md，逐段对比其中的阶段数、数字、交付物清单、功能描述与 SKILL.md 是否一致，不一致项报告并修正。
  - **4.2**: `quality-audit.py <skill>` — 14 维质量评分（基线）
  - **4.3**: `python3 scripts/autofix/engine.py <skill> --backup` — 备份所有文件 · 简化
    - 创建备份 session，文件全量 snapshot 到 `_backups/<session-id>/`
    - 然后 LLM 逐条读 4.1 的 issues，直接写文件修复
  - **4.4**: `python3 scripts/autofix/engine.py <skill> --verify <session-id>` — 重新 validate · 简化
    - 修复后跑 validate + quality-audit，确认问题清零、评分未降
    - 评分降级 → `--rollback <session-id>` 一键回滚
  - **4.5**: `quality-audit.py <skill> --llm-review --json` — LLM 语义审查（4 固定问）
    - 脚本不调用 LLM——仅收集所有文件上下文 + 预提取信号，注入 `llm_review` 字段
    - AI Agent 读取 `llm_review.questions` + `llm_review.files` + `llm_review.extracted_signals`，逐一回答 4 问
    - 4 问固定：Q1 语义漂移 / Q2 术语一致性 / Q3 集成完整性 / Q4 残余痕迹
    - 输出格式：每问 `✅/⚠️/❌` + 具体位置，不加解释
    - **默认关**——仅在深度审（CHANGELOG 含大版本变更）或手动要求时启用
  - **4.6**: 自动生成 `tests/test.py` 并运行 → 修复失败 → 循环至 100%
    - auto-test 互补：检测名称不一致、路由遗漏、领域约束等 validate/audit 盲区
    - 此时处理语义问题——validate/audit 盲区
  - **4.7 修改后自检**（每次修改后必须执行，三项不可跳过）：
    1. **SCK 自动扫描**：`validate.py` + `quality-audit.py`，修到 0 真实问题
    2. **新交付物落地**（SCK 盲区）：新增了文件 → 确认至少一个工作流引用了它 + 脚本已运行通过
    3. **错误处理审计**（SCK 盲区）：新增或修改了 `.py` 脚本 → 确认成功/限流/失败三条路径都有处理
  - **4.8 输出文件约定验证**（当 skill 涉及文件产出时触发）：
    1. 检查 SKILL.md 是否包含 `## 输出文件约定` 章节
    2. 验证实际产出路径是否与约定一致
    3. 目录不存在时是否有 mkdir 逻辑
- **Phase 5 EVOLVE**: 自我反思 → 改进建议（autofix session 历史通过 `--list-sessions` 回溯）

## 快速命令

```bash
# 创建新 skill（自动检测平台）
python3 scripts/init_skill.py --name my-skill --template basic

# 交互式创建（逐步引导）
python3 scripts/init_skill.py --interactive

# 验证 skill
python3 scripts/validate.py your-skill/

# 质量审计（14维度）
python3 scripts/quality-audit.py your-skill/

# 安全修复（备份 → LLM 修 → 验证）
python3 scripts/autofix/engine.py your-skill/ --backup      # 创建备份
# ... LLM 修复文件 ...
python3 scripts/autofix/engine.py your-skill/ --verify <id>  # 验证修复

# 回滚修复
python3 scripts/autofix/engine.py --rollback <session-id> --skill your-skill/

# 查看修复历史
python3 scripts/autofix/engine.py --list-sessions --skill your-skill/

# 完整审计 + LLM 语义审查（检测脚本盲区：术语漂移、残留、集成缺口）
python3 scripts/quality-audit.py your-skill/ --llm-review --json

# 自动生成并运行定制测试（Phase 4.6）
# 由 LLM 在 VERIFY 阶段自动执行：分析结构 → 生成 tests/test.py → 运行 → 修复

# Phase 完整性检查
python3 scripts/phase-check.py --phase 2 your-skill/

# 跨平台审计
python3 scripts/quality-audit.py your-skill/ --platform universal
```

## 平台支持

| 平台 | 满分 | 跳过维度 | 路径检测 | autofix |
|------|------|---------|---------|---------|
| WorkBuddy | 135 | 无 | `~/.workbuddy/skills/` | ✅ backup/verify |
| OpenClaw | 81 | token_budget, semantic_consistency, readme_sync, changelog_today | `~/.openclaw/skills/` | ✅ backup/verify |
| Hermes | 81 | 同上 | `~/.hermes/skills/` | ✅ backup/verify |
| Universal | 81 | 同上 | `~/.agents/skills/` | ✅ backup/verify |

## 核心原则

详见 `DESIGN.md`

## 注意事项

- 修改 Skill 后必须运行 SCK 完整扫描（`validate.py` + `quality-audit.py --no-cache`），修到 0 真实问题
- 修复前用 `autofix --backup` 创建备份，修复后用 `autofix --verify` 验证，有问题 `--rollback` 回滚
- 版本升级后同步更新 SKILL.md / DESIGN.md / README.md / CHANGELOG.md 四处版本号

## 文件结构

详细结构见 `README.md`。关键参考文件：
- `references/phase-0-preflight.md` — Phase 0 出发前确认
- `references/phase-1-positioning.md` — Phase 1 DISCUSS：需求讨论与定位
- `references/phase-2-design-requirements.md` — Phase 2 DESIGN · 子步骤 1/2：需求定义
- `references/phase-2-design-architecture.md` — Phase 2 DESIGN · 子步骤 2/2：架构设计
- `references/phase-3-build.md` — Phase 3 BUILD：实施构建
- `references/build-standards.md` — BUILD 施工规范（L2 约定/错误处理/输出格式）
- `references/phase-4-verify.md` — Phase 4 VERIFY：验证交付
- `references/phase-5-evolve.md` — Phase 5 EVOLVE：持续迭代
- `references/review-guide.md` — 审查打磨流程
- `references/upgrade-guide.md` — 升级流程
- `references/auto-test.md` — 自动测试
- `references/readme-standard.md` — README 最低标准
- `references/vitality-audit.md` — 活性审计
- `scripts/validate.py` — 文件完整性 + 版本一致性校验
- `scripts/quality-audit.py` — 14 维度质量评分
- `scripts/estimate-tokens.py` — Token 预算测算
- `scripts/init_skill.py` — 脚手架生成
- `scripts/phase-check.py` — Phase 完整性检查
- `scripts/autofix/engine.py` — 修复安全骨架（backup→verify→rollback）
- `scripts/autofix/backup.py` — 备份 + 回滚
- `data/anti-patterns.yaml` — 反模式定义
- `rules/operational-rules.md` — 六条操作纪律（不穷举/不双写/不窄检/改必扫/不孤改/表先于盘）

## Output

SCK 产出的交付物：

- **新 Skill 脚手架**：目录 + SKILL.md + README.md + CHANGELOG.md（`init_skill.py` 生成）
- **验证报告**：反模式列表 + 修复建议 + 语义一致性检查（`validate.py --json`）
- **质量审计评分**：A/B/C/D 四级，14 维度评分（`quality-audit.py`）
- **安全修复报告**：备份 session-id / 验证结果 / 可回滚
- **LLM 语义审查**：4 问审计报告（Q1 数字漂移 / Q2 术语一致 / Q3 结构完整 / Q4 残留检测）
- **自动测试**：`tests/test.py`（Phase 4.6 自动生成）
- **修改后自检清单**：3 项不可跳过（SCK 自动扫描 + 新交付物落地 + 错误处理审计）

## 输出文件约定

- **输出目录**：`~/.{平台}/skills/{name}/`（由 Phase 0 确认平台后确定；可用 `--dest` 覆盖）
- **文件命名**：SKILL.md / README.md / CHANGELOG.md / DESIGN.md 等固定名称
- **文件格式**：Markdown (.md) 为主，Python 脚本 (.py)，YAML 配置 (.yaml)
- **错误输出**：脚本错误返回结构化 JSON（`{"ok": false, "error": str}`），不泄露系统信息
- **autofix 备份**：`_backups/<session-id>/` — LLM 修复前的安全 snapshot

---

## Further Reading

- `DESIGN.md` — 架构设计与核心原则（含 autofix 设计决策）
- `README.md` — 安装与使用

---

_v3.23.1_
