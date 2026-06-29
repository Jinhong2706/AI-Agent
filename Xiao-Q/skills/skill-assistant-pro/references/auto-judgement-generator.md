# 自动 Judgement 生成器

读 SKILL.md → 推断执行路径（scopes）→ 自动生成细粒度 judgement，**作为 `test-prompts.json` 的半自动起点**。

> **设计来源**：融合自 [panlm/skills@generate-judgements](https://github.com/panlm/skills/tree/main/others/generate-judgements) 的 5 类 judgement 框架 + 11 种 question pattern + 否定 check 设计。**不直接搬其英文 SKILL.md**——上游目标是 mlflow-skills 的 `judge_definitions` YAML 配置，本文件适配 skill-assistant 的 `test-prompts.json` schema 与 D10.3 critique evals 评分维度，并增加"与三角色子 Agent（Grader / Comparator / Analyzer）对齐"的中文规则。

---

## 何时使用

- diagnose Step 0 用户选「自动模式」时
- inspect 发现 D10.1 输出质量可验证性低分（缺 test-prompts.json）时
- 用户主动说「自动生成测试集」「帮我写 evals」「不会写测试 prompt」时

---

## 工作流

```
Phase 1   收集与分析    → 读 SKILL.md / references / README，抽取功能模块、工作流步骤、规则、输出格式
Phase 2   推断 scopes   → 识别多个执行路径（默认所有 skill 至少有 `all` scope）
   ↓ 用户确认 scopes
Phase 2.5 场景维度规划  → 为每个功能模块规划 5 类场景（happy/complex/edge/negative/error）+ 优先级（P0/P1/P2）
Phase 3   分类生成      → 按"功能 × 场景 × 5 大类 judgement × 优先级"4 维矩阵生成 prompts + judgements
Phase 3.5 完整性 check  → 跑覆盖完整性 checklist；缺位置自动补 P0 必填条目
Phase 4   呈现给用户    → 4 维覆盖矩阵 + judgement 分组表格，支持增 / 删 / 改 / 重新生成
   ↓ 用户确认
Phase 5   写入 JSON     → 输出 test-prompts.json（含 scope + functional_module + priority 字段）+ 关联 trigger-queries.json
```

> **设计原则**：测试用例生成不是"想几条凑合"，而是基于 SKILL.md 功能分析推导出**尽可能完整**的覆盖矩阵。完整性的可量化标准见下方「完整性 checklist」段。

---

## Phase 1 — 收集与分析

### 输入

| 编号 | 输入 | 必填 | 说明 |
|:-:|---|:-:|---|
| 1 | 被测 Skill 目录路径 | ✅ | 必含 SKILL.md |
| 2 | 已有 test-prompts.json | 可选 | 提供时增量更新而非覆盖 |
| 3 | workspace 路径 | 自动 | 沿用 W.1 解析结果 |

### 读取顺序

| 优先级 | 文件 | 用途 |
|:-:|---|---|
| 1 | `SKILL.md` | 主要来源——工作流步骤、行为规则、输出格式 |
| 2 | `references/*` | 补充细节——模板、CLI 命令、查询模式 |
| 3 | `README.md` / `README_CN.md` | 边界与限制说明 |
| 4 | 已有 `test-prompts.json` | 防止重复生成、保留好的现有项 |

### 抽取要点（写入诊断笔记，不展示给用户）

| 要点 | 识别方式 | 后续用途 |
|---|---|---|
| **功能模块**| frontmatter `tags`、SKILL.md 的"模块概览"小节、`modules/*.md` 目录、章节标题中的并列功能词 | Phase 2.5 矩阵的"功能"维度 + Phase 4 覆盖率呈现 |
| **工作流步骤** | 编号列表（"1. ... 2. ..."）、流程图、表格列出的阶段 | Category B 工作流类 judgement |
| **行为规则** | "must" / "always" / "never" / "do not" / "必须" / "不得" / "严禁" | Category E 准则合规类 |
| **输出格式** | "the output must contain" / "格式如下" / 模板代码块 | Category C 输出质量类 |
| **条件分支** | "if X → A; else → B" / "当...时" | Phase 2 推断 scopes |
| **重要准则** | 常出现在文末"重要约束""注意事项""Important Guidelines" | Category E |

### 功能模块抽取规则

按以下优先级抽取**功能模块清单**（决定测试用例 prompt 数量的下限）：

| 优先级 | 信号 | 说明 |
|:-:|---|---|
| 1 | `modules/*.md` 文件名 | 每个 `<module>.md` 即一个独立功能模块（如 search / install / diagnose）|
| 2 | SKILL.md 「模块概览」小节的子标题 | 若没有 modules/ 目录，从 body 中的 `### 搜索模块` 这种结构抽 |
| 3 | frontmatter `tags` 列表 | 兜底——把 tags 中的动词性词（search / recommend / install）作为模块 |
| 4 | 章节标题中的并列动词 | 如"搜索 · 推荐 · 安装 · 创建 · 检查 · 诊断"——按分隔符切 |

**输出**：`functional_modules: [{name, description, source}]`（写入诊断笔记，不直接展示）

**最小数量约束**：
- 单一功能 skill（如纯"格式化 markdown"）：至少 1 个模块
- 多功能 skill（如 skill-assistant）：抽出来的模块数 ≥ 3，否则 Phase 1 视为失败，要求用户补充确认 modules 清单

---

## Phase 2 — 推断 Scopes

### 什么是 scope

一个 skill 内部不同的**执行路径**。每条路径产生**不同的输出**或**走不同的逻辑**，独立成一个 scope。

| 命名规则 | 说明 |
|---|---|
| 用小写 + 连字符 | `checklist` / `assessment` / `research` / `batch-baseline` |
| `all` 是保留字 | 表示"任何 scope 下都跑"——共同行为 |
| 每个 skill 至少有 `all` | 即使是单一执行路径的 skill 也有 `all` 表示通用判定 |

### 识别 scope 的三种线索

1. **条件分支**：SKILL.md 含"如果 X → 做 A；否则 → 做 B"
2. **可选步骤**："仅当 ... 时执行此步"
3. **输出形态**："checklist 模式" vs "assessment 模式" 这种二选一描述

### 与用户确认（必须 STOP）

```
我从 SKILL.md 识别到以下执行路径：

1. `all` — 通用行为（每条 prompt 都要校验）
   覆盖：skill 加载、frontmatter 读取、references 路由

2. `checklist` — 仅生成检查清单的路径
   触发条件：用户输入含「列出 / 检查清单 / 给我看看有没有漏」
   独有产物：checklist.md 文件，**不**生成评估报告

3. `assessment` — 实测评估路径
   触发条件：用户输入含「评估 / 跑一次 / 实测」
   独有产物：assessment-report.md，**不**生成 checklist

请确认：是否需要增 / 删 / 改某个 scope？
```

**等待用户确认后再进 Phase 2.5**。

---

## Phase 2.5 — 场景维度规划

> 解决"测试用例生成只想 happy path"的常见盲点。每个功能模块都要按 5 类场景规划，按优先级筛选成最终矩阵。

### 5 类场景定义

| 场景类型 | 默认优先级 | 含义 | 典型 prompt 模板 |
|---|:-:|---|---|
| **happy_path** | P0 | 用户最常说的那句话——核心路径 | "帮我做 X" / "搜索一个 Y skill" |
| **complex** | P0 | 多步骤 / 含分支 / 上下文依赖 | "帮我评测这 5 个 skill 排个序" |
| **edge** | P1 | 边界条件——空输入 / 极大输入 / 极少匹配 | 空字符串 / 全是 emoji / 极长文本 |
| **negative** | P1 | 反例触发——用户说了"似是而非"的话，期望 Skill **不**激活或拒答 | "帮我配置 npm 仓库"（应不被路由到 skill 搜索）|
| **error** | P2 | 异常处理——前置依赖缺失 / API 失败 / 权限不足 | "搜索 X skill"（API Token 未配置）|

### 优先级矩阵

每个 `(功能模块, 场景类型)` 组合按下表决定优先级：

| | happy_path | complex | edge | negative | error |
|---|:-:|:-:|:-:|:-:|:-:|
| **核心模块**（如 search 之于 skill-assistant）| P0 | P0 | P1 | P1 | P2 |
| **次要模块**（如 setup） | P0 | P1 | P2 | P2 | P2 |
| **附加模块**（如 result-card 渲染）| P1 | P2 | — | — | — |

> **核心 vs 次要 vs 附加**：基于 Phase 1 抽出的 `functional_modules` + 在 SKILL.md 中的章节深度判断（顶级模块 = 核心；二级子模块 = 次要；提供给其他 skill 引用的 = 附加）。

### 用户确认（必须 STOP）

```
我从 SKILL.md 识别到 N 个功能模块，按 5 类场景规划了下面的覆盖矩阵：

| 功能模块 | happy | complex | edge | negative | error | 小计（仅 P0/P1）|
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| search    | P0 ✓ | P0 ✓ | P1 ✓ | P1 ✓ | P2 △ | 4 |
| install   | P0 ✓ | P0 ✓ | P1 ✓ | P1 ✓ | P2 △ | 4 |
| inspect   | P0 ✓ | P0 ✓ | P1 ✓ | P1 △ | P2 △ | 3 |
| ...
| **总计**                                                      |  **N P0 + M P1**

✓ = 默认生成   △ = 默认跳过   — = 不适用

请确认：是否需要 (a) 增 / 删某个模块  (b) 升降某个场景的优先级  (c) 把 △ 改为 ✓ 强制生成
```

> 用户可逐格选择修改；最终矩阵决定 Phase 3 要生成多少 prompts（每格 1 条 prompt）。

---

## Phase 3 — 按 5 类生成 Judgement

**输入**：Phase 2.5 的覆盖矩阵（N 个 P0 + M 个 P1 单元格 = N+M 条 prompt）。

针对每个 `(功能模块, 场景, 优先级)` 三元组生成 1 条 prompt，并按下方 5 大类**逐类生成**细粒度 judgement 挂在该 prompt 下。**一条 judgement 只测一件事**。

**Prompt 与 judgement 数量约束**：

| 单元格优先级 | 必填 judgement 数 | 应至少覆盖的 category |
|:-:|:-:|---|
| P0（核心） | ≥ 4 | A 加载 + B 工作流 + C 输出质量 + E 准则合规 |
| P1（次要） | ≥ 3 | A 加载 + (B 工作流 或 C 输出质量) + E 准则合规 |
| P2（锦上） | ≥ 2 | A 加载 + 任一其他 |

### Category A — Skill 加载与触发（scope: `all`）

| 检查点 | question 写法 |
|---|---|
| Skill 是否被加载 | "检查 transcript 中能否看到 SKILL.md 被读取（路径含 `.cursor/skills/{skill-name}/SKILL.md` 或 `.claude/skills/...`）。能看到回答『是』" |
| references 是否按需加载 | "Skill 要求按需读 `references/X.md`。检查只在用户问到相关问题时才读，不全量预加载。回答『是』当只看到 1-2 次按需读取" |

### Category B — 工作流行为（scope: `all` 或具体 scope）

| 检查点 | question 写法 |
|---|---|
| 步骤顺序 | "Skill 要求步骤 1-N 按序执行。检查工具调用顺序：每个 CALL 在前一个完成后开始。**关键澄清**：单次调用 batch 多个 item 不算并行——只有两个独立 CALL 同时进行才标『否』。无法判断时给『是』（疑罪从无）" |
| 条件分支正确 | "用户输入命中 X 条件时，Skill 应走分支 A。检查输出是否符合分支 A 的形态" |
| 错误处理 | "Skill 规定 `--exec` 失败时应 retry 3 次。检查 transcript 中失败后是否能看到 retry 痕迹" |

### Category C — 输出质量（scope: `all` 或具体 scope）

| 检查点 | question 写法 |
|---|---|
| 必需 sections 都在 | "输出必须含 N 个章节：1) ... 2) ... 检查最终 markdown 是否包含全部 N 个章节标题。N-1 个也接受（宽松一档）" |
| 命名规则正确 | "输出文件名必须符合 `{prefix}-{date}.json`。检查 Write 工具调用使用的路径" |
| 必填元数据呈现 | "每条结果必须含 `source` 字段（举例：`tencent_cloud` / `iwiki`）。检查输出 JSON 中 source 字段不为空" |
| 数量在范围内 | "输出 items 数量应在 [MIN, MAX] 之间。计数 + 容忍边界各 5 条" |

### Category D — Scope 特有行为（每个非 `all` scope 一组）

| 检查点 | question 写法 |
|---|---|
| 该路径**应**有的产物 | "在 `assessment` scope 下，必须生成 assessment-report.md 文件。检查 Write 工具是否写过这个路径" |
| 该路径**不应**有的产物（否定 check）| "在 `checklist` scope 下，**不**应该生成 assessment-report.md。检查整个 transcript 没有写过该路径——回答『是』当未发现该文件被写过" |
| 该路径独有动作 | "在 `research` scope 下，应执行至少 3 次外部搜索。检查 search/web 工具调用次数 ≥ 3" |

### Category E — 准则合规（scope: `all`）

| 检查点 | question 写法 |
|---|---|
| 「必须」类规则 | 把 SKILL.md 里所有 "必须 / must / always" 句子转成判定 |
| 「不得」类规则（否定）| 把所有 "不得 / never / do not" 句子转为否定 check |
| 输出语言 | "Skill 要求中文输出。检查最终输出是否中文" |
| 边界处理 | "用户输入空字符串时，Skill 应返回友好错误而非崩溃。检查无 stack trace" |

---

## 11 种 question 写法模式（融合自 #9 patterns）

每条 question 必须包含 **what / where / criteria** 三要素。

### 1. 加载检查
> "检查 SKILL.md 是否被读取——transcript 中应能看到 Read 工具调用，路径含 `{skill-name}`。回答『是』当能看到证据。"

### 2. 顺序执行检查（区分并行 CALLS vs 批量请求）
> "检查 {tool} 调用按顺序执行——每个 CALL 在前一个完成后开始，**不是**两个 CALL 并行。**关键**：单 CALL 内 batch 多 item 不算并行。无法判断时回答『是』。"

### 3. 覆盖率/数量（带宽容度）
> "检查执行了约 N 次 {操作}，覆盖以下话题：1) ... 2) ... 至少 N-1 个话题被覆盖即可回答『是』。"

### 4. 必需 sections 检查
> "检查输出含全部 N 个必需章节：{section1} / {section2} / ... 看 transcript 中 Write 写入的内容。"

### 5. 格式 / pattern 检查
> "检查 IDs 符合 `{PATTERN}` 格式（例：{ex1}, {ex2}）。看 Write 写入的文件内容。"

### 6. 文件命名
> "输出文件名必须符合 `{NAMING_RULE}`。看 Write 工具的 path 参数。"

### 7. 数量范围（带宽容度）
> "items 总数应在 [{MIN}, {MAX}]，每组至少 {MIN_PER_GROUP}。**宽松**：相差 5 以内仍判『是』。"

### 8. 元数据呈现（引原文）
> "每个 {item} 必须含 {field}（如 {ex1} / {ex2}）。Skill 要求："{原话引用}"。看 Write 写入内容。"

### 9. 否定检查（NOT happen）
> "在 {scope} 下，Skill **不应** {forbidden_action}。检查 transcript 中**未出现** {forbidden_artifact}。回答『是』当确实未出现。"

### 10. CLI / 命令执行
> "检查 agent 执行了 {service} CLI 命令——预期含 {cmd1} / {cmd2}。至少看到 {MIN_DIFFERENT} 个不同命令即『是』。"

### 11. 条件 section 检查
> "输出含 `{section_name}` 章节（描述：{description}）。**允许为空**当 {empty_condition}。"

---

## 反模式（NEVER）

### ❌ 多检查塞一条

```yaml
# 错的
- name: workflow-correct
  question: 检查 5 个步骤都正确，输出有 6 个章节，命名符合规范
```

**修复**：拆成 3 条独立 judgement，每条只测一件事。

### ❌ 模糊成功标准

```yaml
# 错的
- name: docs-searched
  question: 检查 agent 是否合理地搜索了文档
```

**修复**：明确"哪些话题、最少几次、什么算合理"。

### ❌ 缺位置指引

```yaml
# 错的
- name: has-source-tags
  question: 检查 source tag 存在
```

**修复**：加"看 Write 工具写入的文件内容"或"看 transcript 中 X 之后"。

---

## Phase 3.5 — 完整性 checklist

> Phase 3 生成完后**必跑**这一步——量化检查"测试集是否真的覆盖到了 SKILL.md 的所有功能"。不通过项自动补 P0 必填条目，再回 Phase 3 微调。

### 完整性公式

```
功能覆盖率 = 已覆盖功能模块数 / 总功能模块数
场景覆盖率 = 已覆盖 (功能 × 场景) 单元格数 / 矩阵中所有 P0+P1 单元格数
Category 覆盖率（每条 prompt 单独算）= 该 prompt 命中的 category 数 / 应命中的 category 数
```

### Pass 标准（**全部满足**才能进 Phase 4）

| # | 检查项 | Pass 标准 | 不通过时的行为 |
|:-:|---|---|---|
| 1 | **功能覆盖率** | 100%（每个 functional_module 至少 1 条 P0 prompt） | 自动补 happy_path P0 prompt，标 `auto_added=true` |
| 2 | **场景覆盖率（P0）** | ≥ 95%（仅 P0 单元格）| 列出未覆盖 P0 单元格，要求 Phase 3 重生成 |
| 3 | **场景覆盖率（P0+P1）** | ≥ 70% | 警告但不阻断；让用户在 Phase 4 决定要不要补 |
| 4 | **每条 P0 prompt 的 category 覆盖** | ≥ 4 个 category（A/B/C/E 必含） | 自动补缺失 category 的 judgement |
| 5 | **negative_judgements 比例** | 至少有 1 条 P0 prompt 含 negative_judgements（防"全 happy 路径"偏置）| 警告 + 推荐补 1 条 negative scope |
| 6 | **判别力**（与 D10.3 对齐）| 每条 prompt 至少 1 条 skill 专属 judgement（baseline 不可能命中） | Phase 3 重写：把通用 judgement 改写为 skill 专属 |
| 7 | **场景类型分布** | happy / complex 各 ≥ 1，edge / negative / error 至少 2 类有覆盖 | 列出缺失场景类型 |

### 输出格式（写到诊断笔记）

```yaml
completeness_report:
  total_modules: 6           # search / install / inspect / diagnose / create / setup
  covered_modules: 6
  total_p0_cells: 12
  covered_p0_cells: 12
  total_p0_p1_cells: 18
  covered_p0_p1_cells: 16
  scene_distribution:
    happy_path: 6
    complex: 5
    edge: 3
    negative: 2
    error: 0       # ⚠️ 0 条 error 场景——警告
  category_coverage_per_p0_prompt:
    - prompt_id: 1
      categories: [A, B, C, E]   # 缺 D（该 prompt scope=all 不需 D，OK）
      pass: true
    ...
  pass_overall: true
  warnings: ["缺 error 场景 prompt"]
```

### 与 D10.3 critique evals 的差异

| | Phase 3.5 完整性 checklist | D10.3 critique evals |
|---|---|---|
| 时机 | 测试集生成中（Phase 3 之后立即跑） | 动态评测后 Grader 反向质询 |
| 关注 | "覆盖率够不够"（结构维度） | "判别力够不够"（语义维度） |
| 是否阻断 | 阻断（必通过才进 Phase 4）| 仅评分扣分，不阻断 |

> 两者互补：完整性 checklist 保证"该测的都测到了"；critique evals 保证"测的方式不太宽松/太严苛"。

---

## Phase 4 — 呈现给用户

> Phase 4 输出**两块**：① 4 维覆盖矩阵概览 ② judgement 分组表格。

### Step 4.1 — 覆盖矩阵概览

```markdown
## 测试集覆盖矩阵（共 N 条 prompt，覆盖 M 个功能模块 × 5 类场景）

| 功能模块 | happy | complex | edge | negative | error | 命中 category（A/B/C/D/E） |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| search    | P0 ✓ | P0 ✓ | P1 ✓ | P1 ✓ | — | A B C D E |
| install   | P0 ✓ | P0 ✓ | P1 ✓ | — | — | A B C E |
| inspect   | P0 ✓ | P0 ✓ | — | P1 ✓ | — | A B C E |
| ...
| **覆盖率** | 100% | 100% | 50% | 50% | 0% | — |

### 完整性 checklist 结果
- ✅ 功能覆盖率：100%（6/6）
- ✅ P0 场景覆盖率：100%（12/12）
- ⚠️ P0+P1 场景覆盖率：89%（16/18）—— 缺 install/edge、create/edge
- ✅ 判别力：每条 prompt 含 ≥1 条 skill 专属 judgement
- ⚠️ 场景分布：error 场景 0 条 → 建议补 1 条
```

### Step 4.2 — judgement 分组表格

把生成结果按 scope 分组展示成表格：

```markdown
## 生成的 Judgements（共 N 条，跨 M 个 scope）

### Scope: `all`（共 7 条）

| # | name | category | 检查内容 |
|:-:|---|---|---|
| 1 | skill-invoked | A 加载 | SKILL.md 被读取 |
| 2 | sequential-tool-calls | B 工作流 | 工具调用顺序而非并行 |
| ... |

### Scope: `checklist`（共 3 条）

| # | name | category | 检查内容 |
|:-:|---|---|---|
| 1 | checklist-file-written | D 特有 | 写出 checklist.md |
| 2 | no-assessment-report | D 否定 | **不**生成 assessment-report.md |
| ... |

### Scope: `assessment`（共 5 条）

...

请确认：是否需要增 / 删 / 改任意 judgement？
```

**等待用户确认后再进 Phase 5**。

---

## Phase 5 — 写入 test-prompts.json

### Schema 升级

`skill-assistant` 历史 `test-prompts.json` schema：

```json
[
  {"id": 1, "scenario": "happy_path", "prompt": "...", "expected": "..."}
]
```

**schema 增强**（向后兼容旧版）：

```json
[
  {
    "id": 1,
    "scenario": "happy_path",
    "scope": "all",
    "functional_module": "search",
    "priority": "P0",
    "prompt": "用户会说的话",
    "expected": "期望输出的简短描述（自由文本，给 Grader 看）",

    "judgements": [
      {
        "name": "skill-invoked",
        "category": "A_loading",
        "question": "检查 SKILL.md 是否被读取——transcript 中应看到 Read 工具调用 ..."
      },
      {
        "name": "checklist-file-written",
        "category": "D_scope_specific",
        "question": "..."
      }
    ],

    "negative_judgements": [
      {
        "name": "no-assessment-report",
        "question": "**不**应该生成 assessment-report.md ..."
      }
    ]
  }
]
```

### 字段语义

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | int | 用例编号 |
| `scenario` | string | `happy_path` / `complex` / `edge` / `negative` / `error` |
| `scope` | string | 执行路径分组，与 Phase 2 的 scope 一致 |
| `functional_module` | string | 来自 Phase 1 抽取的功能模块名（search / install / ...）|
| `priority` | enum | `P0` / `P1` / `P2`，由 Phase 2.5 矩阵给出 |
| `prompt` | string | 用户会说的话 |
| `expected` | string | 给 Grader 的自由文本期望（用于 rubric 评分）|
| `judgements[]` | array | 可机械验证的细粒度 yes/no 检查项 |
| `negative_judgements[]` | array | 否定 check（应**不**出现的事）|

### 向后兼容（多版本兼容矩阵）

| 字段 | 缺失时行为 |
|---|---|
| `scope` | 默认按 `all` 处理 |
| `judgements` | 退化为 Grader 仅按 `expected` 自由打分 |
| `functional_module` | 不参与覆盖矩阵渲染（标 `unassigned`），不阻断评测 |
| `priority` | 默认按 P1 处理 |
| `scenario=edge/error`（旧版只有 happy/complex/negative）| 旧 Grader 兼容这两个新值，按 `complex` 同等处理 |

旧 `test-prompts.json` **照样可用**——只是覆盖矩阵的"功能模块"列会显示为"unassigned"，建议运行一次 `inspect → 自动补全` 补齐新字段。

---

## 与 D10.3 critique evals 的对齐

`modules/inspect.md` D10.3 的 critique evals 维度负责**反向质询测试集本身**：

| critique 维度 | 自动 judgement 生成器如何配合 |
|---|---|
| **测试集是否太宽松（baseline 也能过）** | 生成 judgement 时尽量包含**只有 with-skill 才能命中**的细节（如"输出含 SKILL.md 中独有的术语"），避免"通用礼貌回复也能过"|
| **测试集是否太严苛（with-skill 也过不了）** | 生成时给关键计数加 ±5 的 leniency；模糊匹配（"约 N 次"）而非精确（"恰好 N 次"）|
| **测试集是否缺关键校验点** | 生成 5 大类 + 否定 check 全覆盖，比手写更不易漏维度 |

> **关键**：自动生成只是 D10.3 的**起点**——critique evals 仍会反向质询，质量低的 judgement 会被 critique 标"❌ 太宽松"或"❌ 缺位置指引"，进入 Phase 6 自我修正循环。

---

## Phase 6（可选）— Critique 反馈循环

Phase 5 写完 `test-prompts.json` 后，自动跑一次 critique evals（使用 `agents/grader.md` 的 critique 模式）：

```
对每条 judgement，Grader 反向质询：
  - "这条 question 给 baseline 跑也能过吗？" → 太宽松
  - "with-skill 跑也过不了吗？" → 太严苛
  - "缺位置指引（where to look）吗？" → 不可机械验证
```

输出 `critique-report.md`，标记需要修正的 judgement。用户审核后回到 Phase 3 微调。**最多 2 轮 critique**，避免过度雕琢。

---

## 与三角色子 Agent 的衔接

| 角色 | 在自动 judgement 生成中的作用 |
|---|---|
| Grader（`agents/grader.md`） | Phase 6 critique evals 的执行者；后续 inspect/diagnose 跑动态评测时按 judgement 逐条评分 |
| Comparator（`agents/comparator.md`） | blind_hybrid 形态下读 `judgements[]` 作为评判维度，盲评 baseline vs with_skill |
| Analyzer（`agents/analyzer.md`） | 看 Comparator 输出 + judgements 命中分布，归因"哪些 judgement 帮 with_skill 赢了" |

---

## 边界

- **不生成**性能 / 成本类 judgement——属于 inspect D9 自由度校准，不在动态评测范围
- **不生成**安全审计 judgement——D8 由 `skill_audit.py` + 金标基线处理，不放在 test-prompts.json
- **不生成**主观艺术性 judgement——如"输出风格优雅"——LLM 判断方差大，应转为可量化的代理指标（如"含 N 个示例"）

---

## NEVER 规则

- **NEVER 跳过 Phase 1 功能模块抽取直接生成 prompt** — 没有功能清单 = 没有覆盖矩阵的横轴 = 测试集只能凭直觉，必有盲区
- **NEVER 生成单一场景类型的测试集** — 5 类场景至少要覆盖 3 类（happy + complex 至少各 1 条，edge/negative/error 至少 1 类有覆盖）；只有 happy_path 的测试集等于"只测顺风路况"
- **NEVER 跳过 Phase 3.5 完整性 checklist 直接进 Phase 4** — 完整性公式不通过的测试集，棘轮决策可信度直接 -50%
- **NEVER 仅按 prompt 数量判断测试集质量** — 100 条 prompt 全是 happy_path 不如 5 条覆盖 5 类场景的；评估测试集质量看的是"覆盖矩阵 + Category 分布 + 判别力"三维度，不是单一计数
- **NEVER 把"测试用例"和"trigger queries"混淆** — `test-prompts.json` 测的是"触发后好不好（输出质量）"；`trigger-queries.json` 测的是"会不会被触发（路由）"。两者 schema 不同、生成策略不同，不能合并
- **NEVER 让用户跳过 Phase 2.5 矩阵确认直接进 Phase 3** — 矩阵决定整个测试集的覆盖范围，必须用户对齐功能清单 + 优先级 + 场景表后才生成 prompt
