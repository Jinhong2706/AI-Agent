# 创建模块

引导用户从零创建高质量 Agent Skill —— 集成 Anthropic best practices + skill-creator 的"draft → test → review → improve"实操循环。

> 本模块**不直接写 Skill**，而是组织"创建 + 自检 + 实测 + 迭代"的完整工作流。最终 SKILL.md 由用户（或主 Agent 在用户授权下）执行写入。
>
> **入门**：[anthropic-best-practices.md](../references/anthropic-best-practices.md) 是创建 Skill 的事实来源，强烈建议先读完该文档第 1-7 节。

---

## 创建 Skill 的两种路径

| 路径 | 适用场景 | 流程 |
|---|---|---|
| **A. 模板启动**（推荐）| 已知大致需求、想快速产出 | clone template → 填字段 → 跑 eval → 迭代 |
| **B. Eval 驱动**（严谨）| 高价值 skill、需要可证明有效 | 先写 eval baseline → 写最小 skill → 跑实测 → 持续迭代 |

> 两条路径都遵循 **"draft → test → review → improve"** 的核心循环。区别只是 path A 跳过了 eval baseline 测量，靠 reviewer 主观判断。

---

## 核心原则（覆盖 anthropic best practices 精华）

### 三层加载预算

| 层 | 加载时机 | Token 预算 |
|---|---|---|
| Metadata（`name` + `description`）| 始终在 context | ~100 tokens / Skill |
| SKILL.md body | Skill 触发时 | < 5K tokens（≤ 500 行硬上限，≤ 300 理想） |
| references/ + scripts/ + assets/ | 按需加载 | 实际无限 |

**85% 的初始 context 开销可通过此分层消除**——所以"description 写好 + body 精简"是创建 skill 的两个最高 ROI 动作。

### 自由度三档（按任务脆弱度匹配）

| 自由度 | 适用 | 指令形式 |
|---|---|---|
| **高** | 多种方法均可 / 启发式驱动 | 文本 + 原则（如 code review）|
| **中** | 有最佳实践 / 配置影响行为 | 伪代码 / 带参数脚本（如 generate report）|
| **低** | 操作脆弱 / 必须按序 | 确定性脚本，参数极少（如 DB migration）|

详见 [anthropic-best-practices.md §自由度三档校准](../references/anthropic-best-practices.md#自由度三档校准)。

---

## 创建工作流

### Step 0：捕获意图（Capture Intent）

> 来自 skill-creator 的关键洞察：当前对话本身常常已经包含了用户想 capture 的工作流。先扫一遍上下文再问问题，能省 50% 的来回。

提问 4 个核心问题，**简短直接，不堆术语**：

1. **这个 Skill 让 Agent 做什么？** （核心功能）
2. **什么时候应该触发？** （用户会怎么说、用什么文件、提到哪些关键词）
3. **预期输出格式是什么？** （结构化 JSON / Markdown 报告 / 文件 / 自由文本）
4. **要不要测试用例？** —— 输出可客观验证（文件转换、数据抽取、代码生成、固定步骤）→ **强烈建议**；输出主观（写作风格、视觉设计）→ 可跳

> 用户回答"我也不太清楚"时，先用 **路径 A 快速产出 v1 草稿**，让用户基于草稿修正 —— 比抽象提问效率高 10×。

### Step 1：确定 Skill 类型与自由度

| 类型 | 特征 | 核心价值 | 自由度 | 示例 |
|---|---|---|---|---|
| **思维型 (Mindset)** | 改变思考方式 | Expert 知识注入 | 高 | frontend-design |
| **导航型 (Navigation)** | 路由到参考文档 | 渐进式披露 | 高 | claude-api（多语言路由） |
| **流程型 (Process)** | 多步骤工作流 | 步骤编排 + 决策树 | 中 | deploy-tool |
| **工具型 (Tool)** | 封装工具链 | 脚本 + 决策框架 | 低 | pptx, pdf-editor |
| **规范型 (Standard)** | 标准与约束 | 认知框架 | 高 | code-style, brand-guide |

**类型决定了 SKILL.md 的写作侧重**：流程型重 workflow，工具型重 scripts，思维型重 expert 知识注入，导航型重 references 拆分。

### Step 2：脚手架（Scaffold）

```
{skill-name}/
├── SKILL.md              # 必须，≤ 500 行硬上限（理想 ≤ 300）
├── references/            # 可选，按需加载的详细文档（每个 ≤ 200 行，> 100 行加 TOC）
├── scripts/               # 可选，确定性逻辑（CPU 擅长的事）
├── assets/                # 可选，输出模板（不加载到 context）
└── tests/                 # 强烈建议，eval 测试用例
    └── evals.json
```

**命名规则**（D1.11）：
- ✅ 优先动名词：`processing-pdfs`、`analyzing-spreadsheets`、`managing-databases`
- ✅ 可接受名词短语：`pdf-processing`
- ❌ 避免模糊词：`helper`、`utils`、`tools`
- ❌ 不能含保留词：`anthropic-*`、`claude-*`

### Step 3：写 SKILL.md（最关键）

#### 3.1 YAML Frontmatter 完整字段

```yaml
---
name: <kebab-case>                        # 必须，≤ 64 字符，与目录名一致
description: >-                           # 必须，≤ 1024 字符（硬上限）
  <WHAT 1-2 句>。当用户 <WHEN 触发场景 + 触发词> 时，必须使用本 skill。
  英文触发词同样适用：<English trigger words>。
  不要用于：<NEGATIVE BOUNDARIES 3-5 个易混场景>。
compatibility: <env requirements>          # 推荐：Requires Python 3.10+...
allowed-tools: <tool whitelist>            # 推荐（trust signal）
metadata:                                  # 推荐
  author: <author>
  version: "1.0.0"                        # SemVer
  last-updated: "YYYY-MM-DD"
  category: <category>
  tags: "<comma, separated>"
license: <SPDX>                           # 仅开源 / 公开发布场景需要；内部 / 项目级 skill 可省
---
```

> 每个推荐字段都是**信任信号**：reviewer 看到 `allowed-tools: Read Write` 而不是 `Bash(curl:*)` 就知道这是个安全 skill。
>
> ℹ️ **`license` 不是必须**：Anthropic spec 没强制要求，Vijay 文章把它列为 trust signal 是面向公开发布到 skill 市场的场景。公司内部 / 项目私有 skill 省略 license 不会扣分。

#### 3.2 description 五件事原则 ⭐

`description` 是路由引擎 —— Agent 只看它决定是否激活。**五件事缺一不可**：

| 件 | 内容 | 例子 |
|---|---|---|
| ① **WHAT** | 1-2 句具体功能 | `Converts Markdown resume to professionally formatted PDF...` |
| ② **WHEN（trigger words）**| 触发条件 + 5-10 个具体说法 | `Use when the user asks to create a resume...` |
| ③ **NEGATIVE BOUNDARIES** ⭐ | 反向边界，3-5 个易混场景 | `Do NOT use for: cover letters, interview prep, LinkedIn optimization.` |
| ④ **LANGUAGE MATCH** ⭐ | 主体语言匹配用户提问语言；多语言场景含双语兜底；技术术语保留英文 | 中文用户 → 中文 description + 英文 trigger 兜底；技术名（PDF/OOXML）保留英文 |
| ⑤ **TRIGGER WORDS 边界** ⭐ | 只列**主入口动作**（用户冷启动会单独说的话），不列**派生菜单动作**（已进入 skill 后才会触发的子动作如"收藏"、"导出"、"重搜"） | ✅ "找 / 装 / 创建 skill"；❌ "收藏 skill"（实际场景永远是先搜到才收藏） |

**为什么语言匹配关键**：LLM 跨语言语义理解虽强，但同语言匹配信号显著更强。中文用户 + 全英文 description 的实测召回降低 30-50%。

**为什么 trigger words 边界关键**：把 skill 内部所有功能都列进 trigger words 是常见过度堆砌——派生动作（用户已经在 skill 流程中才触发的子菜单）放进 description 等于让 router 听到无意义关键词，反而抢自家其他 skill 的触发，拉低整体路由准确率。判断方法：问自己"用户冷启动对话时会不会单独说这句话"。

**英文场景范例**（580 字符）：

```yaml
description: >-
  Converts a Markdown resume into a professionally formatted PDF with multiple
  style options and ATS optimization. Use this skill when the user asks to
  create a resume, format a resume, convert a resume to PDF, build a CV, or
  make a resume ATS-friendly. Triggers include: 'resume', 'CV', 'curriculum
  vitae', 'resume PDF', 'format my resume', 'ATS-friendly resume'.
  Do NOT use for: cover letters, job searching, interview preparation,
  LinkedIn profile optimization, or portfolio websites.
```

**中文场景范例**（中英混合 + 技术术语保留英文）：

```yaml
description: >-
  resume-forge 把 Markdown 简历转成专业格式的 PDF，支持多种样式和 ATS 优化。
  当用户想要创建 / 制作 / 排版 / 转 PDF 一份简历或 CV，想做 ATS 兼容简历，
  或要把现有简历重新排版时，必须使用本 skill。英文触发词同样适用：
  resume / CV / curriculum vitae / format resume / ATS-friendly resume。
  不要用于：求职信（cover letter）、找工作、面试准备、LinkedIn 资料优化、
  作品集网站。
```

#### 3.3 Body 写作原则（concise is key）

每段都要问 3 个问题：
- 这段 Claude 真的需要解释吗？
- 我能假设 Claude 知道这个吗？
- 这段是否值得它占用的 token？

**默认假设：Claude 已经很聪明**。只写它不知道的。

**结构推荐**（按章节顺序）：

```markdown
# Skill Name

[一句话核心价值]

## When to use
[已在 description 里说过的，body 不重复，body 只放 expert 决策]

## Workflow
[checklist 形式，关键步骤可勾选]

## Patterns / Examples
[3+ 具体输入输出例子]

## Gotchas ⭐
[Agent 自己摸不到的坑，每条：症状 + 原因 + 隐含修复]

## References
[列出所有 references/ 文件 + 加载触发条件]
```

#### 3.4 4 个核心模式（按需采用）

| 模式 | 用法 | 何时用 |
|---|---|---|
| **Checklist Workflow** | `- [ ] Step N: 描述（脚本路径）` | multi-step 任务，防 Agent 跳步 |
| **Validation Loop** | "do → validate → fix → retry until pass" | 关键操作易出错（如 OOXML 编辑） |
| **Plan-Validate-Execute** | parse → 写中间产物 → 校验产物 → 执行 | 批量 / 不可逆操作 |
| **Conditional File Loading** | "Read X.md when [condition]" | 多分支、按需深入 |

详细模式与示例见 [anthropic-best-practices.md §核心模式](../references/anthropic-best-practices.md#核心模式)。

#### 3.5 Gotchas 段（最高 ROI 内容）⭐

Vijay Kumar 称为 "the highest-value content in the skill"。每条遵循：**症状 + 原因 + 隐含修复**。

```markdown
## Gotchas
- **WeasyPrint font rendering**: Uses system fonts. If template specifies a
  font not installed, silently falls back to default serif (so explicitly
  install required fonts before generation).
- **Markdown parsing edge cases**: Parser expects `##` for sections. Using
  `**bold**` as a section header will be missed entirely (use proper heading
  levels, not bold-as-heading).
```

这些是 Agent 自己摸索会踩的坑，提前注入省 10× 试错成本。

### Step 4：拆分到 references/

body 超 200 行（理想门槛）/ 超 500 行（硬上限）时按以下规则拆：

| 内容类型 | 放在 | 理由 |
|---------|------|------|
| 核心流程、触发条件 | SKILL.md | 每次触发都需要 |
| 详细规则、参数表、示例集 | references/ | 按需加载 |
| 确定性逻辑（正则、计算） | scripts/ | 不消耗 Token |
| 输出模板（HTML/JSON）| assets/ | 仅生成输出时读取 |

**两个硬约束**（违反即失分）：
- **D7.7 引用深度 = 1**：references/ 文件只从 SKILL.md 直接链接，不嵌套引用其他 ref
- **D7.8 长 ref 加 TOC**：> 100 行的 reference 文件首部加 `## Contents`

### Step 5：写测试用例（强烈建议）

```json
// tests/evals.json
{
  "skill_name": "<your-skill>",
  "evals": [
    {
      "id": 1,
      "prompt": "代表性场景 1（happy path）",
      "expected_behavior": ["客观可验证的产出特征 1", "..."],
      "files": []
    },
    {
      "id": 2,
      "prompt": "代表性场景 2（complex / edge case）",
      "expected_behavior": ["..."],
      "files": []
    },
    {
      "id": 3,
      "prompt": "代表性场景 3（negative boundary，不该触发的）",
      "expected_behavior": ["不触发本 skill / 给出兜底建议"],
      "files": []
    }
  ]
}
```

> 至少 3 条 eval：1 happy + 1 complex + 1 negative boundary。

### Step 6：跑 inspect 自检 + dynamic 实测

#### 6.1 静态自检（30s-2min）

```
路由到 modules/inspect.md → eval_mode=static
→ 自动跑 D0-D10 维度评分（含新增的 D1.9 ~ D1.13、D7.7 ~ D7.8）
→ 输出 A-F 总评 + 每项扣分点 + 改进建议
```

通过线：D0/D1/D7 ≥ 70，整体 ≥ 75（B 级及以上可交付）。

#### 6.2 动态实测（5-15min）

```
路由到 modules/inspect.md → eval_mode=hybrid
→ 子 Agent 双跑（baseline 不带 skill / with_skill 带 skill）
→ Grader 评分
→ 看 D10.1 是否 ≥ 30（实测有提升）
```

> 静态高分但动态分低 = "结构整齐但实际没用"型 skill —— 必须重写。

### Step 7：迭代闭环（draft → test → review → improve）

这是 skill-creator 的核心循环：

```
       ┌─────────────────────────────────────────┐
       ▼                                         │
   Draft v1 ──→ inspect 静态自检 ──→ 修复 D1/D7  │
       │                                         │
       ▼                                         │
   inspect dynamic 实测 ──→ 看 baseline vs with_skill 差距
       │                                         │
       ▼                                         │
   Reviewer 评估 outputs ──→ 找 gap ─────────────┘
       │
       ▼
   D10.1 ≥ 50 + Reviewer 满意 → 交付
```

**进入 diagnose 棘轮的时机**：
- 静态分 ≥ 70 但 D10.1 < 50（实测没用）→ 进 diagnose 全面诊断
- 静态分 + D10.1 都 ≥ 70 但 description 触发率低 → 进 diagnose Step 4.6 description 加速器

---

## 自检清单（交付前必跑）

直接跑 [skill-md-checklist.md](../references/skill-md-checklist.md) 30 项自检 ——通过 ≥ 25 项达 baseline。

或精简为 12 项 quick audit（见 [anthropic-best-practices.md §快速 Audit 自检流程](../references/anthropic-best-practices.md#快速-audit-自检流程)）。

---

## Eval 驱动开发（高价值 Skill 推荐）

**先写 eval，再写 Skill**——确保解决真实问题而非想象问题。

工作流：

1. **Identify gaps**：让 Claude **不带 skill** 跑代表性任务，记录失败点
2. **Create evaluations**：基于失败点写 3 条测试场景
3. **Establish baseline**：跑无 skill 版本，记录 baseline 分数
4. **Write minimal skill**：只写恰好通过 eval 的内容
5. **Iterate**：跑 eval → 对比 baseline → 改 skill → 再跑

**Claude A + Claude B 模式**（来自 anthropic 官方）：
- **Claude A**（创作者）：与你对话、写 SKILL.md、根据反馈改进
- **Claude B**（测试者）：加载 SKILL.md 跑真实任务、暴露问题
- 主 Agent 充当 A，spawn 子 Agent 充当 B

---

## 常见问题与反模式

| 反模式 | 问题 | 修复 |
|---|---|---|
| description 写成"I can help you with X" | 第一人称破坏 router 召回 | 改第三人称 "Processes X..." |
| description 没 negative boundaries | 易被泛关键词误触发 | 加 "Do NOT use for: ..." / "不要用于：..." |
| **中文用户场景写全英文 description** ⭐ | 同语言匹配信号更强，全英文召回 ↓ 30-50% | 主体用中文，trigger 词中英双语，技术术语保留英文 |
| **把派生菜单动作列进 trigger words** ⭐ | "收藏 / 导出 / 重搜"等用户冷启动不会单独说的动作占用路由信号，抢其他 skill 触发 | 只列主入口动作；派生动作放路由表/编号菜单 |
| body 一上来 800+ 行 | 超 token 预算、加载慢 | 拆到 references/ |
| references/ 嵌套引用 | Agent 部分读取丢信息 | 全部上提到 SKILL.md 直链 |
| 命名是 helper / utils | 不可发现、不可触发 | 改动名词 + 领域词 |
| 没有 Gotchas 段 | Agent 反复踩同样的坑 | 加 3-5 条经验沉淀 |
| 时效性硬编码 | 过期后误导 | 用 `<details>` 折叠到 "Old patterns" |
| ALL CAPS NEVER 堆砌 | 像生气的家长，效果差 | 解释 WHY，必要才用强约束 |
| 因为"trust signal"硬给内部 skill 加 license | 增加维护负担没收益 | 内部 / 项目级 skill 省略 license 不扣分 |

详见 [anti-patterns.md](../references/anti-patterns.md)。

---

## 与其他模块的关系

| 我想... | 用什么 |
|---|---|
| 从零创建一个 Skill | **本模块**（Step 0-7） |
| 检查我已经写好的 Skill 是否符合 best practices | **modules/inspect.md** + [skill-md-checklist.md](../references/skill-md-checklist.md) |
| 改造一个已有的 Skill 的某些 D 维度扣分项 | [create-best-practices.md](../references/create-best-practices.md) 改造清单 |
| 全面诊断 + 棘轮迭代提升 | **modules/diagnose.md** |
| 优化 description 触发率 | **modules/diagnose.md** Step 4.6 |
