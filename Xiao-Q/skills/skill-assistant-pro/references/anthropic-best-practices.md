# Anthropic Skill 编写官方最佳实践（精华版）

> 来源：5 份权威参考资料的综合提炼，作为 `create / inspect / diagnose` 三个模块共同的事实来源。
>
> 1. [Claude Skills Overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
> 2. [Claude Skills Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
> 3. [Claude Skills Enterprise](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/enterprise)
> 4. [Deep Dive SKILL.md (Vijay Kumar, Mar 2026)](https://abvijaykumar.medium.com/getting-deep-agents-to-work-with-skill-md-part-2-2-a65707eb5131)
> 5. [microsoft/azure-skills](https://github.com/microsoft/azure-skills)

---

## 目录

1. [三层加载架构](#三层加载架构)
2. [YAML Frontmatter 完整字段表](#yaml-frontmatter-完整字段表)
3. [Description 三件事原则](#description-三件事原则)
4. [Body 写作原则（Concise is key）](#body-写作原则concise-is-key)
5. [自由度三档校准](#自由度三档校准)
6. [Progressive Disclosure 三种模式](#progressive-disclosure-三种模式)
7. [核心模式（Workflows / Validation Loop / Plan-Validate-Execute / Gotchas）](#核心模式)
8. [Anti-patterns 速查](#anti-patterns-速查)
9. [Eval-Driven Development](#eval-driven-development)
10. [Enterprise 级风险矩阵 + 安全审查清单](#enterprise-级风险矩阵--安全审查清单)
11. [Recall Limits（多 Skill 共存）](#recall-limits多-skill-共存)
12. [快速 Audit 自检流程](#快速-audit-自检流程)

---

## 三层加载架构

| Level | 加载时机 | Token 成本 | 内容 |
|---|---|---|---|
| **Level 1: Metadata** | 始终加载（启动时） | ~100 tokens / Skill | YAML 的 `name` + `description` |
| **Level 2: Instructions** | Skill 触发时 | < 5K tokens | SKILL.md body 全文 |
| **Level 3: Resources** | 按需加载 | 实际无限 | references/, scripts/（执行不进上下文）, assets/ |

**关键含义**：
- **description 是唯一的"路由信号"**——Agent 只看它决定是否激活 Skill
- 多 skill 场景下 description 占用的"全局元数据上下文"按 ~100 tokens × N 增长
- 大 reference 文件不读就不消耗 token，bundle 不要怕"太大"，怕"误读"

---

## YAML Frontmatter 完整字段表

```yaml
---
name: resume-forge                    # 必须（≤64 字符，仅小写字母/数字/连字符）
description: >-                       # 必须（≤1024 字符，非空，不含 XML）
  Convert a Markdown resume into a professionally formatted PDF...
compatibility: Requires Python 3.10+ and weasyprint. No network access needed.
metadata:                             # 自由格式（spec 未定义内容）
  author: <author>
  version: "1.0.0"                    # 推荐（SemVer）
  last-updated: "2026-03-17"
  category: document-generation
  tags: "resume, pdf, career"
allowed-tools: Bash(python3:*) Bash(pip:*) Read Write   # 推荐（experimental，trust signal）
license: Apache-2.0                   # 仅开源场景需要，内部/项目级 skill 可省
---
```

| 字段 | 必须？ | 上限/格式 | 作用 |
|---|---|---|---|
| `name` | ✅ | ≤ 64 字符；仅 `[a-z0-9-]`；不含 `anthropic`/`claude` | 标识符；必须与目录名一致 |
| `description` | ✅ | ≤ 1024 字符；非空；不含 XML 标签 | **路由引擎**（详见下节） |
| `compatibility` | 推荐 | 自由文本 | 声明依赖（Python 版本、网络访问需求等） |
| `metadata` | 推荐 | YAML map | 版本、作者、分类、tags（spec 未规范） |
| `allowed-tools` | 推荐 | 工具白名单字符串 | **安全审计 trust signal**——`Bash(curl:*)` 出现在文档处理 skill 中 = 红旗 |
| `license` | 仅开源 | SPDX 标识符 | 公开发布到 skill 市场时需要；公司内部 / 项目私有 skill 可省略 |

> ⚠️ **`name` 不能含 `anthropic` 或 `claude`** —— 是官方保留词，命中会被拒。
>
> ⚠️ **`license` 不是必须项**——Anthropic 官方 spec 没有强制要求，Vijay 文章把它列为"trust signal"是面向公开发布的 skill。如果你的 skill 只在公司内或项目内使用，省略 license 不会扣分。

### 顶层字段 vs metadata 嵌套字段（常被搞混）

> 官方 spec **只把 `name` + `description` 列为顶层必填字段**。`metadata:` 是 spec 明确规定的"自由格式 key-value map"，所有"非功能性元数据"应该归在这里——而不是平铺到顶层。

| 字段位置 | 推荐放什么 | 不要放什么 |
|---|---|---|
| **顶层** | `name`（必须）、`description`（必须）、`compatibility`（声明依赖，被 runtime 读取）、`allowed-tools`（被安全审计读取）、`license`（公开发布场景）、`tags`（部分工具读取） | `version`、`author`、`last-updated`、`category`——这些应进 metadata |
| **`metadata:` 嵌套** | `author` / `version`（SemVer）/ `last-updated` / `category` / `tags`（如顶层未放） | 不要重复放已经在顶层的字段 |

✅ Good：
```yaml
name: my-skill
description: ...
compatibility: ...
allowed-tools: ...
metadata:
  author: lintonliu
  version: "2.1.0"
  last-updated: "2026-05-09"
  category: meta-skill
```

❌ Bad（version/author 平铺顶层污染）：
```yaml
name: my-skill
version: 2.1.0          # ← 应进 metadata
author: lintonliu       # ← 应进 metadata
description: ...
```

**为什么有差别**：顶层字段中部分会被工具读取（`compatibility` 给 runtime / `allowed-tools` 给安全审计 / `license` 给 SPDX 工具），而 `version`/`author` 只是给人看的元数据——平铺会让 frontmatter 看起来字段密度高，但其实没有工具消费它们。归到 metadata 下结构更清晰。

---

## Description 三件事原则

> Vijay Kumar 文章原文：description 必须做三件事，缺一不可。

### ① State what it does（做什么）

第三人称 / 祈使语调，1-2 句话说清核心功能。

✅ "Processes Excel files and generates reports"
❌ "I can help you with Excel files"
❌ "You can use this to process Excel files"

### ② List trigger words（列触发词）

包含用户可能用的具体说法（工具名、动作词、领域词、文件类型）。

✅ "Use when working with PDF files or when the user mentions PDFs, forms, or document extraction."

### ③ Draw negative boundaries（划反向边界）⭐

明确"何时**不**该用"——这是被多数人忽略但最关键的一项。

✅ "Do NOT use for: cover letters, job searching, interview preparation, LinkedIn profile optimization."

**为什么关键**：没有 negative boundaries 时，"准备面试" 这种含 career 关键词的请求会误触发 resume skill。

### 完整范例

```yaml
description: >-
  Convert a Markdown resume into a professionally formatted PDF with multiple
  style options and ATS optimization. Use this skill when the user asks to
  create a resume, format a resume, convert a resume to PDF, build a CV,
  generate a professional resume, make a resume ATS-friendly, or restyle an
  existing resume. Triggers include: 'resume', 'CV', 'curriculum vitae',
  'resume PDF', 'format my resume', 'ATS-friendly resume', 'professional resume'.
  Do NOT use for: cover letters, job searching, interview preparation,
  LinkedIn profile optimization, or portfolio websites.
```

字符数：~580 / 1024。三件事齐全。

### ④ Language Match（语言匹配，跨官方文档之外的实战经验）⭐

> 官方文档默认场景是英文用户，但实战中**用户用什么语言提问，description 主体就用什么语言**——LLM 跨语言语义理解能力虽强，但**同语言匹配的路由信号显著更强**（实测中文用户 + 全英文 description 召回降低 30-50%）。

**正确策略**：

| 内容类型 | 用什么语言 | 例子 |
|---|---|---|
| WHAT 主句 | 用户主流语言 | "skill-assistant 是 Agent Skill 全生命周期管理助手" |
| WHEN trigger words | **同时含**用户主流语言 + 英文 | 中文「找 / 搜 / 安装 skill」+ 英文 `find / search / install skill` |
| 平台名 / 技术术语 / 文件类型 | **保留英文原文**（这些是事实性符号） | `skills.sh`、`SkillHub`、`PDF`、`OOXML`、`static / dynamic eval` |
| Negative boundaries | 用户主流语言 | "不要用于：通用包管理（npm / pip / brew）..." |

**反例**（中文用户 + 全英文 description）：
```yaml
description: Use when the user mentions any skill platform, wants to find / search /
  install / create a skill...
```
→ 中文 query "帮我找个 PPT skill" 时，路由 LLM 看不到中文 trigger 词，召回降低。

**正例**（中文为主 + 英文兜底 + 英文术语保留）：
```yaml
description: >-
  skill-assistant 是 Agent Skill 全生命周期管理助手...
  当用户提到任何 skill 技能市场（skills.sh / SkillHub），想要找 / 搜索 /
  安装 / 创建一个 skill，问"有没有 skill 能做 xxx"... 时，必须使用本 skill。
  英文触发词同样适用：find / search / install / create skill。
```

### Trigger Words 的边界：主入口 vs 派生菜单（实战洞察）⭐

> 官方文档没明说，但实战中**最常见的过度堆砌**——把 skill 内部所有功能都列进 trigger words，反而拉低路由准确率。

**核心区分**：

| 类型 | 定义 | 示例（以 skill-assistant 为例）| 是否进 description |
|---|---|---|---|
| **主入口动作** | 用户**主动发起整个 skill** 的高频说法 | "找一个 skill"、"安装 skill"、"创建 skill"、"诊断 skill" | ✅ **必须列** |
| **派生菜单动作** | 用户**已经在 skill 流程中**才会触发的子动作 | "收藏这个 skill"、"star 这个 skill"、"展开诊断详情"、"导出报告" | ❌ **不要列** |

**为什么派生动作不该进 trigger words**：

1. **路由层级混淆**：description 决定"router 是否激活整个 skill"，派生动作是"激活后才执行的子菜单"——它们是不同层级的决策
2. **router 信号污染**：用户单独说"收藏一个 skill"几乎不会发生（实际场景永远是"先搜到 → 再收藏"），把它列进去等于让 router 听到无意义的关键词
3. **抢自家其他 skill 的触发**：如果你有多个 skill 都含"收藏"动作（比如 bookmark-skill），它们会互相抢触发

**判断方法**：
- 问自己："**用户冷启动**对话时，会不会**单独说**这句话？"
- ✅ 会单独说："帮我找一个 PPT skill" → 是主入口
- ❌ 不会单独说："收藏这个 skill"（一定是先搜到才会说）→ 是派生菜单

**正确的两层设计**：

```
description（路由层）
└─ trigger words 只列主入口动作

SKILL.md 路由表 / 模块菜单（功能层）
└─ 派生菜单动作（收藏 / star / 详情 / 重搜 / 导出报告 ...）
   通过编号菜单提供，不进 description
```

**反例**：

❌ 把所有动作都堆进 description：
```yaml
description: ... 想要找 / 搜索 / 安装 / 创建 / 收藏 / star / 详情 / 重搜 /
  分享 / 导出 / 评分 一个 skill...
```

✅ 只列主入口，派生动作进路由表/菜单：
```yaml
description: ... 想要找 / 搜索 / 安装 / 创建 / 更新一个 skill...

# SKILL.md 路由表里再列：
| "收藏 / star 这个 skill" | 推荐模块（收藏操作）|
| "重新搜索" / "看更多结果" | 搜索模块 refine 流程 |
```

### 描述质量评分（D1 维度细化）

| 检查项 | 通过标准 |
|---|---|
| **长度** | ≤ 1024 字符（硬上限）、≥ 80 字符（太短无信号） |
| **第三人称** | 不含 "I can…"、"You can…"、"Help you to…" |
| **WHAT** | 1-2 句具体功能描述 |
| **WHEN（trigger words）** | "Use when..." 子句 + 具体触发词列表 |
| **NEGATIVE BOUNDARIES** | 显式 "Do NOT use for..." 子句 |
| **关键词不堆砌** | 关键词嵌入语境，而非裸列 20 个 tag |
| **语言匹配** ⭐ | description 主体语言匹配用户主流提问语言；技术术语保留英文；多语言 trigger words 兜底 |

---

## Body 写作原则（Concise is key）

### 默认假设：Claude 已经很聪明

> "Only add context Claude doesn't already have. Challenge each piece of information"

每段都要问三个问题：
- 这段 Claude 真的需要解释吗？
- 我能假设 Claude 知道这个吗？
- 这段是否值得它占用的 token？

✅ 简洁版（~50 tokens）：
```markdown
## Extract PDF text
Use pdfplumber for text extraction:
\`\`\`python
import pdfplumber
with pdfplumber.open("file.pdf") as pdf:
    text = pdf.pages[0].extract_text()
\`\`\`
```

❌ 冗长版（~150 tokens）：
```markdown
## Extract PDF text
PDF (Portable Document Format) files are a common file format that contains
text, images, and other content. To extract text from a PDF, you'll need to
use a library. There are many libraries available...
```

### Token 预算

| 部分 | 预算 |
|---|---|
| SKILL.md body | < 5000 tokens（≤ 500 行硬上限，≤ 300 行理想，≤ 200 行优秀） |
| 单个 reference 文件 | 若 > 100 行必须加 TOC |
| frontmatter | 100-200 tokens |

---

## 自由度三档校准

> "Match the level of specificity to the task's fragility and variability."

| 自由度 | 适用场景 | 指令形式 | 例 |
|---|---|---|---|
| **高** | 多种方法均可 / 依赖上下文判断 / 启发式驱动 | 文本指令 + 原则 | Code review 流程：列原则，不规定具体改法 |
| **中** | 有最佳实践 / 允许部分变化 / 配置影响行为 | 伪代码 / 带参数脚本 | Generate report：给模板让 LLM 填字段 |
| **低** | 操作脆弱 / 一致性关键 / 必须按序执行 | 确定性脚本，参数极少 | DB migration：`python migrate.py --verify --backup` 一字不改 |

**判断比喻**：
- **悬崖之间的窄桥**（DB migration、生产部署）→ 低自由 + 精确指令
- **开阔原野**（写代码、做设计）→ 高自由 + 给方向

---

## Progressive Disclosure 三种模式

### 模式 1：高层指南 + 引用

```markdown
# PDF Processing
## Quick start
[最常用的 5 行代码]

## Advanced features
- **Form filling**: See [FORMS.md](FORMS.md)
- **API reference**: See [REFERENCE.md](REFERENCE.md)
```

适用：单领域，按"基础 → 进阶 → 参考"分层。

### 模式 2：按领域组织

```text
bigquery-skill/
├── SKILL.md (overview + 路由)
└── reference/
    ├── finance.md (revenue, billing)
    ├── sales.md (pipeline)
    ├── product.md (api usage)
    └── marketing.md (campaigns)
```

适用：多个独立子领域，user 一次只问一个 → Claude 只读对应文件。

### 模式 3：条件详情

```markdown
# DOCX Processing
## Creating documents
Use docx-js. See [DOCX-JS.md](DOCX-JS.md).

## Editing documents
For simple edits, modify XML directly.
**For tracked changes**: See [REDLINING.md](REDLINING.md)
**For OOXML details**: See [OOXML.md](OOXML.md)
```

适用：基础场景在 body，特殊场景按需展开。

### ⛔ 引用深度必须 = 1

| ✅ Good | ❌ Bad |
|---|---|
| SKILL.md → ref.md（一层） | SKILL.md → ref.md → detail.md（两层）|
| 所有 ref 直接从 SKILL.md 链接 | ref 之间互相跳转 |

**原因**：Claude 遇到嵌套引用时可能用 `head -100` 部分读取，造成信息丢失。

### 长 reference 必须有 TOC

```markdown
# API Reference
## Contents
- Authentication and setup
- Core methods (CRUD)
- Advanced (batch, webhooks)
- Error handling
- Code examples
## Authentication...
```

> 100 行的 ref 文件不加 TOC，Claude 可能只读前 100 行错过关键章节。

---

## 核心模式

### Pattern 1: Checklist Workflow

```markdown
## Workflow
Progress:
- [ ] Step 1: Obtain Markdown resume
- [ ] Step 2: Parse → JSON (`scripts/parse_resume.py`)
- [ ] Step 3: Validate (`scripts/validate_resume.py`)
- [ ] Step 4: Fix issues (loop until clean)
- [ ] Step 5: Generate PDF (`scripts/generate_pdf.py`)
- [ ] Step 6: Final review
```

让 Agent 抄到对话里勾选进度，不易跳步。

### Pattern 2: Validation Loop

```markdown
### Step 4: Fix and Re-validate
If validation reports issues:
1. Read specific error messages — they explain what's wrong and how to fix
2. Edit `resume.md` to address issues
3. Re-run Step 2 (parse) and Step 3 (validate)
4. **Only proceed to Step 5 when validation passes with zero errors**
```

"Do work → validate → fix → repeat"。错误信息要 self-explanatory，让 Agent 自纠正。

### Pattern 3: Plan-Validate-Execute

```
parse → validate plan → execute → verify
        ↑ 卡这里防止 garbage-in-garbage-out
```

中间产物（`parsed.json`、`fields.json`）用 script 校验，错了就 revise plan，确认无错才执行不可逆操作。

适用：批量操作、destructive changes、复杂校验、高风险操作。

### Pattern 4: Conditional File Loading

```markdown
For ATS-specific optimization, read [references/ats-optimization.md] before generating
— it contains keyword placement strategies and formatting rules that affect
how ATS parsers score the resume.

For industry-specific styling, read [references/industry-styles.md]
only if the user specifies a target industry.
```

明确 trigger condition + 明确 file path，Agent 才会按需读。

### Pattern 5: Gotchas Section ⭐

> Vijay 称为"the highest-value content in the skill"

```markdown
## Gotchas
- **WeasyPrint font rendering**: WeasyPrint uses system fonts. If template
  specifies a font not installed, it silently falls back to default serif.
- **Page overflow**: Long resumes may push content to second page with awkward
  breaks mid-section.
- **Markdown parsing edge cases**: Parser expects `##` for sections and `###`
  for sub-entries. Using `**bold**` as a section header will be missed.
```

每条：**症状 + 原因 + 隐含修复**。这些是 Agent 自己摸索会踩的坑，提前注入省 10 倍试错成本。

---

## Anti-patterns 速查

| 反模式 | 问题 | 修复 |
|---|---|---|
| 过于冗长的背景说明 | Agent 已经知道 | 只写它不知道的 |
| 提供太多选项 | Agent 选择困难 | 给一个默认 + escape hatch |
| Windows 风格路径 | 跨平台兼容差 | 统一用正斜杠 |
| 嵌套引用（ref → ref）| 部分读取信息丢失 | 引用深度 = 1 |
| 模糊命名（helper/utils）| 难发现、难触发 | 动名词 + 领域词 |
| 时效性内容 | 过期后误导 | 用 `<details>` 折叠旧版 |
| Magic numbers / voodoo constants | 无法解释为什么 | 加注释说明依据 |
| Punt to Claude | 脚本失败时丢锅 | 显式 try/except + 默认值 |
| 假设包已安装 | 跨环境失败 | 显式 `pip install xxx` 指令 |
| ALL CAPS NEVER 堆砌 | 像生气的家长 | 解释原因 + 必要才用强约束 |
| ANSI / 特殊字符乱码 | 跨终端不显示 | 用 ASCII 或 markdown 语法 |

详细分模块的 NEVER 清单见 [anti-patterns.md](anti-patterns.md)。

---

## Eval-Driven Development

> "Build evaluations BEFORE writing extensive documentation."

### 工作流（先 eval 再 skill）

1. **Identify gaps**：Run Claude 在代表性任务上 **不带 skill** 跑，记录失败点
2. **Create evaluations**：基于失败点写 3 个测试场景
3. **Establish baseline**：测无 skill 的表现作基线
4. **Write minimal instructions**：只写恰好通过 eval 的内容
5. **Iterate**：跑 eval → 对比 baseline → 改 skill → 再跑

### Eval 结构（最小可用）

```json
{
  "skills": ["pdf-processing"],
  "query": "Extract all text from this PDF and save to output.txt",
  "files": ["test-files/document.pdf"],
  "expected_behavior": [
    "Successfully reads PDF using appropriate library",
    "Extracts text from all pages without missing any",
    "Saves to output.txt in clear, readable format"
  ]
}
```

### Claude A + Claude B 模式

| 角色 | 职责 |
|---|---|
| **Claude A**（创作者）| 与你对话、写 SKILL.md、根据反馈改进 |
| **Claude B**（测试者）| 加载 SKILL.md 跑真实任务、暴露问题 |

迭代：A 写 → B 测 → 观察 B 行为 → 反馈给 A → A 改 → 再测。

> Skill-creator 的 draft → test → review → improve 闭环就是这个模式的工程化实现。

### 观察 Claude 如何使用 Skill（重要！）

| 信号 | 含义 |
|---|---|
| 读文件顺序出乎意料 | 你的结构不如想象中直观 |
| 漏读关键 ref | 链接不够明显，需要更显眼 |
| 反复读同一段 | 该内容应该提到 SKILL.md 主体 |
| 从未读某 bundled file | 多余或信号太弱 |

---

## Enterprise 级风险矩阵 + 安全审查清单

### 风险指标矩阵（部署前必查）

| 风险指标 | 检查内容 | 严重度 |
|---|---|---|
| **Code execution** | `*.py`/`*.sh`/`*.js` 脚本 | 🔴 高（脚本以完整环境权限运行） |
| **Instruction manipulation** | "ignore safety rules"、"hide actions"、条件改变 Claude 行为 | 🔴 高（绕过安全控制） |
| **MCP server references** | `ServerName:tool_name` 引用 | 🔴 高（扩展超出 skill 自身的访问范围） |
| **Network access** | URL、API endpoint、`fetch`/`curl`/`requests` | 🔴 高（数据外泄向量） |
| **Hardcoded credentials** | API key / token / 密码 | 🔴 高（git 历史 + 上下文窗口暴露） |
| **File system scope** | 跨 skill 目录的路径、广泛 glob、`../` 路径穿越 | 🟡 中 |
| **Tool invocations** | bash、文件操作、tool 引用 | 🟡 中 |

### 8 步安全审查清单

1. **读完整 skill 目录**：SKILL.md + 所有 ref + scripts + assets
2. **沙箱验证脚本**：行为是否与 description 声明一致
3. **检查对抗指令**：是否含"ignore safety"、"hide actions"、"exfiltrate via response"
4. **检查网络调用**：搜 `http`/`requests.get`/`urllib`/`curl`/`fetch`
5. **检查硬编码凭证**：API key/token/password 应走环境变量
6. **列举工具与命令**：bash 命令、文件操作、tool 引用清单 → 评估组合风险
7. **确认重定向目的地**：外部 URL 指向预期域
8. **检查数据外泄模式**：读敏感数据后写/发/编码外传（含通过对话回复）

> 永远不要部署来自 untrusted source 的 skill 而未做完整 audit。

### 5 维评测维度（部署门槛）

| 维度 | 测什么 | 失败示例 |
|---|---|---|
| **Triggering accuracy** | 该激活时激活、不该激活时静默 | 提到 spreadsheet 就激活，连讨论数据也触发 |
| **Isolation behavior** | 单 skill 独立运行正常 | 引用了不在目录里的文件 |
| **Coexistence** | 加入此 skill 是否影响其他 skill | description 太宽，抢走其他 skill 的触发 |
| **Instruction following** | Claude 是否按 skill 指令执行 | 跳过 validation 步骤、用错库 |
| **Output quality** | 产出是否正确有用 | 生成的报告格式错误、缺数据 |

要求每个 skill 提交 3-5 条 eval（含 should-trigger / should-not-trigger / ambiguous edge case），并跨 Haiku/Sonnet/Opus 测试。

---

## Recall Limits（多 Skill 共存）

> 加载越多 skill，每个 skill 的 description 在系统 prompt 里争夺注意力，召回率下降。

**硬限制**：
- API 单请求最多 **8 个 skills**
- 太多 skill 的"全局元数据上下文"超过临界值，Claude 选择困难

**最佳实践**：
- **Start specific, consolidate later**：先建窄 skill（`formatting-sales-reports`、`querying-pipeline`、`updating-crm`）→ 跑 eval 收集模式 → 合并为宽 skill（`sales-operations`）
- **Role-based bundles**：按角色组（sales/eng/finance），每用户只激活相关 bundle
- 用 eval 监控召回，加 skill 时关注是否拉低整体准确率

---

## 快速 Audit 自检流程

> 任何已经写完的 skill 在交付前跑一遍这个 12 项 audit。详细 30 项 checklist 见 [skill-md-checklist.md](skill-md-checklist.md)。

### Tier 1：Frontmatter（6 项）

- [ ] `name` ≤ 64 字符 / kebab-case / 与目录名一致 / 不含 anthropic|claude
- [ ] `description` ≤ 1024 字符 ✅ 且 ≥ 80 字符 ✅
- [ ] description 是第三人称（不含 "I can…"、"You can…"）
- [ ] description 含 **WHAT + WHEN（trigger words）+ NEGATIVE BOUNDARIES + Language Match + Trigger Words 边界** 五件事
- [ ] trigger words 只含主入口动作，不含派生菜单动作（收藏 / 导出 / 重搜）
- [ ] 推荐字段：`compatibility` + `allowed-tools` 至少有 1 项（开源场景再加 `license`）

### Tier 2：Body 结构（4 项）

- [ ] body ≤ 500 行硬上限（≤ 300 行理想）
- [ ] 引用深度 = 1（SKILL.md → ref，不嵌套）
- [ ] > 100 行的 ref 文件含 TOC
- [ ] 术语全文一致（不混用 endpoint/URL/route）

### Tier 3：内容质量（3 项）

- [ ] 无时效性硬编码（日期、版本号 → 用 `<details>` 折叠或抽到"Old patterns"）
- [ ] 至少有 3 个具体 example（不是抽象描述）
- [ ] Workflow 含 checklist + validation loop（如有 multi-step 操作）

通过 12 项 = 达到 official best practices baseline，可以提交到企业 registry。
