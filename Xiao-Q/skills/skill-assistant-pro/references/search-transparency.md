# 搜索透明度规范

搜索模块 Step 6 使用此文件。**搜索时无需加载此文件**——诊断数据收集和异常检测规则已内化为 Agent 执行行为，仅在输出格式有疑问或需要调整检测阈值时查阅。

> **设计理念**：搜索不是黑盒。用户必须能看到 Agent 用了什么关键词、查了多少条、筛掉了什么、每条结果因何而来——这样当搜索结果不符合预期时，用户可以精准干预（修关键词 / 深搜渠道 / 升级策略 / 补充或排除词），而不是盲目"换个说法再试一次"。

---

## 一、诊断数据模型

Agent 在 Step 2-5 执行搜索的同时，必须维护一份结构化诊断数据 `diagnostics`，在 Step 6 输出前汇总为诊断头。

```yaml
diagnostics:
  # 用户原始输入（完整保留，用于后续 refine）
  user_input: "简历 AI 助手"
  user_language: "zh"          # zh / en / mixed

  # 环境快照（Step 0.5 生成，全搜索只读）
  # 所有字段由 modules/search.md 第 0.5 步的快照脚本一次性填入
  # 后续步骤严禁重新探测（详见 SKILL.md NEVER 规则）
  environment:
    keys:
      KEY_SKILLSMP: "yes"      # yes / no
    tools:
      CLI_GH:       "ok"       # ok / unauth_or_err / missing / error
      CLI_SKILLHUB: "ok"
      CLI_NPX:      "ok"
      CLI_NODE:     "ok"
    # 由 Agent 从上述原始值派生，用于 0.5.2 路由表决策的人类可读摘要
    summary: "gh ✅ 已认证 · SkillsMP Key ✅ · SkillHub CLI ✅"

  # 关键词生成结果
  keywords:
    level_1:                   # 语义核心词
      - resume
      - cv
      - 简历
      - AI
      - agent
    level_2:
      a:                       # 精确匹配组
        keyword: "resume builder"
        hits: 7                # 在所有渠道的总候选命中数
        status: "ok"           # ok / weak / empty
      b:                       # 近义替代组
        keyword: "cv generator"
        hits: 2
        status: "weak"
      c:                       # 相关概念组
        keyword: "job application"
        hits: 0
        status: "empty"
    level_3:                   # 宽路单核心词
      keyword: "resume"
      hits: 95
    level_4:                   # 扩展词（仅触发时有值）
      triggered: false
      keywords: []
    chinese_variants:          # 中文平台变体（仅 zh/mixed 输入时）
      - "简历"
      - "简历生成"
    tags: []                   # 用户 #tag 格式输入

  # 渠道漏斗数据（每渠道独立）
  channels:
    - name: "skills.sh"
      enabled: true
      status: "ok"             # ok / skipped / failed
      skip_reason: null        # 仅 status=skipped 时有值
      candidates: 30           # 第 2 步返回原始条数
      after_dedup: 28          # 漏斗 1：去重后
      after_relevance: 12      # 漏斗 2：混合相关度筛后
      top_n: 3                 # 漏斗 3：精选输出条数
      max_installs: 7979       # 该渠道命中结果的最高热度（可选）
      warnings: []             # 本渠道特定警告

    - name: "skillhub"
      enabled: true
      status: "ok"
      candidates: 8
      after_dedup: 8
      after_relevance: 5
      top_n: 3
      warnings: ["候选偏少（<10）"]

    - name: "skillsmp"
      enabled: true
      status: "skipped"
      skip_reason: "missing_api_key"
      candidates: 0

    - name: "websearch"          # 第 4 路：WebSearch 兜底
      enabled: true              # 由 strategy + 触发条件决定是否实际执行
      status: "triggered"        # triggered / not_triggered / strategy_forced / disabled_by_strategy
      trigger_reason: "low_recall"    # low_recall / coverage_degraded / low_confidence / core_tools_missing / strategy_forced / null
      templates_used:            # 执行了哪些 WebSearch 查询模板（对应 channel-search-commands.md#websearch-调用约定）
        - "template_1"           # "{核心词} SKILL.md agent skill github"
        - "template_2"           # "{核心词} skills.sh OR skillhub OR ..."
      candidates: 14             # WebSearch 返回的网页条数（经初筛去广告/无效链接）
      after_link_extract: 9      # 抽取出的 GitHub/平台链接数
      after_dedup: 6             # 去掉已出现在前 3 路结果的
      top_n: 2                   # 进入精选池的数量
      awesome_list_hits: 1       # 识别出的 Awesome List 或博客索引数（进第 4 分区）
      warnings: []

  # 搜索策略
  strategy: "balanced"         # speed / balanced / thorough

  # 总漏斗汇总
  funnel_summary:
    total_candidates: 113
    after_dedup: 96
    after_relevance: 44
    final: 12

  # 异常清单（Agent 根据规则自动检测）
  anomalies:
    - code: "L2C_EMPTY"
      message: "L2-C 关键词 0 命中，可能需要补充近义词"
      suggestion: "补充关键词：job hunting / career builder"
    - code: "CHANNEL_THIN"
      channel: "skillhub"
      message: "SkillHub 候选仅 8 条"
      suggestion: "深搜 SkillHub（建议取前 30）"

  # 每条结果的命中归因（Step 5 筛选后填入每条 result）
  # 格式见下方「二、结果命中归因」
```

---

## 二、结果命中归因（per-result attribution）

Step 2 搜索结束后，每条候选结果 `result` 必须附带 `hits` 字段，记录命中了哪些关键词层级。这是 Step 6 结果表格「命中」列的数据来源。

```yaml
result:
  skill_name: "career-ops"
  owner_repo: "santifer/career-ops"
  source: "github-repos"
  hits:
    - level: "L3"              # 层级标识
      keyword: "resume"
      location: "description"  # 命中位置：name / description / tags / readme
    - level: "L2-A"
      keyword: "resume builder"
      location: "readme"
  confidence: 4.8              # 混合相关度得分
  recommendation: 4.5          # 推荐指数
```

### 命中标记格式（在「命中」列展示）

| 命中组合 | 展示格式 | 含义 |
|---|---|---|
| L3 + 任意 L2 精确组 | `🎯 L3 + L2-A` | 最强命中，宽窄都匹配 |
| L3 + 多个 L2 组 | `🎯 L3 + L2-A + L2-B` | 多维命中，极高信心 |
| 仅 L2 组（L3 未命中） | `✅ L2-A` | 精确词命中，用户需求定位清晰 |
| 仅 L3 宽路 | `⚠️ L3 only` | **只在宽路命中——需要用户二次判断匹配度** |
| L4 扩展词命中 | `➕ L4` | 扩展搜索的产物，通常权重最低 |
| 中文变体命中 | `🈯 中文` | 标注该结果来自中文关键词匹配 |
| 标签命中 | `🏷️ #tag` | `#tag` 搜索模式的产物 |

> **重要**：仅 L3 命中的结果必须标注 `⚠️ L3 only`——这是用户判断"搜索结果是否真的贴合需求"的核心信号。`⚠️` 不代表结果差，只是告诉用户该结果是宽路捞上来的、没有被任何精确词直接命中。

---

## 三、异常检测规则

Agent 在 Step 6 输出前，对 `diagnostics` 数据运行以下规则，命中即写入 `diagnostics.anomalies[]`，并在诊断头「⚠️ 注意事项」区展示。

| 规则 code | 触发条件 | 警告文案模板 | 建议 refine 分支 |
|---|---|---|---|
| `L2A_EMPTY` | L2-A 命中 = 0 | L2-A 精确词「{kw}」0 命中——可能关键词方向偏离需求 | 7 修改关键词 |
| `L2B_EMPTY` | L2-B 命中 = 0 | L2-B 近义词「{kw}」0 命中 | 10 补充近义词 |
| `L2C_EMPTY` | L2-C 命中 = 0 | L2-C 相关词「{kw}」0 命中 | 10 补充相关概念 |
| `L2_ALL_WEAK` | L2 总命中 < L3 命中 × 30% | 所有窄路普遍失效，宽路占主导——关键词精确度不足 | 7 修改关键词 / 9 升级策略 |
| `CHANNEL_THIN` | 任意渠道 `candidates < 10` 且 `status=ok` | {channel} 候选仅 {N} 条，可深搜 | 8 深搜该渠道 |
| `CHANNEL_SKIPPED` | 任意渠道 `status=skipped` | {channel} 被跳过（{skip_reason}） | 配置 API Key / 安装依赖 |
| `LOW_TOP_CONFIDENCE` | Top N 最高混合相关度 < 3.0 | 最高相关度仅 {score}，未命中高相关结果 | 7 修改关键词 / 9 升级策略 |
| `STRATEGY_UPGRADE_RECOMMENDED` | 策略 ≠ thorough 且 final < 5 | 当前 {strategy} 策略仅返 {N} 条，可升级为 thorough | 9 升级策略 |
| `MISSING_CN_VARIANTS` | `user_language` 含 zh 且 `chinese_variants` 为空 | 用户输入含中文但未生成中文变体——可能遗漏中文平台结果 | 10 补充中文关键词 |
| `COMPOUND_QUERY_IN_GH_REPOS` | `gh search repos` 首轮关键词词数 > 1 或附加了 `--language/--stars` 过滤 | **违反 NEVER 规则**：`gh search repos` 第一轮使用了复合查询/过滤器 | 立即重搜（单核心词） |
| `ALL_L3_ONLY` | Top N 中 ≥ 80% 结果仅 L3 命中 | 精选结果主要来自宽路命中，精确度偏低 | 7 修改关键词 |
| `TOOL_UNAVAILABLE` | `environment.tools.*` 任一 = `missing` / `unauth_or_err` 且该工具是某路径的强依赖 | {tool} 不可用（{reason}）→ {path} 路降级；建议 {install_hint} | 安装对应工具后重搜 |
| `CHANNEL_UNREACHABLE` | `environment.network.NET_*` = `token_invalid` / `endpoint_404` / `network_fail` | {channel} 不可达（{reason}），已跳过——可能遗漏该渠道独有结果 | 更新凭证 / 换备用端点 后重搜 |
| `RUNTIME_RECHECK_DETECTED` | 搜索过程中出现 `which` / `gh auth status` / `skillhub --version` 等工具探测调用（违反 0.5 快照约束） | **违反 NEVER 规则**：绕过环境快照现场探测工具，可能因输出错位误判可用性 | 修复 Agent 执行逻辑，所有状态读自 `environment` |
| `WEBSEARCH_FALLBACK_TRIGGERED` | balanced 策略下命中 4 条触发条件任一 / thorough 策略默认常驻 | 已因 {trigger_reason} 自动补充 WebSearch 兜底（执行模板 {templates_used}，新增候选 {N} 条） | 用户可通过菜单选择"忽略第 4 分区结果"或"升级到 thorough 扩大 WebSearch 查询覆盖" |
| `WEBSEARCH_FALLBACK_NOT_TRIGGERED` | balanced 策略下**所有** 4 条触发条件均未命中但用户输出不满意 | balanced 本次无需兜底（召回 {N}≥20 / 覆盖完整 / Top 置信度 {score}≥3.0 / 工具可用）——如仍想扩大搜索面可手动升级到 thorough | 菜单 9 升级策略 |
| `LAYOUT_NON_TABLE` | 输出中任意「按来源分区」段 / 诊断头关键词表 / 渠道漏斗表 / 跨源比较 / 推荐方案未使用 markdown 表格结构（检测：分区标题 3 行内无 `\| # \|` 表头行） | **违反 NEVER 规则**：结构化信息用了列表/卡片/段落——破坏透明度主线，用户无法快速扫读 | **Agent 必须自行重写输出**为表格形式，不得交付用户 |
| `DIAGNOSTICS_MISSING` | Step 6 输出前 `diagnostics` 对象缺少必填字段（keywords / channels / funnel_summary / environment 任一为空或未定义） | **违反透明度硬约束**：未收集完整诊断数据就输出结果 | **Agent 必须回退补全数据后重新输出**，不得只给结果 |

> **阈值校准**：如果某条规则误报/漏报明显，可在此表格调整阈值（如 `CHANNEL_THIN` 的 10 条阈值改为 5 条）。阈值是工程参数，不是产品承诺。

### 异常严重等级

| 等级 | 标记 | 处理 |
|---|---|---|
| **🚨 阻断** | `COMPOUND_QUERY_IN_GH_REPOS` / `RUNTIME_RECHECK_DETECTED` / `LAYOUT_NON_TABLE` / `DIAGNOSTICS_MISSING` | 必须展示在诊断头顶部；`LAYOUT_NON_TABLE` / `DIAGNOSTICS_MISSING` 等展示/数据级阻断应在**Agent 自检环节**触发——Agent 必须回退重写输出，不得将带此类阻断的结果交付用户 |
| **⚠️ 警告** | `L2X_EMPTY` / `LOW_TOP_CONFIDENCE` / `CHANNEL_THIN` / `TOOL_UNAVAILABLE` / `CHANNEL_UNREACHABLE` | 展示在诊断头「注意事项」区，附带修复建议 |
| **ℹ️ 提示** | `STRATEGY_UPGRADE_RECOMMENDED` / `CHANNEL_SKIPPED` / `MISSING_CN_VARIANTS` / `WEBSEARCH_FALLBACK_TRIGGERED` / `WEBSEARCH_FALLBACK_NOT_TRIGGERED` | 展示在诊断头末尾，小字体 |

---

## 四、诊断头输出模板

### 完整版（balanced / thorough 策略默认使用）

```markdown
## 🔍 搜索诊断

**你的需求**：「{user_input}」

### 环境快照（Step 0.5 采集，全搜索只读）

| 类别 | 状态 |
|---|---|
| 凭证 | SkillsMP {KEY_SKILLSMP_icon} |
| CLI 工具 | gh {CLI_GH_icon} · skillhub {CLI_SKILLHUB_icon} · npx {CLI_NPX_icon} |

> 图标：✅ ok / 🔒 unauth / ❌ missing / 🔑 no_key / 🚫 unreachable
> 本次搜索**只读**此快照——路径启用/跳过的决策依据在此；不认可时可 `/search recheck` 重新探测。

### 关键词生成

| 层级 | 关键词 | 命中候选数 | 状态 |
|---|---|---|---|
| L3 宽路 | `{level_3.keyword}` | {hits} | {status_icon} |
| L2-A 精确 | `{level_2.a.keyword}` | {hits} | {status_icon} |
| L2-B 近义 | `{level_2.b.keyword}` | {hits} | {status_icon} |
| L2-C 相关 | `{level_2.c.keyword}` | {hits} | {status_icon} |
| 中文变体 | `{chinese_variants.join(" / ")}` | — | 🈯 启用 |

> 状态图标：✅ 正常命中 / ⚠️ 命中偏少（< 5） / ❌ 零命中

### 渠道漏斗

| 渠道 | 候选 | 去重 | 相关度筛 | Top N | 备注 |
|---|:-:|:-:|:-:|:-:|---|
| skills.sh | 30 | 28 | 12 | 3 | — |
| SkillHub | 8 | 8 | 5 | 3 | ⚠️ 候选偏少 |
| GitHub code | 45 | 38 | 18 | 3 | — |
| GitHub repos | 30 | 22 | 9 | 3 | — |
| SkillsMP | — | — | — | — | ⏭️ 跳过（缺 API Key） |
| 🌐 **WebSearch 兜底** | 14 | 6 | — | 2 + 1(awesome) | ⚙️ 触发：low_recall |
| **合计** | **127** | **102** | **44** | **14** | 策略：balanced |

> **WebSearch 行**：status = `triggered` 时填入实际数据并在备注标触发原因；status = `not_triggered` 时整行显示 `—`；status = `strategy_forced`（thorough）时备注标 `✅ 默认常驻`；speed 策略下**不显示该行**。

### ⚠️ 注意事项（{N} 条）

- **L2-C 关键词 0 命中**：「{kw}」可能过于宽泛，建议补充近义词（→ 菜单 10）
- **SkillHub 候选仅 8 条**：可深搜到前 30（→ 菜单 8）
- **SkillsMP 被跳过**：配置 API Key 后可追加搜索结果（→ 配置引导）
```

### 精简版（speed 策略或结果完全符合预期时使用）

```markdown
🔍 **搜索关键词**：`resume`（宽）/ `resume builder` / `cv generator` ｜ **候选**：113 → **精选**：12 ｜ **策略**：balanced ｜ **环境**：gh✅ SkillHub✅ SkillsMP✅ ｜ 输入 `/search debug` 查看完整诊断
```

> 精简版也必须保留「环境」字段一行——这是用户判断"搜索覆盖是否完整"的唯一线索。环境异常（任一 🔒/❌/🚫）时自动升级为完整版。

### 选择规则

| 场景 | 使用版本 |
|---|---|
| 用户初次搜索 + balanced/thorough 策略 | 完整版 |
| speed 策略且无异常 | 精简版 |
| 有任意 🚨 阻断级异常 | 完整版（强制） |
| 用户在 refine 菜单发起二次搜索 | 完整版（必须展示变化 diff） |

---

## 五、Refine 后诊断头变化展示

用户通过菜单 7-11 触发 refine 后，重新输出的诊断头必须展示**变化 diff**，让用户清楚看到"我的调整带来了什么效果"。

```markdown
## 🔍 搜索诊断（Refine #2）

**变化**：
- L2-A：`resume builder` → **`ATS resume`**（用户修改）
- 策略：balanced → **thorough**（用户升级）

### 对比（上次 → 本次）

| 指标 | 上次 | 本次 | 变化 |
|---|:-:|:-:|:-:|
| 总候选 | 113 | 187 | +74 |
| 相关度筛后 | 44 | 68 | +24 |
| Top 最高置信度 | 2.1 ⚠️ | 4.3 ✅ | +2.2 |
| L2-A 命中 | 0 ❌ | 12 ✅ | +12 |

（关键词和渠道漏斗同完整版）
```

---

## 六、Agent 实施提示

### 数据收集时机

| 阶段 | 需要记录 |
|---|---|
| Step 1 理解需求 | `user_input` / `user_language` |
| Step 2.1 关键词生成 | `keywords.*`（所有层级） |
| Step 2.3-2.5 各渠道搜索 | 每渠道 `candidates` + 原始结果 |
| Step 5 漏斗 1 去重 | 每渠道 `after_dedup` |
| Step 5 漏斗 2 相关度 | 每渠道 `after_relevance` + 每 result `hits` |
| Step 5 漏斗 3 精选 | 每渠道 `top_n` + `funnel_summary` |
| Step 6 输出前 | 运行异常规则，填 `anomalies[]` |

### 性能开销

诊断数据的收集和展示**不应**增加额外的 API 调用或搜索耗时——所有数据都是 Step 2-5 本来就有的中间态，只是以前丢弃，现在保留。

### 失败降级

- 如果 Agent 未能收集某个渠道的 `after_dedup` 或 `after_relevance`（如异常中断），该单元格显示 `—` 而非 `0`
- 如果异常检测规则本身抛错，跳过该规则，其他规则继续

### 与 NEVER 列表的协同

诊断头会自动把违反 NEVER 规则的情况（如 `COMPOUND_QUERY_IN_GH_REPOS`）显性化——这是一种自我约束机制，让"违规搜索"变得可见，而不是悄悄执行。

---

## 七、隐私考虑

诊断头展示的都是 Agent 自己生成的搜索参数和公开 API 的返回量，**不含**：

- 用户 API Key 的任何部分
- 用户在搜索前扫描到的已安装 Skill 列表全文（只在"已安装对比"区按需展示）
- 工作区的文件/路径信息

诊断头可以安全地复制粘贴到工单/分享给团队，用于排查搜索偏差。
