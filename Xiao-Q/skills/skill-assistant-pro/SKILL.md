---
name: skill-assistant
description: >-
  skill-assistant 是 Agent Skill 全生命周期管理助手——发现、推荐、安装、创建、质检、
  诊断优化一站式完成。当用户提到任何 skill 技能市场（skills.sh / SkillHub /
  ClawHub / SkillsMP / GitHub skill 仓库），想要找 / 搜索 / 安装 / 创建 / 更新一个
  skill，问"有没有 skill 能做 xxx"，想要诊断 / 优化 / 审查 / 体检 / 评分 / 改进
  一个已有 skill，想跑静态 / 动态 / 混合 / 盲评测试，想优化 skill description
  提升触发率，或想扫描所有已安装 skill 出优化优先级排行榜时，必须使用本 skill。
  英文触发词同样适用：find / search / install / create / update / diagnose /
  optimize / inspect / audit / score / evaluate skill。
  不要用于：通用包管理（npm / pip / brew）、IDE 插件/扩展的搜索与安装。
compatibility: Requires Python 3.8+, optional Node.js for HTML reports. No mandatory network access for core flows.
allowed-tools: Bash(python3:*) Bash(node:*) Bash(curl:*) Bash(gh:*) Bash(git:*) Read Write Glob Grep WebFetch
metadata:
  version: "2.1.0"
  last-updated: "2026-05-09"
  category: meta-skill
tags: [skill, lifecycle, search, install, create, quality, diagnose, security, eval, meta-skill]
---

# Skill 助手

搜索 · 推荐 · 安装 · 创建 · 质检 · 诊断 — Agent Skill 全生命周期一站式管理。

```
┌─────────┐     ┌──────────────┐     ┌──────────────────────┐
│ 用户意图 │ ──→ │ ⛔ 前置检查   │ ──→ │ 意图路由（6 模块）    │
└─────────┘     │ 首次使用引导  │     │ 搜索/推荐/安装/创建    │
                └──────────────┘     │ 质检/诊断             │
                                     └──────────────────────┘
       ┌─ config/sources.yaml (偏好 + 凭证)
       ├─ references/ (按需加载，含 best practices 全量参考)
       └─ scripts/ (CPU 密集 + workspace/manifest 原子写)
```

### 典型交互

> **用户**：帮我找一个生成 PPT 的 skill
> → 前置检查 → 4 级关键词 → 多渠道宽窄并行搜索 → 跨源去重 + 推荐指数 → 编号菜单 → 三引擎安全扫描 → 完成

> **用户**：审查这个 skill 是否符合 best practices
> → 路由到质检（[6.5] best_practices_only）→ 30 项 checklist 自动过 → 输出 ✅/❌ + 必修项 Top 3

> **用户**：推荐适合我的 skill
> → 扫描已安装 + 项目特征 → 用户画像 → 能力缺口 → 个性化推荐 2-5 条

### 不在范围内

- 非 Agent Skill 的通用包管理（npm / pip / brew 等）
- IDE 插件/扩展的搜索与安装
- 已安装 Skill 的代码级修改（诊断模块只交付建议和重构后的文件，不自动覆盖原文件）

---

## ⛔ 前置检查（任何操作前必须执行，不可跳过）

读取本 Skill 后，在执行任何用户意图之前，**严格按以下顺序**完成前置检查。**跳过任何步骤 = 流程错误**。

> ⚠️ 跳过前置检查是最常见的执行错误。直接搜索/安装将因缺少 API Token、未选择搜索源等问题导致失败，浪费用户时间。

### 步骤 0：配置自愈 / 迁移检测（每日一次）

扫描并清理废弃 / 需迁移的配置，让从旧版本升级的用户环境自动收敛到当前规范。**按日期节流**，避免每次使用都重复扫描。

**0.1 是否需要本次检测**（读 `config/sources.yaml` 的 `preferences.maintenance.last_check_date`）：

检测**固定每日一次**，无频率/开关选项。按 `last_check_date` 判断：
- 为空 `""` / 字段缺失 / `maintenance` 块缺失 → 视为从未检测，**强制执行**（块或字段缺失时顺带补全 `maintenance: { last_check_date: ... }`）
- 不是今天 → 执行
- 已是今天 → **跳过**，直接进入步骤 1

**0.2 执行检测清单**（命中即用 Read→StrReplace 精准删除并写回，保持 YAML 缩进合法；幂等——无残留则跳过该条）：

| # | 检测项 | 命中位置 | 处理 |
|---|--------|---------|------|
| 1 | **Knot 渠道残留**（已废弃，不支持第三方下载） | `sources.yaml`：`platforms` 下 `name: knot` 整条目 / `preferences.dedup_strategy.prefer_channels` 里的 `knot` / `meta_schema` 中 knot 相关枚举与注释（`source.skillId`、`source.type`/`channel`/`installedVia` 的 `knot`/`knot-cli`） / `custom_sources` 中指向 `knot.woa.com` 的源；`.credentials.yaml`（若存在）：顶层 `knot:` 段（含 `api_token`） | 全部删除，保留其他平台配置 |
| 2 | **废弃的检测开关 / 频率及自更新字段** | `sources.yaml`：`preferences.maintenance` 下的 `check_frequency` / `enabled`（含遗留 `never` 值）——本块只保留 `last_check_date`；`preferences.self_update` 整块（自更新机制已下线） | 全部删除 |

> **扩展点**：未来新增「废弃字段下线」「配置项改名迁移」等自愈需求时，**在本表追加一行**即可，节流与执行逻辑复用本步骤，无需改动其他流程。

**0.3 收尾**：本次有实际清理 → 用**一行**告知用户（如「已清理废弃的 Knot 渠道配置」）；无论是否有清理，只要执行了检测就把 `preferences.maintenance.last_check_date` 更新为今天（ISO `YYYY-MM-DD`）。**严禁**因检测/清理失败而阻断用户原始意图——这是尽力而为的自愈，失败则静默跳过并继续步骤 1。

### 步骤 1：首次使用拦截

**立即**读取 `config/sources.yaml` 的 `preferences.setup_completed` 字段：

- `false` 或不存在 → **停止。不执行任何后续操作。** 转入 [modules/setup.md](modules/setup.md) 完成 4 步引导，完成后回到步骤 2
- `true` → 继续步骤 2

### 步骤 2：意图路由

根据用户输入分流到对应模块，**严禁跳模块混合执行**。

| 用户意图 | 路由模块 | 参考文件 |
|---------|---------|---------|
| "搜一个 xxx skill" / "find skill for xxx" | **搜索** | [modules/search.md](modules/search.md) |
| "推荐适合我的 skill" / "有什么好用的" | **推荐** | [modules/recommend.md](modules/recommend.md) |
| "安装 xxx" / "帮我装这个 skill" | **安装** | [modules/install.md](modules/install.md) |
| "创建 / 写一个 skill" / "create skill" | **创建** | [modules/create.md](modules/create.md) |
| "审查 SKILL.md 是否符合 best practices" / "best practices 体检" | **质检**（`[6.5] best_practices_only`） | [modules/inspect.md](modules/inspect.md) + [references/skill-md-checklist.md](references/skill-md-checklist.md) |
| "检查这个 skill 质量" / "skill 体检" | **质检** | [modules/inspect.md](modules/inspect.md) |
| "动态评测 / 实测验证 / 跑测试看效果" | **质检**（`eval_mode=dynamic`） | [modules/inspect.md](modules/inspect.md) |
| "混合评测 / 静态加动态 / 正式评审" | **质检**（`eval_mode=hybrid`） | [modules/inspect.md](modules/inspect.md) |
| "扫描所有 skill / 全量体检 / 优化优先级" | **质检**（`mode=batch_baseline`） | [modules/inspect.md](modules/inspect.md) |
| "诊断 / 优化 / 重构这个 skill" / "迭代到收敛" / "帮我改进这个 skill" / "这个 skill 有问题" | **诊断**（⚠️ 必须先执行策略确认，见下方「诊断/优化前置策略确认」） | [modules/diagnose.md](modules/diagnose.md) |
| "优化 description / 提升触发率 / 跑加速器 / trigger eval" | **诊断**（Step 4.6 description 量化加速器） | [modules/diagnose.md](modules/diagnose.md) + [references/description-optimizer.md](references/description-optimizer.md) |
| "生成成果卡片 / 出张图 / skill 优化战报" | **质检/诊断** 报告后菜单触发 | [references/result-card.md](references/result-card.md) |
| "推荐一个 xxx skill" | **搜索**（以 xxx 为关键词） | [modules/search.md](modules/search.md) |
| "热门 skill" / "最受欢迎的 skill" | **搜索**（Leaderboard 优先） | [modules/search.md](modules/search.md) |
| "更新 skill" / "检查 skill 新版本" | **安装**（更新流程） | [modules/install.md](modules/install.md) |
| "相似 skill" / "类似 xxx 的 skill" | **搜索**（相似搜索模式） | [modules/search.md](modules/search.md) |
| "收藏 / star 这个 skill" | **推荐**（收藏操作） | [modules/recommend.md](modules/recommend.md) |
| "重新配置搜索偏好" / "reconfigure" | **引导** | [modules/setup.md](modules/setup.md) |
| 搜索无结果时 | 自动降级到**推荐** + 引导**创建** | [modules/recommend.md](modules/recommend.md) |
| 安装前未扫描时 | 自动插入**安装**模块的安全扫描 | [modules/install.md](modules/install.md) |

**诊断/优化前置策略确认**（⚠️ 强制，不可跳过）：
用户意图命中「诊断 / 优化 / 重构 / 改进 / 帮我看看这个 skill / 这个 skill 有什么问题」等任何优化类意图时，若用户**未在原始输入中明确指定策略**（如未说"直接修复"/"走棘轮"/"static"/"dynamic"/"hybrid"），**第一步必须**向用户展示策略选择：

```
您希望如何优化这个 Skill？

  [1] 直接修复已知问题（快速，适合明确问题清单）
  [2] 棘轮迭代流程（评测 → 诊断 → 修复 → 重新评测，适合全面提升）
      └ 评测模式：[2a] 静态  [2b] 动态  [2c] 混合  [2d] 盲评混合

请选择后继续。
```

收到用户明确选择后，再路由到对应模块执行。**"帮我优化"、"帮我看看"等模糊表达绝不视为已指定策略。**

**模糊意图兜底**：用户说「帮我看看这个 skill」/「这个 skill 怎么样」/「有没有 skill 可以做 xxx」等模糊表达时：
- 含 skill 文件路径/名称 → 路由到**质检**，先展示策略选择菜单
- 含功能描述无路径 → 路由到**搜索**（以功能描述为关键词）
- 完全模糊无上下文 → 询问用户：「您是想搜索一个 skill，还是检查/优化某个已有的 skill？」

**复合意图处理**：用户同时提到搜索+安装（"帮我找一个 xxx skill 并装上"），按顺序执行搜索 → 用户确认 → 安装。

**提案式交互**：每次搜索/推荐结果后，必须附带编号式下一步菜单（安装/详情/收藏/重搜）。

**关键参数契约速查**（详细定义见各 modules/*.md）：

| 模块 | 必填参数 | 可选参数 | 前置条件 |
|---|---|---|---|
| 搜索 | `query`(用户意图字符串) | `strategy`(speed/balanced/thorough，默认 balanced) | 无 |
| 安装 | `skill_id`(平台 ID 或仓库路径) | `force`(bool，默认 false) | 安全扫描通过 |
| 质检 | `target`(SKILL.md 路径) | `eval_mode`(static/dynamic/hybrid/blind_hybrid) | **建产物前先调 `resolve_workspace.py` 解析 workspace 路径** |
| 诊断 | `target`(SKILL.md 路径) | `eval_mode`, `max_iterations`(默认 3) | D10.1 ≥ 30（dynamic/hybrid 时）/ **建 workspace 前必走 W.0** |
| Description 加速器 | `target` | `provider`(claude/codebuddy/…) | D10.2 ≥ 30（需 trigger-queries.json）|
| 创建 | `intent`(用户意图) | `path_mode`(template/eval_driven，默认 template) | **必读 [references/anthropic-best-practices.md](references/anthropic-best-practices.md)** |

**Workspace 路径解析**（W.0 强制规则）：建任何评测产物前必读 [references/workspace-layout.md](references/workspace-layout.md) + 调 `python3 scripts/resolve_workspace.py --skill <skill_path>`，**不得手拼路径**（manifest_io 写入时会拒绝非 `skill-assistant-workspace/` 下的路径）。

---

## 核心原则

### 安全第一

- 所有来源不明的 Skill 安装前必须经过三引擎安全扫描（脚本硬扫描 + skills.sh 三方审计 + AI 软判断）
- **渠道信任等级 → 审查深度映射**：

| 信任等级 | 渠道示例 | 扫描策略 |
|---|---|---|
| **高信任** | Anthropic 官方 / skills.sh 官方认证 | 跳过脚本扫描，仅 AI 软判断 |
| **中信任** | skills.sh 社区 / SkillHub / SkillsMP | 完整三引擎扫描 |
| **低信任** | 用户自带 URL / 私有仓库 / 未知作者 | 三引擎 + 人工确认后才安装 |

- CRITICAL 风险（如发现 `curl | bash`、硬编码密钥、读 MEMORY.md）→ **立即中止，不询问用户**；HIGH 风险 → 展示详情由用户决定
- 检查访问 `MEMORY.md`、`USER.md`、`SOUL.md`、`IDENTITY.md` 等 AI Agent 敏感文件的行为
- Enterprise 级 7 类风险指标 + 8 步审查清单见 [references/anthropic-best-practices.md §Enterprise 级风险矩阵](references/anthropic-best-practices.md#enterprise-级风险矩阵--安全审查清单)

### 渠道可配置

源分为**平台型技能市场**和**GitHub 优质仓库**两大类，通过 [config/sources.yaml](config/sources.yaml) 统一配置。

| 场景 | 首选渠道 | 原因 |
|---|---|---|
| 社区热门 skill | skills.sh（安装量降序）| 安装量是最真实的质量信号 |
| 国内加速 / 中英双语 | SkillHub（CLI）| OpenClaw 同源，国内 CDN 加速 |
| 最新/实验性 skill | GitHub（gh search repos）| 上架慢的平台常滞后 1-2 版本 |
| 公司私有 skill | 自定义源（sources.yaml）| 平台不收录内部 skill |

### 质量驱动

- 搜索关键词遵循三原则：简单核心词优先 / 先粗后细 / 多意图拆分
- 跨平台质量归一化：将各平台不同维度的指标映射为统一推荐指数
- 跨源去重比较：同一 Skill 出现在多个源时合并展示，功能相似的给出 A/B/融合建议
- 搜索结果必须经过名称验证 + 质量评估才能推荐
- 质检模块提供 10 维度 70+ 检查项量化评分（A-F 五级）+ D10 实测可验证性附加维度
- 创建 / 质检 / 诊断三个模块共享 [references/anthropic-best-practices.md](references/anthropic-best-practices.md) 作为事实来源
- 诊断模块基于"Prompt 效能模型"进行三维分析（指令 40% / 约束 30% / 冗余 30%）

### 渐进式披露（按需加载架构）

- 本文件只做路由和原则声明
- 每个模块的详细工作流在对应的 `modules/*.md` 中
- **搜索模块核心流程**（`modules/search.md`），固定规则拆到 `references/` 按需加载
- **sources.yaml 选择性读取**：搜索时只读 `preferences:` + `settings:` 段（~70 行）
- 模板、规则库等低频参考在 `references/` 中
- 自动化逻辑在 `scripts/` 中

### 静默执行 + 幂等性

- 搜索/安装命令由 Agent 直接执行，不向用户展示原始命令；用编号式菜单和自然语言提案代替命令行展示
- 除 `maintenance.last_check_date` 写入与命中残留/遗留字段时的清理外，所有读操作幂等
- 搜索、质检、诊断报告阶段均为只读操作
- 安装操作通过 `--force` 参数控制覆盖行为，默认检测已安装不重复安装

### 常见错误（NEVER）— 核心 5 条

> 完整 50+ 条 NEVER 清单按模块分组在 [references/anti-patterns.md](references/anti-patterns.md)。本节只保留**最致命的 5 条**——违反这 5 条会直接破坏整个评测/搜索流程。

- **NEVER 跳过前置检查直接搜索/安装** — API Token 未加载会导致全部需认证渠道失败
- **NEVER 跳过 eval_mode 确认直接开始评审或优化** — inspect/diagnose 都适用："帮我看看"绝不视为已指定策略；用户未明确选 eval_mode 时必须展示菜单
- **NEVER 凭直觉拼 workspace 路径** — workspace 容器名固定 `skill-assistant-workspace/`，必须调 `scripts/resolve_workspace.py` 解析；27 个产物文件曾因手拼路径被迫迁移
- **NEVER 用列表/卡片/段落替代搜索的 Top N 表格** — markdown 表格是搜索透明度主线，违反触发 🚨 阻断级 `LAYOUT_NON_TABLE`
- **NEVER 评测完成后不落盘 detailed-report.html** — 任何 eval_mode 都必须通过 `scripts/generate-full-report.mjs` 落盘；Step 6 菜单只控制是否打开浏览器，不控制是否生成

> ⚠️ 进入对应模块（search / install / inspect / diagnose）时**必须读对应模块章节**的 [anti-patterns.md](references/anti-patterns.md)：包括搜索关键词与渠道并行、子 Agent 与 dry_run 评测（grading.json schema 等）、time-budget / 性能控制、盲评 Comparator 隔离等。

---

## 模块概览

### 引导模块 — `modules/setup.md`

首次使用引导（`setup_completed: false` 时强制触发）：搜索源选择（ClawHub/SkillHub 二选一，支持自定义仓库）→ 环境检查 + API Key 持久化 → 搜索策略（speed/balanced/thorough）→ 配置写入 sources.yaml。说"重新配置搜索偏好"可随时重进。

### 搜索模块 — `modules/search.md`

宽窄双路 × 多路并行（宽路 30 + 窄路 10）；多平台（skills.sh / SkillsMP / SkillHub）+ 优质仓库（gh）+ 全 GitHub；跨源去重 + 融合推荐；质量归一化（热度 40% + 权威 35% + 鲜度 25%）→ 统一推荐指数；搜索透明化（诊断头 + 11 条异常检测 + 5 个 refine 分支）。

### 推荐模块 — `modules/recommend.md`

多信号用户画像（已安装 Skill + 工作区特征 + README）→ 角色快查表 → 识别能力缺口 → 个性化推荐（业务价值优先，明确标注互补/增强/延伸关系）。含收藏/Star 管理系统。

### 安装模块 — `modules/install.md`

统一安装入口（`install_skill.sh` v2，禁止 `npx skills add`）+ 三引擎安全审查（13 项硬扫描 / skills.sh audit / AI 软判断）+ `_skill_meta.json` 版本追踪。支持单/批量更新。

### 创建模块 — `modules/create.md`

Skill 创建全流程：模板启动 / Eval 驱动两条路径 → frontmatter 完整字段引导（含 license / compatibility / allowed-tools）→ description 三件事原则（WHAT + WHEN + **Negative Boundaries**）→ 5 个核心 pattern（Checklist / Validation Loop / Plan-Validate-Execute / Conditional Loading / **Gotchas**）→ Eval 驱动开发 + Claude A/B 模式 → 与 inspect/diagnose 闭环迭代。详见 [references/anthropic-best-practices.md](references/anthropic-best-practices.md)。

### 质检模块 — `modules/inspect.md`

10 维度评分（D0-D9，对齐 OWASP LLM Top 10）+ D10 实测可验证性（附加）；eval_mode 五选一（preview / static / dynamic / hybrid / blind_hybrid）；`mode=batch_baseline` 全量扫描输出优先级排行榜；新增 `[6.5] best_practices_only` 入口跑 30 项 [skill-md-checklist.md](references/skill-md-checklist.md)；输出 A-F 评分 + 改进建议 + 子 Agent 双跑实证。

### 诊断模块 — `modules/diagnose.md`

三维诊断（指令 40% / 约束 30% / 冗余 30%）→ Step 0-6 交互流程 → Step 4 棘轮迭代（独立子 Agent 评分 / git revert 防退步 / 体积守门 ≤ 1.5×）。Step 4.6 description 加速器（子 Agent 模拟 / CLI 保真双路径，60/40 split + 5 轮选优）；三角色子 Agent（Grader / Comparator / Analyzer）；产物落独立 workspace（manifest.yaml 管理）。

---

## 降级规则

> 详细 9 条单源降级 + L1/L2/L3 三层兜底链全文在 [references/fallback-rules.md](references/fallback-rules.md)。本节只声明核心原则。

### 三层兜底链

| 层级 | 触发条件 | 处理策略 |
|---|---|---|
| **L1 单源失败** | 单个渠道/工具失败 | 按 [fallback-rules.md L1 表](references/fallback-rules.md#l1单源失败降级表9-条) 处理，输出标注「⚠️ 渠道/工具降级」 |
| **L2 模块失败** | 同模块超过半数渠道全部失败 | 自动跨模块降级：搜索 → 推荐 → 创建引导 |
| **L3 全部失败** | L2 后仍无结果 / 系统资源缺失 | **透明告知用户**：列出已尝试路径 + 失败原因 + 3 条人工兜底 |

### 降级透明度强制约束

任何 L1/L2/L3 降级**必须在输出中显式提示** ——不允许静默 fallback。降级路径写入诊断头的「环境/异常」段，让用户能定位偏差来源（违反触发 🚨 阻断级 `SILENT_FALLBACK`，重跑前必须修复）。

---

## 参考资料

### 🌟 Best Practices 三件套（创建/质检/诊断共同事实来源）

- **[anthropic-best-practices.md](references/anthropic-best-practices.md)** — Anthropic 官方 + 社区 5 篇精华汇总（三层加载 / Frontmatter 完整字段 / Description 三件事 / 5 个 pattern / Eval-driven dev / Enterprise 风险矩阵）
- **[skill-md-checklist.md](references/skill-md-checklist.md)** — 30 项自检清单（5 分钟可过完，对应 D0-D10）
- **[anti-patterns.md](references/anti-patterns.md)** — 50+ 条 NEVER 清单按模块分组（含搜索召回、子 Agent dry_run、报告生成等真实事故）

### 模块工作流参考

- 渠道详情：[references/channels.md](references/channels.md)
- 安全规则（三引擎）：[references/security-rules.md](references/security-rules.md)
- 搜索词模板：[references/search-templates.md](references/search-templates.md)
- 推荐策略模板：[references/recommend-templates.md](references/recommend-templates.md)
- 质检维度详情：[references/quality-dimensions.md](references/quality-dimensions.md)（含新增 D1.9 ~ D1.13 / D7.7 ~ D7.8）
- 诊断校准参考：[references/diagnosis-calibration.md](references/diagnosis-calibration.md)
- 创建改造清单：[references/create-best-practices.md](references/create-best-practices.md)
- 评分归一化映射表：[references/scoring-rules.md](references/scoring-rules.md)
- 渠道搜索命令模板：[references/channel-search-commands.md](references/channel-search-commands.md)
- 搜索输出模板：[references/output-templates.md](references/output-templates.md)
- 搜索透明度规范：[references/search-transparency.md](references/search-transparency.md)
- 搜索 Refine 规则：[references/refine-search.md](references/refine-search.md)
- 降级规则全集：[references/fallback-rules.md](references/fallback-rules.md)
- 成果卡片生成：[references/result-card.md](references/result-card.md)

### 评测产物 / 报告模板

- 单轮摘要报告（**diagnose Step 4.1.6.5 自动生成 iter-summary.html 时加载**）：[references/iteration-report.md](references/iteration-report.md)
- 完整详细报告（**diagnose Step 6 生成 detailed-report.html 时加载**）：[references/full-report.md](references/full-report.md)
- 卡片模板：[templates/result-card.html](templates/result-card.html)
- 卡片渲染脚本：[scripts/render-card.mjs](scripts/render-card.mjs)
- Description 量化加速器（融合 skill-creator）：[references/description-optimizer.md](references/description-optimizer.md)
- 自动 Judgement 生成器（**diagnose Step 0 / inspect D.0 自动生成测试集时加载**）：[references/auto-judgement-generator.md](references/auto-judgement-generator.md)
- test-prompts 设计与确认共用模块（**inspect D.0.1 / diagnose Step 0.1 必加载**）：[references/test-prompts-design.md](references/test-prompts-design.md)
- 时间预算控制（**inspect D.0.3 / diagnose Step 4.0 必加载**）：[references/time-budget.md](references/time-budget.md)
- 子 Agent 调用协议（**inspect D.1 / diagnose 4.1.4 / agents/* 共同遵循**）：[references/sub-agent-protocol.md](references/sub-agent-protocol.md)
- manifest 原子读写 helper（**强约束**）：[scripts/manifest_io.py](scripts/manifest_io.py)
- 金标数据集（**batch_baseline 扫描 / detector 回归时加载**）：`tests/golden-dataset/`（位于 workspace 根，不在 skill 目录内）
- Detector 回归基线脚本：`tests/run_golden_baseline.py`（位于 workspace 根）

### 配置与外部

- 渠道配置：[config/sources.yaml](config/sources.yaml)
- 浏览所有 skills：https://skills.sh
