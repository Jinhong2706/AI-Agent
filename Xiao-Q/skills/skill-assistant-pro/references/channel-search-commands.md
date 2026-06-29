# 渠道搜索命令模板

搜索模块 Step 2 使用此文件。**搜索时无需加载此文件**——命令已内化为 Agent 执行行为。
仅在需要查阅具体 API 端点、请求体格式、响应字段时按需加载对应渠道章节。

---

## 平台型搜索

### skills.sh

```bash
# 宽路：核心词，limit=30，按安装量排序
curl -s "https://skills.sh/api/search?q={核心词}&limit=30" \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
skills = sorted(data.get('skills', []), key=lambda x: x.get('installs', 0), reverse=True)
for s in skills[:30]:
    print(f\"{s['source']}@{s['skillId']}  {s['installs']:,} installs\")
"

# 窄路：精确词，5 条
npx skills find "{核心词+限定词}"
```

> 宽路用 curl API（CLI 硬编码 limit=10 + Top 6），窄路用 CLI 即可。无 Node 时窄路也用 curl API（`limit=5`）。

### SkillHub / ClawHub

```bash
# 宽路：核心词，取前 20
skillhub search "{核心词}" | head -60

# 窄路：精确词，取前 5
skillhub search "{核心词+限定词}" | head -15
```

### SkillsMP（REST API）

```bash
# 宽路：核心词，20 条
curl -s "https://skillsmp.com/api/v1/skills/search?q={核心词}&sortBy=stars&limit=20" \
  -H "Authorization: Bearer ${SKILLSMP_API_KEY}"

# 窄路：精确词，5 条
curl -s "https://skillsmp.com/api/v1/skills/search?q={精确词}&sortBy=stars&limit=5" \
  -H "Authorization: Bearer ${SKILLSMP_API_KEY}"
```

返回 JSON：`stars`（源仓库 Stars）、`author`、`description`、`githubUrl`、`skillUrl`、`updatedAt`。

**无 Key** — 跳过 SkillsMP，搜索结束后提示配置。

---

## GitHub 优质仓库搜索

`gh search code` 跨仓库合并搜索（一条命令搜多仓库）：

```bash
# 模板 A：核心词搜 SKILL.md（跨所有优质仓库）
gh search code "{核心词}" \
  --repo anthropics/skills \
  --repo VoltAgent/awesome-openclaw-skills \
  --repo ComposioHQ/awesome-claude-skills \
  --repo obra/superpowers \
  --filename SKILL.md --limit 20 --json repository,path,textMatches

# 模板 B：精确词搜 SKILL.md
gh search code "{精确词}" \
  --repo anthropics/skills --repo VoltAgent/awesome-openclaw-skills \
  --repo ComposioHQ/awesome-claude-skills --repo obra/superpowers \
  --filename SKILL.md --limit 10 --json repository,path,textMatches

# 模板 C：核心词搜 README.md（策展合集）
gh search code "{核心词}" \
  --repo VoltAgent/awesome-openclaw-skills --repo ComposioHQ/awesome-claude-skills \
  --filename README.md --limit 10 --json repository,path,textMatches
```

> `anthropics/skills` 结果可直接信任（🏢 官方）。`ComposioHQ/awesome-claude-skills` 默认分支是 `master`。

**用户自定义仓库**（`sources.yaml` 中 `repos` 段新增的）追加到 `--repo` 参数。

**gh 不可用时降级**：

| 层级 | 方式 | 说明 |
|------|------|------|
| 优先 | WebSearch 兜底 | `{核心词} SKILL.md site:github.com/{owner}/{repo}`，逐仓库 |
| 兜底 | `curl` raw.githubusercontent.com | 直接抓取 README.md 原始内容，文本匹配 |

---

## 全 GitHub 搜索

> ⚠️ **MUST — `gh search repos` 第一轮硬约束**：
> 1. **必须用 Level 3 单核心词**（1 个最短词，不带修饰词），不叠加 `--language` / `--stars` 过滤
> 2. 语言/Stars 过滤只能作为**第二轮补充**（第一轮结果 > 30 条需要收敛时）
> 3. **违反示例**：~~`gh search repos "resume AI generator" --language=python --stars=">=100"`~~
>    - `"resume AI generator"` 是 3 词复合查询，违反「简单核心词优先」
>    - `--language=python` 会踢掉 Go/Node/TS 大型项目（如 `santifer/career-ops` ⭐38K Go）
>    - `--stars=">=100"` 会踢掉新锐高质量项目
> 4. **正确示例**：`gh search repos "resume" --sort stars --limit 30`，然后再按语言/领域在结果中筛选

```bash
# 宽路：核心词搜所有公开 SKILL.md
gh search code "{核心词}" --filename SKILL.md --limit 20 --json repository,path,textMatches

# 窄路：精确词搜高 Stars 仓库（⚠️ 禁止叠加 --language / --stars）
gh search repos "{单核心词}" --sort stars --limit 30 --json fullName,stargazersCount,description,updatedAt,language
```

**可选：非 Skill 源**（用户需要时才搜索）：

```bash
# ⚠️ 同样禁止第一轮叠加语言/Stars 过滤
gh search repos "{单核心词}" --sort stars --limit 10 --json fullName,stargazersCount,description,updatedAt,language
```

非 Skill 源标注 `📦 非 Skill — 可转化`。

**第二轮收敛**（可选，仅当第一轮返回 > 30 条且需要收敛时）：
在已拿到的结果集内按语言/Stars 在 Agent 侧筛选，**不要**二次调用 `gh search repos` 加过滤参数——会丢失第一轮的高质量结果。

**gh 不可用降级**（WebSearch 兜底）：`WebSearch: "{核心词} SKILL.md site:github.com"`

---

## 搜索策略完整定义

用户在首次引导（setup.md）中选择策略，存入 `sources.yaml` 的 `preferences.search_strategy`。

> ⚠️ **术语澄清**：以前文档里的"全网搜索"语义混淆，同时指代 GitHub 全公开搜索和 WebSearch 网页搜索。现已正式拆分为两路：
> - **全 GitHub 搜索** = `gh search code` 全公开 + `gh search repos`，覆盖域仍是 GitHub 仓库
> - **WebSearch 兜底** = Agent 直接调用 `WebSearch` 工具，覆盖域是**真正的网页**（博客 / Awesome List / 社区文章 / Twitter / CSDN / 掘金 / 微信公众号 / iwiki 等非 GitHub 源）

### speed（快速）

**适用场景**：用户已知需求明确，想尽快拿到前几个结果。

| 维度 | 行为 |
|------|------|
| 平台 | 仅 skills.sh + SkillHub（无需 API Key 的快速渠道） |
| 优质仓库 | gh 仅模板 A（核心词搜 SKILL.md） |
| 全 GitHub 搜索 | 跳过 |
| **WebSearch 兜底** | **永不启用** |
| 关键词层级 | Level 3 宽路 + Level 2 组 A（跳过组 B/C，不触发 Level 4） |
| 每渠道结果数 | Top 2 |
| 预计耗时 | 最短（2-3 个并行请求） |

### balanced（均衡）— 默认

**适用场景**：大多数搜索场景，覆盖与效率的平衡。

| 维度 | 行为 |
|------|------|
| 平台 | 所有已启用平台 |
| 优质仓库 | gh 跨仓库 3 模板（A/B/C） |
| 全 GitHub 搜索 | gh search code + gh search repos |
| **WebSearch 兜底** | **条件触发**（见下方触发规则）——满足任一条件时自动补一路 WebSearch |
| 关键词层级 | Level 2 全部（A/B/C） + Level 3 宽路（Level 4 仅结果 < 5 时触发） |
| 每渠道结果数 | Top 3 |
| 预计耗时 | 中等（5-8 个并行请求，触发 WebSearch 时 +1-2 路） |

**balanced 下 WebSearch 兜底触发规则**（**任一**满足即自动补一路，不需用户确认）：

| 触发条件 | 判断依据 | 异常规则 code |
|---|---|---|
| **A. 召回过低** | `funnel_summary.total_candidates < 20` | `WEBSEARCH_FALLBACK_TRIGGERED` (reason: `low_recall`) |
| **B. 覆盖受损** | `diagnostics.channels[*].status == "skipped"` 的数量 ≥ 2 | `WEBSEARCH_FALLBACK_TRIGGERED` (reason: `coverage_degraded`) |
| **C. 置信度不足** | Top N 最高混合相关度 < 3.0（即已触发 `LOW_TOP_CONFIDENCE`） | `WEBSEARCH_FALLBACK_TRIGGERED` (reason: `low_confidence`) |
| **D. 核心工具缺失** | `environment.tools.CLI_GH ≠ ok` 且 `environment.keys.KEY_SKILLSMP == no` | `WEBSEARCH_FALLBACK_TRIGGERED` (reason: `core_tools_missing`) |

> **条件触发的设计理由**：balanced 的定位是"均衡"，默认常驻 WebSearch 会压缩 thorough 差异化；只在结构性信号（召回低 / 覆盖损 / 置信度差 / 工具缺）出现时自动补救，既保留正常路径性能，也保证异常场景下有底可兜。

### thorough（全面）

**适用场景**：用户想全面了解市面上有什么，不怕耗时。

| 维度 | 行为 |
|------|------|
| 平台 | 所有平台（含已禁用的，标注为 _未启用_ 提示用户可开启） |
| 优质仓库 | 全模板 + curl README 补充 |
| 全 GitHub 搜索 | 含非 Skill 源（标注"📦 可转化"） |
| **WebSearch 兜底** | **默认常驻**（强制执行，至少 2 条查询） |
| 关键词层级 | 全部 Level（Level 4 扩展始终执行） |
| 每渠道结果数 | Top 5 |
| 预计耗时 | 最长（10+ 个请求，含 WebSearch） |

### 策略覆盖对照表

| 维度 | speed | balanced | thorough |
|------|:---:|:---:|:---:|
| 第 1 路（多平台） | skills.sh + SkillHub | 所有已启用 | 所有平台 |
| 第 2 路（优质仓库） | gh 模板 A | gh 3 模板 | 全模板 + curl README |
| 第 3 路（全 GitHub） | ❌ 跳过 | ✅ code + repos | ✅ 含非 Skill 源 |
| **第 4 路（WebSearch 兜底）** | ❌ 永不 | ⚙️ 条件触发（4 条件任一） | ✅ 强制 2 条 |
| 关键词层级 | L3 + L2-A | L2 全部 + L3 | 全部 + L4 |
| 每渠道 Top N | 2 | 3 | 5 |
| 结果稀缺（< 5）| 升级为 balanced | 触发条件 A 自动补 WebSearch | 已包含 |
| 无 gh CLI | ✅ 不受影响 | 触发条件 D 补 WebSearch | 触发条件 D 补 WebSearch |

> **结果稀缺自动升级**：speed 策略下总结果 < 5 时，自动升级为 balanced 重搜（不需要用户确认）；balanced 下结果不足优先触发 WebSearch 兜底而非升级到 thorough。

### WebSearch 调用约定

Agent 使用 `WebSearch` 工具执行（不要用 `gh search code` / `gh search repos` 假装成 WebSearch），查询模板按优先级：

| 优先级 | 查询模板 | 目的 |
|:-:|---|---|
| 1 | `"{核心词} SKILL.md agent skill github"` | GitHub 之外的 Skill 介绍（博客/文档/索引页） |
| 2 | `"{核心词} skills.sh OR skillhub OR clawhub OR skillsmp"` | 各平台 Skill 详情页（绕过平台搜索盲区） |
| 3 | `"{核心词} awesome claude skill OR awesome agent skill"` | Awesome List 类策展 |
| 4 | `"{中文核心词} AI skill 技能"` | 中文博客/公众号/CSDN/掘金（仅中文输入时） |

**thorough** 默认执行模板 1 + 2（必填），3 + 4 按需。
**balanced 触发时**：按触发原因选模板——`low_recall` → 模板 1 + 2；`coverage_degraded` → 模板 2；`low_confidence` → 模板 1 + 3；`core_tools_missing` → 模板 1 + 4（中文输入时）。

### WebSearch 结果后处理

WebSearch 返回的**不是 Skill**，是网页。必须经过 Agent 二次识别：

1. **抽取 GitHub 链接**：正则匹配 `github\.com/[\w-]+/[\w-]+`，去重后检查是否已在前 3 路结果中
2. **抽取 Skill 平台链接**：`skills\.sh/.+`、`skillhub\..+/skills/.+`、`skillsmp\.com/.+` 等，视为"已在平台型市场收录"的反向发现
3. **识别 Awesome List**：URL 含 `awesome-*` 或标题含 `Awesome`，内容可提取为潜在 Skill 列表
4. **不可直接安装的标注**：网页本身不是 Skill，第 4 分区输出必须醒目标注`⚠️ 非直接安装源，需 Agent 识别转化`

**输出位置**：见 [output-templates.md#第-4-分区websearch-兜底参考](output-templates.md#第-4-分区websearch-兜底参考)。

---

## API 请求失败处理

Key 存在但 API 请求失败时，按 HTTP 状态码精确说明：

| HTTP 状态 | 含义 | 输出说明 | 处理 |
|-----------|------|---------|------|
| 200 | 成功 | — | 正常解析 |
| 302 | 重定向（SSO/VPN 拦截） | `渠道 X：HTTP 302 重定向。Token 已保存，需 VPN/内网。` | 跳过，标注网络原因 |
| 401/403 | 认证失败 | `渠道 X：Token 无效或已过期。` | 跳过，提示重配 |
| 404 | 端点不存在 | `渠道 X：API 端点不存在。` | 跳过 |
| 429 | 限流 | `渠道 X：请求频率超限。` | 跳过 |
| 500+ | 服务端错误 | `渠道 X：服务端异常（HTTP {code}）。` | 跳过 |
| 超时 | 不可达 | `渠道 X：连接超时。` | 跳过 |
| 空响应 | 空 | `渠道 X：返回空响应。` | 跳过 |

> 不要让用户误以为 Token 无效。302 重定向是典型的企业内网 SSO 拦截。

## 缺失 Key 提示模板

搜索结束后统一提示（不阻塞搜索，同一会话只提示一次）：

```markdown
---
💡 **部分渠道因缺少 API Key 未能搜索，配置后可获得更多结果：**

| 渠道 | 获取地址 | 说明 |
|------|---------|------|
| SkillsMP | [skillsmp.com/docs/api](https://skillsmp.com/docs/api) | 格式 sk_live_skillsmp_xxx |

直接告诉我你的 Key，我会自动验证并持久化保存。
---
```
