---
name: game-publishing-research
displayName: Game Publishing Case Study
displayName_zh: 游戏发行案例研究
description: A methodology skill for researching game publishing / promotion / go-to-market / case study work. Provides a four-phase workflow (case pool → single-case analysis → cross-case synthesis → application layer), writing hard rules, HTML deliverable spec — explicitly does NOT preset any path taxonomy. Use when user mentions game publishing research, case study, console / mobile / PC publishing, KOL / platform resource analysis, or works in a game research project directory.
description_zh: 游戏发行 / 推广 / 出海 / 营销案例研究专用方法论。提供四阶段工作流（案例池 → 单案分析 → 综合洞察 → 应用层）、写作硬规则、HTML 交付规范，**不预设任何路径分类**——分类轴必须从本次案例数据归纳得出。适用场景：(1) 用户提到"游戏发行 / 推广 / 案例研究 / 复盘 / 综合洞察 / 出海策略 / 营销打法 / 路径分类"等；(2) 用户给出具体游戏名 + "怎么做发行 / 怎么推广 / 主机版本 / 出海 / 上架 / 营销"等；(3) 用户提到 F2P / 付费 3A / 主机厂商合作 / KOL / 平台资源 等领域词汇；(4) 用户在游戏研究项目目录下工作。
author: mandy
version: 1.0.0
license: MIT
tags:
  - game-publishing
  - research
  - methodology
  - case-study
  - go-to-market
  - 游戏发行
  - 案例研究
keywords:
  - 游戏发行
  - 案例研究
  - 综合洞察
  - 出海策略
  - 主机推广
  - F2P
  - 付费 3A
  - game publishing
  - publishing strategy
  - case study
  - go-to-market
---

# Game Publishing Case Study · Skill / 游戏发行案例研究 · Skill

> **English** | A methodology skill for game publishing case study work. Implements a four-phase workflow with strict writing rules and HTML deliverable spec, but **never presets path taxonomy** — every research must induce its own taxonomy from data.
>
> **中文** | 游戏发行案例研究方法论 skill。实现四阶段工作流 + 写作硬规则 + HTML 交付规范，**永不预设路径分类**——每次研究必须从数据归纳分类轴。

---

## 调用此 skill 后必须遵守的核心原则 / Core Principles

### ⚠️ Red Line 1: Do NOT preset path taxonomy / 红线 1：不预设路径分类

**EN**: This skill does NOT bundle any "path taxonomy" or "five paths / seven paths" preset answers.

**为什么**：游戏行业变化快——主机政策、平台战略、品类红海、营销渠道每年都变。把上一次研究归纳出的路径直接套到下一次研究上，会让分类轴绑架数据。

**正确做法 / Correct flow**：
1. 先按"立题清单"明确研究目标和边界。
2. 跑案例池和单案分析时，**不带预设结论**地观察。
3. 综合洞察阶段从数据里**归纳**分类轴，不是套用上一次的。
4. 第一版分类轴不一定对，敢于在第三轮研究时推翻重排（参考 `references/research-methodology-precedent.md` 里"分类轴迭代史"的真实案例）。

### ⚠️ Red Line 2: Every data point must have a citable source / 红线 2：所有案例数据必须有可点开的来源

每个具体数字、合作时间、销量数据、平台资源声明，**必须附带**可点开的来源链接。来源优先级 / Source priority:

1. 厂商官方 IR / 销售公告（Capcom IR、任天堂 IR、Activision Blog、第一方工作室销售公告）
2. 平台官方（PlayStation Blog、Xbox News、Nintendo 官网、Game Pass 官方公告等）
3. 权威数据源（SteamDB、SensorTower、Newzoo、CIRP、VGChartz）
4. 主流游戏媒体（Wikipedia 因脚注完整可作起点 / GamesIndustry.biz / Eurogamer / The Verge / IGN / 4Gamer / Famitsu 等）
5. 二级讨论（Reddit / 玩家社区）—— **只能作为线索，不能作为定论引用**

如果某个归因/动机只在二级讨论里出现而官方未确认，必须做"真实性降级"：写"行业普遍说法是 X，但官方未公开确认"，**不能写死**。

### ⚠️ Red Line 3: All non-English game names should follow user's locale-appropriate name / 红线 3：游戏名遵循目标读者的本地化习惯

按目标读者使用的语言习惯命名游戏。例如目标读者是中文用户，所有海外游戏一律使用中文名（详见 `checklists/中文名规范对照表.md`）；目标读者是英文用户则用英文名优先。导航栏 / 标题 / 案例索引一律统一命名规则。

---

## 标准工作流（四阶段）/ Standard Workflow (4 Phases)

### Phase 1: 立题对齐 / Topic Alignment (must be done first)

读 `workflow/01_topic-alignment.md`，**主动追问以下问题**直到全部明确：

1. **研究目标 / Research goal**：要回答什么问题？给谁看？
2. **边界 / Scope**：哪些游戏 / 平台 / 时间窗口 / 地区算在内？
3. **分类轴假设 / Taxonomy hypothesis**（如果用户已有想法）：先记录但不固化
4. **输出形式 / Deliverable format**：MD / HTML / PPT / 表格？要不要做交付物视图？
5. **决策选项化 / Multi-choice over open-ended**：给用户 A/B/C 选项，不要开放式提问

不要在立题没对齐前进入下一阶段。

### Phase 2: 案例池构建 / Case Pool (Agent 1 role)

读 `workflow/02_case-pool.md`。

输出 / Output：`01_case_pool/case-pool.md`（含厂商、品类、平台、首发时间、关键词标签、初判标签）

### Phase 3: 单案分析 / Single-case Analysis (Agent 2 role)

读 `workflow/03_single-case-analysis.md` 和 `templates/single-case-template.md`。

每个案例独立 MD，统一结构：核心问题 → 关键动作 → 平台资源 → 数据点 → 对发行方的参考意义 → 数据来源链接区块。

输出 / Output：`02_case_analysis/case_*.md`

### Phase 4: 综合洞察 / Cross-case Synthesis (Agent 3 role)

读 `workflow/04_synthesis.md` 和 `templates/synthesis-template.md`。

**综合洞察阶段是分类轴归纳的关键**：不要套用上一次的分类，从本次案例数据里观察哪些维度真正有差异、哪些动作有共性，再归纳路径。

输出 / Output：`03_synthesis/synthesis.md`

### Optional Phase 5: 应用层 / 交付物视图 / Application Layer & Deliverable View

如果用户要求做交付物，读 `workflow/05_deliverable.md`：
- HTML 集合页规范 见 `workflow/05_deliverable.md` 内嵌规范
- 应用层（用研究结论给具体产品做策略建议）见 `templates/application-template.md`

---

## 写作硬规则（贯穿整个工作流）/ Writing Hard Rules

读 `checklists/writing-rules.md`，关键点：

1. **一句话先行 / TL;DR first**：每个路径、每个案例、每个章节先一句话讲清楚是什么，再展开
2. **决策选项化提问 / Multi-choice questions**：给用户 A/B/C 选项，不开放式问
3. **对发行方的参考意义 / Practical takeaway**：每个案例最后必须落到"发行方可借鉴/不可复制"
4. **反面教材只反衬 / Counter-examples only as foil**：不单独立章，避免分散读者注意力
5. **关键传播素材高亮 / Highlight viral phrases**：HTML 用 `<span class="highlight">` 黄底高亮真实可被传播的素材原话
6. **路径前缀 / Path prefix in nav**：导航栏案例命名格式 "路径 N · 游戏名" / "Path N · GameName"

---

## 自检流程（每次产出前必跑）/ Pre-output Self-check

每次写完一份 MD / HTML 之前，对照 `checklists/output-self-check.md` 逐项核对：

- [ ] 所有海外游戏名命名统一（按目标读者本地化）
- [ ] 每个具体数字都有来源链接
- [ ] 一句话先行
- [ ] 反面教材没有单独立章
- [ ] 决策选项化提问
- [ ] 对发行方的参考意义已写

---

## 参考样例 / Reference Precedent

`references/research-methodology-precedent.md` 记录了一次完整研究的方法论沉淀——分类轴迭代史 + 8 个真实踩坑案例。

**这是参考样例，不是模板 / This is a precedent, NOT a template**：
- ✅ 可借鉴 / Reusable：工作流、写作风格、HTML 视觉规范
- ❌ 不要直接套用 / Don't copy directly：里面提到的具体路径分类是当时数据归纳出的，不一定适合下次的赛道/题目

---

## 这个 skill 不做什么 / What this skill does NOT do

- 不内置案例库，每次研究都从立题阶段从头开始
- 不预设路径分类，分类轴必须从本次案例数据归纳得出
- 不替代用户判断研究方向——立题阶段必须用户确认才能进入案例池构建

---

**最后一条心法 / Final principle**：游戏发行研究的真正价值不在"答案"，而在"问对问题 + 找对数据 + 看出规律"。skill 的作用是让 AI 帮用户少走方法论上的弯路，而不是替用户得出结论。

> The real value of game publishing research is not in the answers, but in asking the right questions, finding the right data, and spotting the patterns. This skill helps the AI avoid methodological pitfalls — it does not draw conclusions for the user.
