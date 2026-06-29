# Game Publishing Case Study · Skill

> 游戏发行案例研究方法论 skill — 让 AI 用专业研究方法论辅助你的游戏发行 / 推广 / 出海 / 营销案例研究工作。
>
> A methodology skill for AI-assisted game publishing case study research.

**Author**: mandy · **License**: MIT · **Version**: 1.0.0

---

## 中文 · Chinese

### 这个 skill 解决什么问题

游戏发行研究往往需要：

- 横向看几十个案例归纳路径
- 一句话讲清楚每个路径的差异
- 给具体产品落地策略建议
- 产出可视化交付物（HTML / 报告）

如果让 AI 不带方法论地做这件事，每次都得从头跟它对齐"案例怎么选、分类轴怎么定、引用源怎么写、本地化怎么做"——非常累。

这个 skill 把上述方法论写死，让 AI **每次接到游戏发行类需求时自动按方法论工作**。

### 关键设计：不预设路径分类

游戏行业变化快——主机政策、平台战略、品类红海、营销渠道每年都变。把上一次研究归纳出的路径直接套用到下一次研究上，会让分类轴绑架数据。

**所以这个 skill 强制：每次研究都从立题阶段重新开始，分类轴必须从本次案例数据归纳得出。**

### 核心组件

```
game-publishing-research/
├── SKILL.md                          # 主入口（触发条件 + 红线 + 工作流总览）
├── workflow/                         # 四阶段流程详解
│   ├── 01_topic-alignment.md
│   ├── 02_case-pool.md
│   ├── 03_single-case-analysis.md
│   ├── 04_synthesis.md
│   └── 05_deliverable.md
├── checklists/                       # 硬约束清单
│   ├── writing-rules.md              # 13 条写作硬规则
│   ├── localized-name-glossary.md    # 海外游戏中英文名对照
│   └── output-self-check.md          # 产出前自检清单
├── templates/                        # 直接可用模板
│   ├── single-case-template.md       # 单案分析模板
│   ├── synthesis-template.md         # 综合洞察模板
│   └── application-template.md       # 应用层（产品策略建议）模板
└── references/                       # 真实研究方法论沉淀
    └── research-methodology-precedent.md
```

### 工作流（四阶段）

| 阶段 | 角色 | 产物 |
|---|---|---|
| 1. 立题对齐 | — | 研究目标 + 范围 + 分类轴假设 + 输出形式 |
| 2. 案例池构建 | Agent 1 | 案例池清单 |
| 3. 单案分析 | Agent 2 | 每个案例独立 MD（含来源链接） |
| 4. 综合洞察 | Agent 3 | 跨案归纳路径分类 + 共通打法 |
| 5. 应用层（可选） | — | 给具体产品的策略建议 + HTML 集合页 |

### 触发方式

只要满足以下任一条件，AI 会自动加载本 skill：

- 用户提到"游戏发行 / 推广 / 案例研究 / 复盘 / 综合洞察 / 出海策略 / 营销打法 / 路径分类"
- 用户给出具体游戏名 + "怎么做发行 / 怎么推广 / 主机版本 / 出海 / 上架 / 营销"
- 用户提到 F2P / 付费 3A / 主机厂商合作 / KOL / 平台资源 等领域词汇
- 用户在游戏研究项目目录下工作

### 适用范围

- ✅ 主机游戏发行研究（Sony / Xbox / Nintendo）
- ✅ F2P / 付费 3A 案例研究
- ✅ 海外发行 / 出海策略研究
- ✅ KOL / 平台资源 / 渠道矩阵研究
- ✅ 给具体产品做主机版 / 海外版策略建议
- ⚠️ 手游买量、电竞赛事、IP 运营等其他游戏赛道——方法论可借鉴，但分类轴需重新归纳
- ❌ 非游戏行业的研究——本 skill 提供游戏行业语境，不适用其他领域

---

## English

### What this skill does

Game publishing research often involves:

- Reviewing dozens of cases horizontally to induce paths/patterns
- Stating each path's differentiation in one sentence
- Translating findings into actionable strategy for a specific product
- Producing visual deliverables (HTML / reports)

Without a methodology, every research session requires re-aligning the AI on case selection, taxonomy axis, citation rules, localization handling — exhausting.

This skill encodes the methodology so the AI **automatically follows it whenever a game publishing research task is detected**.

### Key design: NEVER preset path taxonomy

The game industry changes fast. Reusing last research's path taxonomy on a new study lets the old framework hijack the new data.

**This skill enforces: every research starts from topic alignment, and the taxonomy axis MUST be induced from the current case data.**

### Workflow (4 phases)

| Phase | Role | Output |
|---|---|---|
| 1. Topic Alignment | — | Research goal + scope + taxonomy hypothesis + output format |
| 2. Case Pool | Agent 1 | Case pool list |
| 3. Single-case Analysis | Agent 2 | Individual case MD with citations |
| 4. Cross-case Synthesis | Agent 3 | Induced path taxonomy + common patterns |
| 5. Application (optional) | — | Product-specific strategy advice + HTML collection page |

### Triggers

The skill auto-loads when:

- User mentions "game publishing / promotion / case study / synthesis / go-to-market / marketing strategy / path taxonomy"
- User gives a specific game name + "how to publish / promote / console version / overseas launch / marketing"
- User mentions F2P / Premium 3A / first-party platform partnerships / KOL / platform resources
- User works in a game research project directory

### Scope

- ✅ Console game publishing research (Sony / Xbox / Nintendo)
- ✅ F2P / Premium 3A case studies
- ✅ Overseas publishing / go-to-market research
- ✅ KOL / platform resource / channel matrix research
- ✅ Console / overseas strategy advice for specific products
- ⚠️ Mobile UA, esports, IP licensing — methodology reusable, taxonomy must be re-induced
- ❌ Non-gaming industry — this skill provides gaming context only

---

## 安装 / Installation

### 通过 SkillHub / Via SkillHub

```bash
npx clawhub install game-publishing-research --workdir ~ --dir .workbuddy/skills
```

### 手动安装 / Manual install

```bash
# Clone or download this repo
git clone <repo-url> ~/.workbuddy/skills/game-publishing-research
```

或将整个目录复制到 `~/.workbuddy/skills/game-publishing-research/`，重启 WorkBuddy 即可。

---

## 卸载 / Uninstall

```bash
rm -rf ~/.workbuddy/skills/game-publishing-research
```

---

## 反馈 / Feedback

Issues / PRs welcome. 欢迎反馈和贡献。

---

## License

MIT License © 2026 mandy
