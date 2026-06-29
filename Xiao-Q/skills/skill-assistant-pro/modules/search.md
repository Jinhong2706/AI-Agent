# 搜索模块

多源分类搜索 Skill：本地索引 → 平台型技能市场 + GitHub 优质仓库 → 通用搜索 → 去重比较推荐。

> 评分映射表/输出模板/渠道命令等**固定规则**已拆到 `references/` 按需加载，搜索时只需读本文件。
> 配置读取：只需读 sources.yaml 的 `preferences:` 段（~60 行）和 `settings:` 段（~10 行），无需加载全文。

> **源分类**（详见 [config/sources.yaml](../config/sources.yaml)）：
>
> | 类别 | 定位 | 代表 |
> |------|------|------|
> | **平台型技能市场** | 收录第三方来源的 Skill，提供独有质量信号 | skills.sh、SkillsMP、ClawHub、SkillHub |
> | **GitHub 优质仓库** | 高质量 Skill 源码或策展索引 | anthropics/skills、awesome-openclaw、awesome-claude-skills、obra/superpowers |
> | **通用搜索** | 兜底，覆盖所有 GitHub 公开仓库 | GitHub code search |

## 核心规则

- **环境快照优先**：Step 0.5 生成结构化环境快照（API Key / CLI 工具 / 网络可达性），后续所有渠道启用/跳过决策**只读快照**，严禁现场 `which xxx` 混串判断（详见 NEVER 规则）
- **全阶段执行**：不因前一阶段有结果就跳过后续，确保覆盖面
- **去重比较**：同一 GitHub 仓库出现在多个源时，合并展示并标注各源质量信号，给出比较建议
- **按来源分区输出**：平台型 / GitHub 仓库 / 通用搜索各自成区，无结果的分区用斜体标注
- **关键词三原则**：简单核心词优先、先粗后细、多意图必须拆分（详见 [references/search-templates.md](../references/search-templates.md)）
- **已安装标记**：搜索前扫描已安装目录 + 读取 `_skill_meta.json`，结果中已安装的标注 `✅ 已安装`
- **标签过滤**：用户输入含 `#tag` 格式时（如 `#azure #testing`），按标签匹配
- **名称验证**：搜索返回结果后，读取 description 验证与用户需求是否匹配，标注不过滤
- **静默执行**：搜索命令由 Agent 执行，不向用户展示原始命令
- 源优先级和启用状态读取 [config/sources.yaml](../config/sources.yaml) 的 `preferences:` 段，未配置时用内置默认值
- **用户偏好**：`search_strategy`、`dedup_strategy`、`prefer_channels` 优先于默认行为

---

## 第 0 步：扫描已安装 Skill + 语义索引

搜索前先获取已安装列表（覆盖项目级 + 全局级所有路径），用于后续标记、去重和已安装能力对比：

```bash
echo "=== project .cursor ===" && ls -1 .cursor/skills/ 2>/dev/null
echo "=== project .agents ===" && ls -1 .agents/skills/ 2>/dev/null
echo "=== global ~/.cursor ===" && ls -1 ~/.cursor/skills/ 2>/dev/null
echo "=== global ~/.agents ===" && ls -1 ~/.agents/skills/ 2>/dev/null
```

### 已安装 Skill 语义匹配

扫描到已安装 Skill 后，读取其 SKILL.md 的 `description` 和 `tags`，构建**语义匹配信号**用于 Step 5b 的「已安装 Skill 能力对比」：

```bash
for skill_dir in .cursor/skills/*/; do
  head -10 "$skill_dir/SKILL.md" 2>/dev/null
done
```

匹配方式采用**混合评分**（Hybrid Score）：

| 评分维度 | 权重 | 说明 |
|---------|------|------|
| **关键词匹配** (BM25) | 50% | 搜索关键词在已安装 Skill 的 description/tags 中的出现频率 |
| **语义相似度** | 50% | 搜索需求与已安装 Skill 描述的概念相似度（由 Agent 判断） |

**置信度分级**（替代二元匹配/不匹配）：

| 混合得分 | 置信度 | 处理 |
|---------|--------|------|
| ≥ 0.7 | **高** — 功能高度重叠 | 已安装 Skill 大概率可满足需求，在 Step 5b 中重点对比 |
| 0.4-0.7 | **中** — 部分相关 | 已安装 Skill 覆盖部分能力，在 Step 5b 中标注差异 |
| < 0.4 | **低** — 关联弱 | 跳过对比，不在输出中展示 |

> **设计理念**（来自 fitcheck-skill-search）：混合评分兼顾精确性和召回率——避免关键词匹配但语义不相关，也避免语义相关但关键词不同。

## 第 0.5 步：环境快照（API Key + 工具可用性）

搜索前生成一份**结构化环境快照**，统一采集 API Key、CLI 工具、网络可达性三类状态。**快照结果必须写入 `diagnostics.environment`（参见 [references/search-transparency.md#一诊断数据模型](../references/search-transparency.md#一诊断数据模型) 的 `environment` 字段），后续所有路径判断（gh 路是否启用、SkillsMP 是否跳过）都**必须**基于快照，不得二次调用 `which` / `gh auth status` 现场推断。

> ⚠️ **NEVER 现场判断工具可用性**：如 `which gh && gh auth status` 与其他 `echo` 混写在一行，shell 的退出码、stdout 顺序、权限前缀会让 Agent 读错；必须用结构化 Python 一次性输出 `key=value` 行再解析。

### 0.5.1 一次性快照脚本

**MUST** 在搜索前**以独立 Shell 调用**执行下面的脚本，不得与其他 echo / ls / curl 叠加。脚本保证每行输出 `KEY=VALUE` 严格格式，Agent 按行解析填入 `diagnostics.environment`：

```bash
python3 <<'PY' 2>/dev/null
import os, shutil, subprocess, yaml

out = {}

# ── 1. API Key 可用性（凭证文件 > sources.yaml auth.api_key > 环境变量）──
cred_file = os.path.expanduser('{SKILL_ASSISTANT_ROOT}/config/.credentials.yaml')
creds = {}
try:
    with open(cred_file) as f:
        creds = yaml.safe_load(f) or {}
except FileNotFoundError:
    pass

out['KEY_SKILLSMP'] = 'yes' if (creds.get('skillsmp', {}).get('api_key') or os.environ.get('SKILLSMP_API_KEY')) else 'no'

# ── 2. CLI 工具可用性（path 存在 + 子命令返回码）──
def has(cmd, args=None, timeout=3):
    path = shutil.which(cmd)
    if not path:
        return 'missing'
    if not args:
        return 'ok'
    try:
        r = subprocess.run([cmd] + args, capture_output=True, timeout=timeout)
        return 'ok' if r.returncode == 0 else 'unauth_or_err'
    except Exception:
        return 'error'

out['CLI_GH']        = has('gh', ['auth', 'status'])
out['CLI_SKILLHUB']  = has('skillhub', ['--version'])
out['CLI_NPX']       = has('npx', ['--version'])
out['CLI_NODE']      = has('node', ['--version'])

# ── CLI Provider 可用性（供 inspect 动态评测引擎 + diagnose 加速器使用）──
# 只探测"命令是否存在"，不做 -p 认证验证（耗时且认证验证在 D.0.4 引擎选择时实时探测）
# 已实测通过：codebuddy v2.94.0 / claude-internal v1.1.6
# 支持参数：-p / --system-prompt / --max-turns / --output-format text（三者接口 100% 同构）
out['CLI_CLAUDE']          = has('claude',          ['--version'])
out['CLI_CODEBUDDY']       = has('codebuddy',       ['--version'])
out['CLI_CLAUDE_INTERNAL'] = has('claude-internal', ['--version'])

for k, v in out.items():
    print(f'{k}={v}')
PY
```

### 0.5.2 快照结果路由表

Agent 解析输出后，**严格按此表**决定每个渠道的启用/跳过状态并写入 `diagnostics.channels[*].status`。**禁止**在 Step 2 现场重新判断。

| 快照字段 | 值 | 后续路径 |
|---|---|---|
| `KEY_SKILLSMP` | `no` | SkillsMP `skipped` + `skip_reason=missing_api_key` |
| `CLI_GH` | `missing` | 第 2/3 路（gh 仓库/全 GitHub）`skipped` + `skip_reason=gh_missing`，**强烈引导**安装 `brew install gh` |
| `CLI_GH` | `unauth_or_err` | 第 2/3 路 `skipped` + `skip_reason=gh_unauth`，引导 `gh auth login` |
| `CLI_GH` | `ok` | 第 2/3 路正常启用 |
| `CLI_SKILLHUB` | `missing` | SkillHub `skipped` + `skip_reason=skillhub_missing` |
| `CLI_NPX` + `CLI_NODE` | 任一 `missing` | skills.sh CLI 降级为 curl API（API 始终可用） |

### 0.5.3 Key 解析优先级（仅当快照命中 `KEY_*=no` 但用户临时提供时）

```
1. config/.credentials.yaml 凭证文件（持久化，跨会话生效，优先级最高）
2. sources.yaml 中的 auth.api_key 字段（兼容旧配置）
3. auth.env_var 指定的环境变量（会话级，进程结束即丢失）
4. 用户在当前对话中直接提供的 Key（临时，建议立即持久化）
```

**用户临时提供 Key 时**：立即写入 `config/.credentials.yaml` 持久化，禁止仅 `export`。

### 0.5.4 API 请求失败处理

按 HTTP 状态码精确说明（302=内网拦截非 Token 无效，401=认证失败）。详细状态码表见 [references/channel-search-commands.md#api-请求失败处理](../references/channel-search-commands.md#api-请求失败处理)。

**缺失 Key / 工具** — 不阻断搜索，跳过该渠道，搜索结束后统一在诊断头「ℹ️ 渠道跳过」区汇总提示（同一会话只提示一次）。提示模板见 [references/channel-search-commands.md#缺失-key-提示模板](../references/channel-search-commands.md#缺失-key-提示模板)。

## 第 1 步：理解需求

1. **领域**：React、测试、设计、部署、安全…
2. **具体任务**：写测试、生成 PPT、审查 PR…
3. **用途**：直接使用 or 参考学习
4. **标签**：用户提供 `#tag` 时优先按标签搜索

**精确名称信号**：用户说"这个 skill"、"叫 xxx 的"、提供了含连字符的名称 → 直接用名称搜索。

## 第 2 步：四级关键词 + 多路并行搜索

**核心策略**：通过四级关键词生成覆盖不同表达方式，每个搜索源发起宽路 + 多组窄路搜索，合并后通过漏斗式筛选输出精选结果。

### 2.1 四级关键词生成

详细规则见 [references/search-templates.md](../references/search-templates.md)，此处为执行摘要。

**生成流程**：

```
用户输入 → Level 1 语义核心提取（2-4 个概念词）
         → Level 2 主关键词组（2-3 组窄路，每组 2 词）
         → Level 3 宽路关键词（1 个最短核心词）
         → Level 4 扩展词（仅结果不足时触发）
```

| 层级 | 关键词规则 | 搜索量 | 目的 |
|------|-----------|--------|------|
| **Level 3 宽路** | 1 个最短核心词 | API limit=30 | 最大召回，撒大网 |
| **Level 2 组 A** | 精确匹配词组 | limit=10 | 命中高安装量结果 |
| **Level 2 组 B** | 近义替代词组 | limit=10 | 覆盖不同命名风格 |
| **Level 2 组 C** | 相关概念词组 | limit=5 | 捕捉意外好结果 |
| **Level 4 扩展** | 缩写/别名/工具名 | limit=5 | 仅 Level 2-3 总数 < 5 时触发 |

> **示例**：用户要"自动生成 PPT"
> - Level 1 核心：presentation + pptx + slides + generate
> - Level 2 组 A：`pptx presentation`（精确→命中 7,979 安装量头部 Skill）
> - Level 2 组 B：`presentation builder`（近义→命中 4,145 安装量 Skill）
> - Level 2 组 C：`markdown slides`（相关→命中专用 Skill）
> - Level 3 宽路：`presentation`（召回 30 条候选）
>
> **多意图场景**（用户要"查找、审查、创建 skill 的 skill"）：
> - 拆分为独立意图，每个意图各自生成四级关键词
> - **禁止合并为** `skill finder audit create` 这样的长查询

### 2.2 三路并行架构

所有搜索**同时发起**，不等前一个完成：

```
┌──────────────────── 并行执行 ─────────────────────┐
│                                                    │
│  ┌─ 第 1 路：多平台搜索 ───────────────────────┐  │
│  │  skills.sh / SkillHub / SkillsMP             │  │
│  │  ⚡ 各平台独立 CLI/API，无额外依赖           │  │
│  └──────────────────────────────────────────────┘  │
│                                                    │
│  ┌─ 第 2 路：优质仓库搜索 ─────────────────────┐  │
│  │  gh search code 跨仓库合并搜索               │  │
│  │  ⚡ 强依赖 gh CLI，无 gh 降级 WebSearch 兜底 │  │
│  └──────────────────────────────────────────────┘  │
│                                                    │
│  ┌─ 第 3 路：全 GitHub 搜索 ───────────────────┐  │
│  │  gh search code 全公开仓库                   │  │
│  │  ⚡ 强依赖 gh CLI，无 gh 降级 WebSearch 兜底 │  │
│  └──────────────────────────────────────────────┘  │
│                                                    │
└────────────────────────────────────────────────────┘
         │
         ▼
   合并 → 去重 → 相关度评分 → 质量归一化 → 输出 Top N
```

**gh CLI 是第 2、3 路的核心依赖**。状态**一律**读自 Step 0.5 的环境快照 `diagnostics.environment.CLI_GH`，**禁止**在本步骤再次调用 `which gh` 或 `gh auth status` 现场判断——混入其他 echo / ls 的输出会让 Agent 读错。

| `CLI_GH` 快照值 | 处理 |
|---------|------|
| `ok`（已安装 + 已认证） | ✅ 正常执行第 2、3 路 |
| `unauth_or_err`（已安装 + 未认证） | ⚠️ 提示 `gh auth login`，本次降级 WebSearch 兜底，写入 `anomalies[TOOL_UNAVAILABLE]`（同时满足 balanced 条件 D → 追加 `WEBSEARCH_FALLBACK_TRIGGERED`）|
| `missing`（未安装） | ⚠️ **强烈引导安装**（macOS: `brew install gh && gh auth login`），本次降级 WebSearch 兜底，写入 `anomalies[TOOL_UNAVAILABLE]`（同时满足 balanced 条件 D → 追加 `WEBSEARCH_FALLBACK_TRIGGERED`）|

### 2.3 平台型搜索（并行）

每个平台同时发起宽路和窄路搜索。各平台的命令模板、认证方式、响应字段见 [references/channel-search-commands.md](../references/channel-search-commands.md)。

> ⚠️ **MUST**：**每个已启用平台都必须同时执行宽路（Level 3）和窄路（Level 2）搜索**。只发窄路不发宽路是已知的搜索遗漏根因——窄路用复合关键词在部分平台可能全部返空，宽路是召回率的基础保障。

**执行摘要**：

| 平台 | 宽路（MUST） | 窄路 | 关键参数 | 无依赖时 |
|------|------|------|---------|---------|
| skills.sh | curl API, limit=30, 按 installs 排序 | CLI `npx skills find`, 5 条 | 无需认证 | curl 兜底 |
| SkillHub | `skillhub search`, 前 20 | `skillhub search`, 前 5 | 无需认证 | 跳过 |
| SkillsMP | REST API, limit=20, sortBy=stars | REST API, limit=5 | API Key | 跳过 |

### 2.3.1 双语平台关键词适配（MUST）

SkillHub 等中英双语平台收录大量中文 Skill。**纯英文复合关键词（如 `"skill search"`）可能漏掉以中文命名/描述的 Skill**，导致高质量中文 Skill 被遗漏。

**强制规则**：
1. **Level 1 语义核心提取时，必须同时保留中英文词**。用户输入「帮我找能搜索 skill 的 skill」→ 核心词应为 `skill, search, 搜索, 查找`
2. **Level 3 宽路对双语平台必须包含中文变体**。如用户输入含中文，英文宽路 `"skill"` 之外还应加中文宽路 `"搜索"` / `"推荐"` 等
3. **Level 2 窄路对双语平台生成中英文双组**。英文 `"skill search"` + 中文 `"skill 搜索"`

| 用户输入语言 | 英文平台（skills.sh/GitHub） | 双语平台（SkillHub） |
|-------------|---------------------------|-----------------|
| 纯英文 | 英文关键词 | 英文关键词 |
| 含中文 | 提取英文等价词 | **中英文双语关键词（MUST）** |
| 纯中文 | 翻译为英文 | **原始中文 + 英文翻译** |

### 2.4-2.5 GitHub 搜索（并行）

命令模板见 [references/channel-search-commands.md#github-优质仓库搜索](../references/channel-search-commands.md#github-优质仓库搜索)。

**执行摘要**：
- **第 2 路**：`gh search code` 跨 4 仓库 × 3 模板（核心词 SKILL.md / 精确词 SKILL.md / 核心词 README.md）
- **第 3 路**：`gh search code` 全公开 SKILL.md + `gh search repos` 高 Stars
- **gh 不可用**：降级为 WebSearch 兜底（balanced 条件 D 自动触发）
- **`anthropics/skills` 结果可直接信任**（🏢 官方）

> ⚠️ **`gh search repos` 第一轮硬约束（MUST）**：必须用 Level 3 单核心词，**禁止叠加 `--language` / `--stars` 过滤**——语言过滤会踢掉其他语言的大型项目（如 Go ⭐38K），stars 过滤会踢掉新锐高质量项目。过滤只能作为第二轮补充，且优先在结果集内 Agent 侧筛选。详见 [references/channel-search-commands.md#全-github-搜索](../references/channel-search-commands.md#全-github-搜索)。

### 2.6 搜索策略与覆盖规则

读取 `preferences.search_strategy`（用户在首次引导中选择），决定搜索范围和深度。将"全网搜索"语义正式拆分为两路：GitHub 全搜索（仍在 GitHub 仓库域）和 WebSearch 兜底（博客/社区等真正的网页）。

| 策略 | 平台 | 仓库 | 全 GitHub | **WebSearch 兜底** | 关键词 | Top N |
|------|------|------|-----------|:---:|--------|:---:|
| **speed** | skills.sh + SkillHub | gh 模板 A | 跳过 | ❌ 永不 | L3 + L2-A | 2 |
| **balanced**（默认） | 所有已启用 | gh 3 模板 | code + repos | ⚙️ 条件触发 | L2 全部 + L3 | 3 |
| **thorough** | 所有平台 | 全模板 + curl README | 含非 Skill 源 | ✅ 强制 2 条 | 全部 + L4 | 5 |

**balanced 下 WebSearch 兜底触发规则**（任一满足即自动补一路，不需用户确认）：
- **A** `funnel_summary.total_candidates < 20`（召回过低）
- **B** `channels[*].status == skipped` 数量 ≥ 2（覆盖受损）
- **C** Top N 最高混合相关度 < 3.0（置信度不足）
- **D** `environment.tools.CLI_GH ≠ ok` **且** `environment.keys.KEY_SKILLSMP == no`（核心工具缺失）

> speed 结果 < 5 时自动升级为 balanced；balanced 结果不足**优先触发 WebSearch 兜底**而非升级到 thorough；thorough 强制追加 2 条 WebSearch。

策略完整定义、4 条触发条件详情、WebSearch 调用约定、结果后处理规则见 [references/channel-search-commands.md#搜索策略完整定义](../references/channel-search-commands.md#搜索策略完整定义)。

### 2.6.1 WebSearch 兜底执行

WebSearch 是**第 4 路**搜索，区别于第 3 路的"全 GitHub 搜索"：前者用 Agent 的 `WebSearch` 工具检索真正的网页（博客 / Awesome List / 社区文章 / 社交媒体 / CSDN 掘金 / 微信公众号 / iwiki），后者仍局限于 GitHub 仓库域内。

**执行触发点**：漏斗 2（相关度筛）完成后检查触发条件，命中任一即插入 WebSearch 路径，结果走漏斗 3（质量归一化）。

**触发判定数据**（全部取自 `diagnostics`，无额外探测）：

| 条件 | 数据字段 | 模板选择 |
|---|---|---|
| A. 召回过低 | `funnel_summary.total_candidates < 20` | 模板 1 + 2 |
| B. 覆盖受损 | `channels[*].status == skipped` 数量 ≥ 2 | 模板 2 |
| C. 置信度不足 | Top N 最高 `confidence < 3.0` | 模板 1 + 3 |
| D. 核心工具缺失 | `environment.tools.CLI_GH ≠ ok` **且** `environment.keys.KEY_SKILLSMP == no` | 模板 1 + 4（中文输入时） |

**thorough 策略下**：上述条件不判断，**默认执行模板 1 + 2**，再按需追加 3 + 4。

**WebSearch 结果的三种处理路径**：

1. **抽取 GitHub 链接** → 去重后比对前 3 路结果，新仓库走漏斗 3 加入精选池，已见过的仅用于**多源加分**（推荐指数 +0.3）
2. **抽取平台 Skill 链接**（skills.sh / skillhub / clawhub）→ 反向查询对应平台 API 补齐元数据（若平台路径此前被跳过，此处能部分恢复）
3. **识别 Awesome List / 博客索引** → 不作为精选结果，而是作为第 4 分区「🌐 社区/博客（WebSearch 兜底·参考）」输出，标注 `⚠️ 非直接安装源，需 Agent 识别转化`

**诊断记录**：WebSearch 被触发时，必须向 `diagnostics.anomalies` 写入 `WEBSEARCH_FALLBACK_TRIGGERED`（ℹ️ 提示级）并记录触发原因（`reason` 字段），供诊断头展示归因；未触发时 `diagnostics.channels.websearch.status = "not_triggered"`，诊断头漏斗表显示 `—`。

**NEVER 规则**：
- NEVER 用 `gh search code` 或 `gh search repos` 冒充 WebSearch——它们的覆盖域是 GitHub 仓库，不是真正的网页
- NEVER 在 speed 策略下启用 WebSearch——用户选 speed 就是要快，触发会破坏策略承诺
- NEVER 悄悄兜底——触发后诊断头必须明确展示"因 [触发原因] 自动补充了 WebSearch 兜底，查询模板：[..]，新增候选 [N] 条"

### 2.7 漏斗式合并与筛选

所有平台和仓库的搜索结果通过三级漏斗筛选，从 100+ 条候选收敛到 5-10 条精选：

```
┌─ 搜索阶段（多搜）─────────────────────────────────────────┐
│  Level 3 宽路（各平台 limit=30）                           │
│  Level 2 窄路 A/B/C（各 limit=5-10）                      │
│  Level 4 扩展（仅不足时，limit=5）                         │
│  → 合计 100+ 条候选                                       │
└───────────────────────────────┬─────────────────────────────┘
                                │
┌─ 漏斗 1：去重合并 ────────────┼─────────────────────────────┐
│  同 owner/repo + skill_name → 合并为一条，保留所有源信号     │
│  同名不同 repo → 各自保留，标注差异                         │
│  → 去重后约 40-60 条                                       │
└───────────────────────────────┬─────────────────────────────┘
                                │
┌─ 漏斗 2：混合相关度评分 ──────┼─────────────────────────────┐
│  混合分 = 关键词命中(50%) + 语义匹配(50%)                  │
│  ≥4.5 🎯 精确匹配 | 3.0-4.4 ✅ 高相关                     │
│  1.5-2.9 ⚠️ 待确认 | <1.5 ❓ 弱相关                       │
│  → 按混合相关度排序，取 Top 15-20                          │
└───────────────────────────────┬─────────────────────────────┘
                                │
┌─ 漏斗 3：质量归一化 + 精选 ───┼─────────────────────────────┐
│  推荐指数 = 热度×0.4 + 权威×0.35 + 鲜度×0.25               │
│  多来源加分（2 源+0.3，3+ 源+0.5）                         │
│  → 按 相关度 + 推荐指数 排序，取 Top 3-5 / 每渠道          │
└───────────────────────────────┬─────────────────────────────┘
                                │
                    最终输出 5-10 条精选 + 跨源比较
```

**去重规则**：
- 同一 `owner/repo + skill_name` 来自多个平台 → 合并为一条，标注所有来源（多源交叉 = 质量加分）
- 同名不同 repo → 各自保留，标注差异

**相关度评分（混合增强）**：

```
混合相关度 = 关键词命中分 × 0.5 + 语义匹配分 × 0.5
```

| 维度 | 评分规则 | 分值 |
|------|---------|------|
| **关键词命中**（50%） | 多组窄路同时命中（A+B 或 A+C） | +3 |
| | 单组窄路命中 | +2 |
| | 宽路命中 + description 含关键词 | +1 |
| | 仅宽路命中 description 不含关键词 | +0 |
| **语义匹配**（50%） | description 与用户需求**语义高度一致** | +3 |
| | description 与用户需求**部分相关** | +1.5 |
| | description 与用户需求**语义不相关** | +0 |

> **语义匹配判断**：由 Agent 阅读 description，判断与用户需求的概念相似度。不依赖关键词是否出现——如搜"数据可视化"，description 说"chart generation and dashboard building"语义高度一致，应给 +3。

**置信度标记**：🎯 ≥4.5 精确匹配 | ✅ 3.0-4.4 高相关 | ⚠️ 1.5-2.9 待确认 | ❓ <1.5 弱相关

**最终输出**：按 `混合相关度 + 推荐指数` 综合排序，每渠道取 Top 3-5 条。

## 第 3 步：名称验证（标注不过滤）

合并结果后，对每个 Skill **读取 description**，确认功能与用户需求的匹配度：

- description 完全匹配 → 正常展示
- description 部分匹配或不确定 → **展示，但标注 `⚠️ 待确认`**
- description 与需求完全无关 → **展示在末尾，标注 `❓ 可能不匹配`**
- description 不可读取时 → 正常展示

> **核心原则：标注而不过滤** — Agent 可能误判，由用户自行判断。

## 第 4 步：深度抓取（按需）

从 Step 2 结果中选择 1-3 个高价值但信息不足的 Skill，用 `curl` 抓取 raw.githubusercontent.com 上的 SKILL.md 补充详情：

优先顺序：含 SKILL.md 的仓库 > 高 Stars 仓库 > awesome- 合集。

**Skill 判断标准**（满足任一即为 Skill）：
- 仓库包含 SKILL.md 文件
- 路径含 `.cursor/skills/`、`.claude/skills/`、`.agents/skills/` 等目录结构
- 在 skills.sh 索引中
- README 明确说明是 "Agent Skill"

不满足以上条件的归类为"相关开源项目"。

## 第 5 步：跨平台质量归一化评估

**推荐指数** = 热度 × 0.4 + 权威 × 0.35 + 鲜度 × 0.25（每维 0-5 分）

各平台的热度/权威/鲜度归一化映射表见 [references/scoring-rules.md](../references/scoring-rules.md)。

**速查**：🔥🔥🔥 ≥4.0 强烈推荐 | 🔥🔥 3.0-3.9 推荐 | 🔥 2.0-2.9 可用 | <2.0 仅展示
**多来源加分**：2 渠道 +0.3 / 3+ 渠道 +0.5
**同分排序**：官方 > 精选 > 社区 → 安装量高 → 更新近

## 第 5b 步：去重与跨源比较

### 去重规则

当多个源返回同一 Skill 时，需合并去重：

**同源判定**（满足任一即为同一 Skill）：
- `source.repo` + `source.path` 完全相同
- skills.sh 的 `id` 格式为 `{owner}/{repo}@{skillId}`，与 GitHub 搜索结果的 `repo + path` 可直接匹配

**去重策略**：
1. 合并为一条，标注所有发现该 Skill 的渠道
2. 各渠道的质量信号全部保留展示
3. 按 `dedup_strategy.prefer_channels` 决定主展示渠道

### 跨源比较

功能相似但来源不同的 Skill，自动进行比较（模板见 [references/output-templates.md#跨源比较表](../references/output-templates.md#跨源比较表)）。

**相似判定**：同名不同仓库 / 描述高度相似（>70%）/ 同领域替代方案。
> 跨源比较表只做客观陈述，不给建议。建议统一在推荐方案中给出。

### 已安装 Skill 的 `_skill_meta.json` 检查

搜索结果中如果某个 Skill 已安装且有 `_skill_meta.json`：读取 `commitHash` → 与远程比对 → 有新版标注 `🔄 有更新`。

### 已安装 Skill 的能力对比与决策

Step 0 扫描到的已安装 Skill 中，如果有与搜索需求**功能重叠**的，必须对比并给出决策建议。对比表模板见 [references/output-templates.md#已安装-skill-对比表](../references/output-templates.md#已安装-skill-对比表)。

**决策逻辑**：

| 已安装 vs 搜索结果 | 推荐决策 |
|-------------------|---------|
| 已安装能力 ⊃ 搜索结果 | **无需安装**，提示已有更完整的本地方案 |
| 已安装能力 ≈ 搜索结果 | **吸收融合**，只取搜索结果的独有特性 |
| 已安装能力 ⊂ 搜索结果 | **替换**，搜索结果全面优于本地 |
| 功能正交 | **并行安装**，各司其职 |
| 本地无相关 | 跳过对比 |

> **原则**：不要忽视用户已安装的 Skill。如果已安装 Skill 已满足需求，应明确告知。

## 第 6 步：输出结果

输出模板见 [references/output-templates.md](../references/output-templates.md)。诊断头数据模型、异常检测规则、diff 展示详见 [references/search-transparency.md](../references/search-transparency.md)。

### 6.1 诊断数据收集（MUST — 贯穿 Step 1-5）

搜索过程中必须维护结构化的 `diagnostics` 对象，记录关键词生成、渠道候选、漏斗收敛、每条结果的命中归因。数据模型见 [references/search-transparency.md#一诊断数据模型](../references/search-transparency.md#一诊断数据模型)。

**数据收集时机**（每一步都要填）：

| 阶段 | 写入字段 |
|---|---|
| **Step 0.5 环境快照** | **`environment.{keys,tools,network,summary}`（整搜索只写一次）** |
| Step 1 理解需求 | `user_input` / `user_language` |
| Step 2.1 关键词生成 | `keywords.*`（所有层级 + 中文变体） |
| Step 2.3-2.5 渠道搜索 | 每渠道 `candidates` + 每条 result 的 `hits[]` |
| **Step 2.6.1 WebSearch 兜底** | **`channels.websearch.{status,trigger_reason,templates_used,candidates,top_n}`**（thorough 必填 / balanced 触发时填 / speed 恒为 `not_triggered`） |
| Step 5 漏斗 1 去重 | 每渠道 `after_dedup` |
| Step 5 漏斗 2 相关度筛 | 每渠道 `after_relevance` |
| Step 5 漏斗 3 精选 | 每渠道 `top_n` + `funnel_summary` |
| Step 6 输出前 | 运行异常规则，填 `anomalies[]`（含 `TOOL_UNAVAILABLE` / `CHANNEL_UNREACHABLE` / `RUNTIME_RECHECK_DETECTED` / `WEBSEARCH_FALLBACK_TRIGGERED` / `LAYOUT_NON_TABLE` / `DIAGNOSTICS_MISSING`） |

**性能要求**：数据收集**不得**增加额外 API 调用——全部从 Step 2-5 的中间态复用。

### 6.2 异常检测（MUST — Step 6 输出前执行）

基于 `diagnostics` 数据运行 11 条异常规则（详见 [search-transparency.md#三异常检测规则](../references/search-transparency.md#三异常检测规则)），按严重等级分类：

| 等级 | 典型规则 | 处理 |
|---|---|---|
| 🚨 阻断 | `COMPOUND_QUERY_IN_GH_REPOS` / `RUNTIME_RECHECK_DETECTED` / **`LAYOUT_NON_TABLE`** / **`DIAGNOSTICS_MISSING`**（违反 NEVER / 透明度硬约束）| 展示在诊断头顶部，**Agent 必须先重写输出再交付用户**，不得绕过 |
| ⚠️ 警告 | `L2X_EMPTY` / `LOW_TOP_CONFIDENCE` / `CHANNEL_THIN` / `TOOL_UNAVAILABLE` / `CHANNEL_UNREACHABLE` | 展示在「注意事项」区 + 指向对应 refine 菜单 |
| ℹ️ 提示 | `STRATEGY_UPGRADE_RECOMMENDED` / `CHANNEL_SKIPPED` / `MISSING_CN_VARIANTS` / `WEBSEARCH_FALLBACK_TRIGGERED` | 小字体提示 |

### 6.3 输出结构

**必须包含**：

1. **🔍 搜索诊断头**（输出第一部分）
   - 完整版：balanced / thorough 策略 + 任意异常
   - 精简版：speed 策略且无异常
   - Refine 版：菜单 7-11 触发的二次搜索（含 diff）
2. **按来源分区展示**（每区 Top 3，编号全局连续）
   - ⚠️ 必须包含**「命中」列**，标注每条结果命中的关键词层级
3. **跨源比较表**（如有相似 Skill）
4. **已安装对比**（如有功能重叠）
5. **推荐方案**（精简/完整/增强/融合四档，含具体编号和理由）
6. **提案式交互菜单**（1-6 原有 + 7-11 refine 分支）

### 6.3.1 展示形式硬约束（MUST）

**所有结构化信息必须用 markdown 表格输出**，不得用列表 / 卡片 / 段落文字替代：

| 输出段 | 必须形式 | 不允许的形式 |
|---|---|---|
| 🔍 诊断头 · 关键词表 | markdown 表格（层级/关键词/命中数/状态 四列） | 列表、散文"我使用了 xxx 作为关键词" |
| 🔍 诊断头 · 渠道漏斗表 | markdown 表格（渠道/候选/去重/相关度筛/Top N/备注 六列） | 列表、百分比文字描述 |
| 🔍 诊断头 · 环境快照 | markdown 表格（类别/项/状态/备注） | `KEY=VALUE` 文本块、YAML 原文 |
| 🔍 诊断头 · 注意事项 | 有序列表（每条含 `→ 菜单 X` 指引） | 自由段落 |
| 📦 来源分区 · Top N | markdown 表格（#/Skill/命中/热度/推荐指数/说明） | ~~bullet 列表~~、~~每条一个标题~~、~~段落描述~~ |
| 🔗 非 Skill 分区 | markdown 表格（#/项目/命中/Stars/说明） | 列表 |
| 🌐 WebSearch 兜底分区 | markdown 表格（潜在仓库表 + 索引类表） | 列表 |
| 🔄 跨源比较 | markdown 表格（维度 × 候选矩阵） | 对比段落 |
| 💡 推荐方案 | 四档各一块，每档**说明段 + 表格**（编号/项目/作用） | 纯散文推荐 |
| 🎯 交互菜单 | 有序列表（编号 + 简述，允许） | — |

**允许的非表格**：段落式说明文字（每段 ≤ 3 行，位于表格**之前或之后**用于解释）、有序列表（仅限「注意事项」和「交互菜单」）、单行引用块（`>` 开头的提示）。

**NEVER 规则**：
- **NEVER 用列表/卡片/段落替代 Top N 表格**——即便结果只有 1 条，也必须输出 1 行表格（不得写成"只找到 X 一个结果，下面介绍一下：..."）
- **NEVER 把诊断头写成散文式**——诊断头是**机器可读的数据仪表盘**，自由文字会破坏透明度主线
- **NEVER 把多个分区合并为一张大表**——每个来源（skills.sh / SkillHub / GitHub / SkillsMP / WebSearch 兜底）独立成一张表，跨分区编号连续但结构各自分开
- **NEVER 省略表头**——即使只有 1 行数据也必须写完整表头

### 6.3.2 输出前校验清单（MUST）

Agent 输出前**必须**逐项 self-check，任意项失败都要回退重写：

| # | 校验项 | 失败 → 触发异常规则 |
|:-:|---|---|
| 1 | 每来源 Top 0-3，编号跨分区连续 | — |
| 2 | 每条含：说明 + 超链接 + 热度 + 推荐指数 + 「命中」 | — |
| 3 | 已去重 + 已安装标注 `✅ 已安装` + 名称验证标注 | — |
| 4 | **诊断头存在且完整**（关键词 / 渠道漏斗 / 环境快照 / 异常清单都有数据） | `DIAGNOSTICS_MISSING` |
| 5 | 每条结果的「命中」列非空（仅 L3 命中必须标 `⚠️ L3 only`） | — |
| 6 | **诊断头的关键词表、渠道漏斗表、环境快照均为 markdown 表格结构** | `LAYOUT_NON_TABLE`（🚨 阻断） |
| 7 | **每个来源分区为 markdown 表格**（有表头 + 分隔行 + 至少 1 行数据或"_暂无结果_"斜体占位） | `LAYOUT_NON_TABLE`（🚨 阻断） |
| 8 | 跨源比较、已安装对比、推荐方案各档均为 markdown 表格 | `LAYOUT_NON_TABLE`（🚨 阻断） |
| 9 | WebSearch 兜底分区（如触发）使用表格展示潜在仓库 + 索引类两个子表 | `LAYOUT_NON_TABLE`（🚨 阻断） |

**简单自检正则**（Agent 心算即可，无需脚本）：输出中每出现一个 `## 📦 来自` / `## ✅ 来自` / `## 🌐 来自`，其下 3 行内**必须**出现形如 `| # | ` 的表头行——否则触发 `LAYOUT_NON_TABLE`。

### 6.4 透明度原则

| 原则 | 反例 | 正例 |
|---|---|---|
| **关键词可见** | 只在诊断头隐含"搜索了 resume" | 明确列出 L3 宽路/L2-A/B/C/中文变体各是什么 |
| **数量可验证** | 只说"找到 12 条" | 展示 113→96→44→12 的漏斗收敛 |
| **命中可归因** | 仅给 🎯/✅/⚠️/❓ 置信度图标 | 标注命中的具体层级，如 `L3 + L2-A` |
| **异常可操作** | 只说"结果偏少" | 「skills.sh 候选仅 8 条 → 菜单 8 深搜」 |
| **违规自曝** | 悄悄用复合查询 | 违反 NEVER 时在诊断头顶部标 🚨 阻断级警告 |

> ⚠️ **NEVER 隐藏搜索参数**：诊断头必须展示 Agent 实际使用的关键词和 API 参数。用户不认可搜索结果时，这是定位偏差的唯一依据。

如果用户是为了**参考学习**，额外说明结构亮点和值得借鉴的写法。

---

## 第 7 步：Refine 循环

用户通过诊断头底部的交互菜单 7-11 发起 refine 时执行。完整规则见 [references/refine-search.md](../references/refine-search.md)。

### 7.1 Refine 分支速查

| 菜单 | 动作 | 保留 | 重新执行 |
|:-:|---|---|---|
| 7 | 修改关键词（L2-A 改 X / L3 改 Y） | 其他层级 + 其他渠道 | 全渠道重搜 |
| 8 | 深搜某渠道（skills.sh 深搜 limit=50） | 其他渠道结果 | 仅该渠道 |
| 9 | 升级策略（balanced → thorough） | 用户输入 | 完整重搜 |
| 10 | 补充关键词（加 L2-D / 加中文变体） | 所有原关键词 + 结果 | 只搜新词并合并 |
| 11 | 排除关键词（排除 template）| 所有候选 | 客户端过滤，不发 API |

### 7.2 Refine 状态管理

- **计数器**：`diagnostics.refine_count`，每次递增
- **上限**：单次会话同一搜索最多 5 次 refine，超限提示用户完全重搜
- **历史**：保留最近 3 次的 `previous_diagnostics`，支持 `/search rollback`
- **输出**：每次 refine 必须用诊断头 diff 版，展示"调整带来了什么变化"

### 7.3 Refine 与 NEVER 规则

Refine 过程中所有 NEVER 规则仍然生效（单核心词 / 宽路不可省 / 中文双语等）。用户指令与 NEVER 冲突时必须提示确认，不得悄悄违规。

### 7.4 收敛提示

连续 3 次 refine 仍未命中高相关度（Top 最高 < 3.0）时，提示用户考虑：
1. 使用菜单 6 完全重搜（思路完全更换）
2. 路由到 [modules/create.md](create.md) 自建 Skill

避免在错误方向上无限深钻。

---

## 相似 Skill 搜索

用户请求"相似 skill"或选择"搜索相似"时：

1. 读取目标 Skill 的 `description` 和 `tags`
2. 提取核心能力词作为新关键词
3. 重新执行第 2-5 步搜索（含诊断数据收集）
4. 输出时标注"相似度"（功能重叠/互补/替代）

---

## 搜索无结果时

全部渠道均无相关 Skill 时：

1. 自动切换到**智能推荐**模块（见 [modules/recommend.md](recommend.md)）
2. 引导用户创建 Skill（路由到 [modules/create.md](create.md)）：
   ```
   未找到 "{关键词}" 相关的 Skill。
   如果这是你经常做的工作，我可以帮你创建一个：
   → 输入"帮我创建一个 {关键词} skill"
   → 或手动执行 npx skills init my-{关键词}-skill
   ```
3. 建议浏览 https://skills.sh 或 awesome-openclaw-skills 合集手动查找
