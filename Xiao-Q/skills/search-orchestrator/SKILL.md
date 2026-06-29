---
name: search-orchestrator
description: >
  全自动智能搜索编排器 v5.2。零配置自动发现并并行调用全部搜索工具，智能多语言query分流，深度迭代自动收敛。
  用于搜索、查资料、核事实、对比、深度研究、调研报告。全链路锚点审计+信息密度评分，每条结论可溯源自动聚合多源搜索。
  支持百度搜索/Tavily/高德地图/Brave/WebSearch/WebFetch/Browser等任何搜索Agent Skill，自动发现即插即用无需配置。
  触发词：搜索、搜一下、查资料、调研、对比、核事实、研究。
metadata:
  openclaw:
    emoji: "🔍"
    requires:
      bins: ["node"]
      env: []
---

# Universal Search — 通用搜索编排器 v5.2

**强制搜索引擎。discover.js 是唯一真相来源。广度全量并行，深度自动迭代直到收敛。全链路锚点锁定——偏离即作废。**

---

## ⚡ 快速开始（安装后必读）

安装此 skill 后，首次使用前请确保：

1. **安装搜索相关 skill**（至少一个，任意搜索类 skill 均可自动发现）：
   - `skillhub search search` — 查看可用的搜索类 skill
   - 安装后 orchestrator 会自动发现并纳入调用，零配置

2. **配置 API Key**（根据你装的 skill 要求，以下任选其一）：
   - 将 key 写入 skill 目录下的 `.env` 或 `config.json`
   - 或写入 `~/.openclaw/.env` 全局配置
   - 或设为环境变量

3. **验证发现**：`node scripts/discover.js --cache` 确认能扫描到已安装的工具

4. **一键搜索**：`node scripts/orchestrate.mjs "你的查询"`

> 💡 即使一个搜索 skill 都没装也能用——自动降级为系统内置的 `web_search` + `web_fetch`（Brave Search）。安装任意搜索 skill 后 orchestrator 自动发现并多源并行，无需额外配置。

## 🛑 硬门槛（开始搜索前，逐条过，少一条禁止搜索）

```
GATE-0: 先跑 discover.js --cache。不跑=违规。跳过=偷懒。没结果=别搜。
GATE-1: 从 discover 输出提取 ready 数组 → 记录 tool_count = ready.length
GATE-2: ready 中每个工具都必须被调用。不允许选择性调用。
GATE-3: 所有工具并行发起，不准串行、不准分批准。
GATE-QUERY: 不同工具用不同 query。中文喂中文/英文喂英文/地理加限定词。禁止同 query。
GATE-RELEVANCE: 所有 query（广度 + 深度每一轮）必须包含用户原始问题的核心关键词。偏离=无效轮次。
GATE-4: 回复前自检：tool_skip_ratio = (tool_count - actual_calls) / tool_count。必须为 0。
```

---

## ♟️ v5.2 自动化脚本

两个轻量脚本接管 v5.1 的手动步骤，向下完全兼容原有流程。**不强制使用，但推荐所有 L1/L2 搜索先跑 prepare 再跑 audit。**

### `scripts/prepare.mjs` — 搜索前准备

```bash
echo "原始问题" | node scripts/prepare.mjs
# 输出 JSON: { anchor_words, complexity, intent, tool_queries, gate_checklist }
```

**接管内容：** 锚点提取（中英文/分隔词切割+实体识别）→ 复杂度分级（L0/L1/L2）→ 意图路由 → GATE-QUERY 分流 → GATE checklist 全量

### `scripts/audit.mjs` — 搜索后审计

```bash
echo '{"query":"...","anchor_words":[...],"results":[...]}' | node scripts/audit.mjs
# 输出 JSON: { summary, backlink_details, signals, convergence, recommendations }
```

**接管内容：** 逐条三层回链 → 7信号自动检测 → 收敛判断 → 信息密度评分 → 低相关标记 → 建议

### `scripts/orchestrate.mjs` — 全自动一键编排（v5.2 新增）

```bash
node scripts/orchestrate.mjs "搜索内容"
# 或: echo "搜索内容" | node scripts/orchestrate.mjs
# 一次 exec 完成 prepare → 并行搜索 → audit → 输出 JSON
```

**自动化内容：** prepare + 全工具并行调用（自动加载 API key）+ 结果归一化 + audit，输出聚合 JSON

### 集成方式

```
discover.js --cache    → 环境发现（同 v5.1）
orchestrate.mjs        → 🆕 一键：prepare → 并行搜索 → audit
                       或手动分步：
  prepare.mjs          → 代替人工：锚点 + Q + 门
  （agent 并行搜索）    → 同 v5.1
  audit.mjs            → 代替人工：回链 + 信号 + 收敛
（agent 决策输出/深度）  → 同 v5.1
```

**已知限制：** 跨语言锚点字面匹配（中文锚点 vs 英文结果）；长复合词（如"磷酸铁锂电池"）未切分；信号⑤事实冲突需人工。

---

## 第零步：环境发现（强制，不可跳过）

```
node skills/search-orchestrator/scripts/discover.js --pretty --cache
```

- 首次运行：扫描 1-3 秒，写入 `/tmp/search-orchestrator-cache.json`
- 后续 1 小时内：秒级缓存命中
- 手动强制刷新：加 `--force`

**从输出中提取：**
- `tools`：完整工具列表及其 call.template
- `ready`：可直接调用的工具（id / strengths / call.template）
- `degraded`：缺 key 或缺依赖的工具（记录原因）

---

## 第一步：复杂度分级

| 级别 | 特征 | 处理 |
|------|------|------|
| **L0** | 单一事实、标准答案（"Python 最新版本号"） | 单工具 + web_fetch 验证 → 跳过深度 |
| **L1** | 常规查询、新闻、对比、资讯 | **全量并行 → 深度检查 → 多轮迭代** |
| **L2** | 深度研究、报告、全面分析 | **全量并行 → 强制≥2轮深度 → 不收敛不停** |

**铁律：不确定时走高级别。L0 升级到 L1 的门槛极低。**

---

## 第二步：意图路由

按查询特征匹配意图，决定 preferred_tools 排序，但**不限制最终工具集**：

```
意图            → 偏好排序
geographic      → amap-lbs 优先
chinese_news    → baidu 优先
chinese_general → baidu 优先
english_news    → tavily 优先
technical       → web_search 优先
fact_check      → web_search 优先
comparative     → web_search 优先
deep_research   → web_search 优先
english_general → tavily 优先
default         → web_search 优先
```

**偏好排序只影响调用顺序，不影响调用全集。**

---

## 第三步：广度搜索 Round 1（全量并行，一个不漏）

### 工具调用规则

```
1. 从 discover ready 列表中取所有工具
2. 排除纯地理工具（仅 geographic 标签）——但仅限非地理意图时
3. 其余全部纳入调用列表 → 并行执行
4. L0 可只调 1 个，L1/L2 必须全量
```

### builtin 工具

直接调系统工具：`web_search` / `web_fetch` / `browser`

### skill 工具

从 discover 输出取 `call.template`，替换 `{skill_dir}` 为 `skillPath`：

```
discover 输出 call.template: "cd {skill_dir} && BAIDU_API_KEY=... python3 scripts/search.py '<JSON>'"
→ exec("cd /path/to/skills/baidu-search && BAIDU_API_KEY=... python3 scripts/search.py '{\"query\":\"...\"}'")
```

全部并行 exec 执行。某工具报错/超时→记录跳过，不阻塞其他。

### GATE-QUERY：工具分流 query（禁止所有工具吃同一个 query）

不同工具擅长的语言和场景不同。必须按工具能力分流：

```
中文工具（baidu-search）          → 中文 query，含中文关键词
英文工具（tavily / web_search）       → 英文 query，语义相同但语种切换
地理工具（amap-lbs）                   → 加城市/坐标限定词
web_fetch                              → 抓 Round 1 返回的高价值 URL
browser                                → 仅 web_fetch 被拦截时兜底
```

**违规：** 所有工具用同一个 query = 浪费工具能力。

### GATE-RELEVANCE：query 锚定规则（所有轮次强制，违反=无效搜索）

**核心原则：每个 query 必须是原始问题的子集展开，不是新问题。偏离=本轮作废。**

1. **提取锚点词（强制执行）**：
   - 从用户原始问题中提取 2-4 个不可丢弃的核心词（实体名、动作、主题）
   - 锚点词必须是**排他性限定词**——换个词整个问题的语义就变了
   - 示例："中日军事冲突风险分析" → 锚点=["中日", "军事冲突"]（丢掉任何一个，问题变为别的议题）
   - 反例："Python 性能优化" → 锚点=["Python", "性能优化"]；"编程语言优化"=❌ 锚点已丢
   - **锚点词写入本轮记录开头**，每轮 query 对照检查

2. **query 构造公式**：`锚点词(必须原样出现) + 本轮要探索的子维度(必须是原始问题的子问题)`
   - ✅ `"中日军事冲突 2025 东海演习"` （锚点 + 时间线子维度）
   - ✅ `"US-China military tensions South China Sea 2025"` （锚点译版 + 地理子维度）
   - ❌ `"东海军事部署历史"` （丢了"中日"锚点，变成泛东海议题 → 本轮作废）
   - ❌ `"亚太安全局势分析"` （锚点全丢，主题漂移 → 本轮作废）
   - ❌ `"中国海军现代化建设"` （从"中日冲突"滑向"中国海军" → 子维度脱离原始问题）

3. **三层检查（缺一不可）**：
   - 层1「锚点在位」：query 中是否原样包含所有锚点词（或合理译版）？
   - 层2「去锚测试」：去掉锚点词后，query 是否有独立语义？有 → 违规，主题已漂移
   - 层3「回链测试」：这个 query 搜出来的结果，能直接回答原始问题的哪个部分？答不上来 → 违规

4. **web_fetch 同样锚定**：只抓取与原始问题直接相关的 URL。标题/摘要中不含锚点词 → 跳过。内容中锚点词出现<2次 → 低相关，仅摘录直接相关段落。

5. **地理工具特殊处理**：锚点词可能被地理限定词替代（如"北京周边"代替"朝阳区"），但原始问题语义必须保留。地理搜索 query 必须与原始问题有明确的地理语义关联。

6. **违规处置**：任何 query 未通过三层检查 → 该 query 结果标记「锚点偏离」，不计入独立源统计，不触发深度信号。整轮违规率 >30% → 本轮标记「低相关」，需重搜。

---

## 第四步：深度迭代 Rounds 2-5（自动触发，强制收敛）

**L0 跳过深度。**

**L1：min_depth = 1 轮。** 默认至少多搜一轮，除非 Round 1 已含 ≥3 个独立源且所有实体均有背景。

**L2：min_depth = 2 轮。** 默认至少多搜两轮，不收敛不停止。

### 自动触发信号（匹配任一即进入下一轮）

每轮结束时，扫描结果中是否出现以下信号。出现任意一条 → 必须进入下一轮，不可停止：

```
① 时效信号：查询含"最新/新闻/今天/突发/刚刚/热点/近日/本周"关键词
② 追问信号：查询含"为什么/原因/分析/对比/怎么样/具体/如何/影响/细节"关键词
③ 空壳实体：人名/公司/产品/事件名仅在结果中一笔带过，无背景展开
④ 单源数据：金额/百分比/日期/数字仅在 1 个来源中出现
⑤ 事实冲突：两个来源对同一事实描述不一致
⑥ 强要求信号：用户明确说"全面/深入/详细/研究报告/透彻"
⑦ 信息不足：整体独立源 < 3 个，或主题覆盖明显不完整
```

### 每轮执行

```
从上一轮结果中提取候选深挖方向 → 逐一过「锚点相关性门」 → 最多保留 3 个。
门控规则（逐条回答，缺一不可）：
  ① 该方向源自哪个具体结果片段？（必须可追溯）
  ② 该方向能直接帮助回答原始问题的哪个部分？（必须明确指出来，不能用"提供背景"敷衍）
  ③ 去掉锚点词后，该方向是否仍有独立语义？（有→丢弃）
  ④ 搜索该方向后得到的信息，能在最终答案中占据≥2句话的位置吗？（不能→丢弃）

从以下维度中选至少 2 个不同维度发散（每个维度必须锚定原始问题）：
  - 时间线：锚点 + "起因/后续/历史背景/最新进展"（不是泛时间线——必须与锚点实体直接相关的时间节点）
  - 地理：锚点 + 特定城市/地区（不是泛地理搜索——必须是锚点事件发生/影响的地理范围）
  - 人物/组织：锚点 + 具体实体名（仅限结果中露名但未展开、且与锚点事件有直接参与关系的实体）
  - 因果链：锚点 + "为什么会发生" / "会有什么影响"（不是独立的因果分析——因果关系必须指向锚点事件）
  - 数据验证：每个单源数字/金额/日期 → 锚点 + 数字 → 找第二源（不要搜到无关领域的数字）
  - 🚫 禁止方向：泛背景综述、泛领域科普、泛相关话题——这些是搜索膨胀的主要来源
     ↓
针对每个方向定向搜索（web_search / web_fetch / 原引擎定向 query）
每次 depth query 必须包含锚点词（遵循 GATE-RELEVANCE 三层检查）
     ↓
合并去重 → 过滤与锚点无关的结果（逐条过回链测试） → 检查收敛 ← 不收敛 → 再来一轮

**本轮输出前自检**：本轮新增的每条信息，能否直接填入原始问题的答案？能→保留展开，不能→压缩为一句话背景或直接丢弃。
```

### 收敛条件（全部满足才停）

```
✅ 每项核心结论 ≥ 2 个独立源
✅ 收敛自证：上一轮搜索新增了哪些与原始问题直接相关的独立源？列举出来。无新增相关源=收敛。
✅ 独立源总数 ≥ 3（仅统计通过回链测试的锚点相关源）
✅ 主题漂移检查：本轮新增内容 ≥80% 与锚点词直接相关。否则本轮标记「低相关」，不计入有效轮次，不计入源数。
✅ 膨胀检查：本轮新增内容中，有没有整段可以删除而不影响回答原始问题？有→未收敛，需更聚焦重搜。
✅ 达到最大轮数（L1 ≤ 4, L2 ≤ 5 — 硬上限，不管收敛与否都得停）
✅ 所有信号①-⑥已消除，且⑦已满足
✅ 信息密度合格：每条保留的信息都能回答"这一句在答案中起什么作用？"——事实支撑/因果解释/数据佐证/必要背景。答不上来→删除。
```

**不收敛 → 继续。达到硬上限 → 强制停并标注「已达到最大轮数」。</parameter>


---

## 第五步：输出

### 输出前强制审计（不可跳过）

**每条待输出信息逐条过「回链测试」**：
- 这条信息能直接回答原始问题的哪个部分？
- 去掉这条信息，原始问题的答案会缺失什么？
- 答不上来 → **删除**（不降级为背景，直接删除）

**信息密度自检**：
- 每个段落/句子承载的独特信息量是否≥1个事实？
- 有无套话、空泛描述、无关铺垫？有→删除。
- 背景信息是否超过总篇幅的15%？超过→压缩。

**最终答案结构**：
```
结论（1-3句，直接回答）→ 核心证据（有源数据）→ 补充细节（必要时）
```

### 输出规则

1. **结论先行**，再展开
2. **独立源 ≥ 2**，每项核心结论至少 2 个独立来源支撑。仅统计通过回链测试的来源。
3. **相关性过滤**：所有内容必须通过回链测试。不能直接回答原始问题的信息：不展开、不保留。
4. **信息密度优先**：每个句子承载一个事实/数据/观点。删除铺垫、套话、重复、泛背景。
5. **禁止输出**：泛领域背景、泛相关话题科普、仅"可能相关"的周边信息。
6. **搜索链路标注**（回复末尾必须包含）：

```
【广度链路】已发现工具: N | 已并行调用: N | tool_skip_ratio: 0 | 锚点偏离query: N
           引擎: toolA + toolB + toolC + ...
           锚点词: [x, y, z] | 回链通过率: X%
【深度链路】自动触发条件: ①时效 + ③空壳实体
           Round 2 → 锚定子方向: "XX详情" / "YY背景" | 丢弃: "ZZ"(无锚点词/回链失败)
           Round 3 → 交叉验证: "XX核实"
           收敛原因: 信号清除 + 独立源 ≥ 3 + 无新增锚点相关信息
           低相关轮次: R× (如有，标注原因)
【汇总】X 独立源(已过滤) | Y 轮有效深度 | 锚点相关率 ≥90% | 信息密度: 高
```

---

## 🖥️ System Tool Co-Execution（内置工具并行补调）

`orchestrate.mjs` 是子进程，**只能执行 shell 命令**，无法调用 OpenClaw agent 的 `web_search` / `web_fetch` / `browser` 系统工具。
这些系统工具必须由 **agent 并行补调**，否则工具覆盖率不完整。

### 触发时机

| 阶段 | 系统工具 | 何时调 |
|------|---------|--------|
| 启动 | `web_search` × 2 | **与 orchestrate.mjs 同时并行启动** |
| R1 后 | `web_fetch` × 3-5 | orchestrate 第一轮结束（拿到 URL 清单后） |
| 降级 | `browser` | web_fetch 被拦截时兜底 |

### agent 执行清单（强制）

```
① 跑 discover.js --cache → 确认 builtin:web_search / builtin:web_fetch 状态
② 同时并行启动:
   ├── exec: node orchestrate.mjs "原始问题"          ← shell 子进程
   ├── web_search: query_CN (中文综合，freshness=week)   ← agent 系统工具
   └── web_search: query_EN (英文交叉，freshness=week)   ← agent 系统工具

③ orchestrate 跑完 → 读取输出中的 system_tool_calls.web_fetch
   → 对每个 URL 调 web_fetch 获取全文

④ audit 审计时 web_search/web_fetch 的结果一并纳入回链检查
```

### GATE 更新

```
GATE-0: discover → 同时列出 skill 工具 + builtin 工具
GATE-1: tool_count = ready_skill + ready_builtin（两类都算）
GATE-2: 每个 ready 工具都必须被调用 — skill 由 orchestrate 调, builtin 由 agent 调
GATE-4: tool_skip_ratio = (tool_count - actual_calls) / tool_count。缺了 builtin = 违规
```

---

## 降级

| 场景 | 处置 |
|------|------|
| 仅 1 个 ready | 单工具 + web_fetch 抓 ≥2 关键页补源 |
| 纯内置工具 | web_search + web_fetch，提示可配更多 |
| 某工具超时/报错 | 跳过，不阻塞 |
| 全部返回空 | web_fetch 试候补 URL，诚实告知 |
| discover 报错 | 降级为 web_search + web_fetch + browser |

---

## 示例

### L1 标准搜索

```
用户: "中日军事冲突风险分析"
→ 锚点词提取: ["中日", "军事冲突", "风险分析"]
→ discover.js --cache → ready: [baidu, tavily, web_search, web_fetch, browser, amap-lbs]
→ L1 标准搜索，意图 chinese_news

→ 同时并行启动:
   ├── exec: orchestrate.mjs → baidu + tavily + ... (shell 子进程)
   ├── web_search: "中日军事冲突 风险分析" (agent 系统工具—中文)
   └── web_search: "China Japan military conflict risk" (agent 系统工具—英文)

→ orchestrate R1 结束 → 读取 system_tool_calls.web_fetch
   → web_fetch × 3 高价值 URL 全文抓取

→ Round 1 结束：触发清单 ☑ ③空壳实体（仅名提及"东海""钓鱼岛"等未展开）
→ 过锚点门：东海→锚点+"东海军事部署"✅ / 钓鱼岛→锚点+"钓鱼岛争端"✅
  丢弃项：泛"东亚地缘政治"→❌ 无关锚点，跳过
→ Round 2 深挖 2 个锚定方向
→ 收敛 → 输出

【复杂度】L1 标准搜索
【广度】已发现: N | 已并行调用: N (skill by orchestrate + builtin by agent) | tool_skip_ratio: 0
       工具: baidu-search + tavily + ... + web_search + web_fetch (动态发现)
       锚点词: [中日, 军事冲突, 风险分析] | 回链通过率: 92%
【深度】Round 2 → 锚定子方向: "东海军事部署" / "钓鱼岛争端"
       丢弃: "东亚地缘政治"(无锚点词,回链失败) / "中国海军现代化"(锚点偏离)
       低相关轮次: 无
【汇总】8 独立源(已过滤) | 2 轮有效深度 | 锚点相关率 95% | 信息密度: 高
```
