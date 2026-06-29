# Description 量化加速器

> 融合自 [skill-creator](https://github.com/anthropics/skills/tree/main/skills/skill-creator) 的 `run_loop.py` / `improve_description.py` / `run_eval.py`，重写为 skill-assistant 的双路径实现
>
> **解决什么问题**：darwin 风格的"输出质量"评测能告诉你"触发后好不好"，但回答不了"会不会被触发"。description 触发率（trigger rate）必须用独立测试集量化——这正是 skill-creator 的强项。
>
> **触发时机**：仅在 diagnose 棘轮迭代发现"P1 短板锁定为 description"，且用户选择 `[加速器]` 路径时执行。**默认走传统手工改写路径**，加速器作为可选高级路径。
>
>
> 1. **路径定位重新表述**——路径 A 不再是"主路径"，而是**兼容兜底**；路径 B 不再是"性能优化"，而是**保真路径**。两条路径回答的不是同一个问题：路径 A 给 *approximate trigger rate*，路径 B 给 *true trigger rate*（详见 §保真度差异）
> 2. **CLI 失败自动降级**——路径 B 启动失败时**自动降级到路径 A**（绝不静默），降级原因 + 保真度损失必须明示用户，`optimizer_path` 列同步追加 `→fallback:subagent_sim` 标记

---

## 核心设计

### 双测试集分工

| 测试集 | 测什么 | 谁评 | 文件 |
|---|---|---|---|
| **`test-prompts.json`**（已有） | 触发后输出质量 | 子 Agent baseline vs with-skill 双跑 | `{skill_dir}/test-prompts.json` |
| **`trigger-queries.json`** | 会不会被触发（trigger rate） | 子 Agent 模拟 router 决策 | `{skill_dir}/trigger-queries.json` |

> **两份测试集都是可选的**——只有要做 description 量化优化时才必须有 `trigger-queries.json`。

### 双路径执行

| 路径 | 何时使用 | 依赖 | 执行方式 |
|---|---|---|---|
| **路径 A：本地子 Agent 模拟**（兼容兜底） | 任何 IDE / 任何环境 | 无外部 CLI | spawn 子 Agent N 次，每次只投喂 description + query，问"会不会激活这个 Skill" |
| **路径 B：claude-compatible CLI 新进程**（保真路径） | 已装任一兼容 CLI 且认证可用 | 见下方 Provider 表 | 由 Provider 命令以 `-p / --output-format stream-json --include-partial-messages` 启**全新进程**，重新走真实 router 决策链 |

### 保真度差异

> **注意**：**两条路径回答的不是同一个问题**。

| 维度 | 路径 A（同进程子 Agent） | 路径 B（新进程 CLI） |
|---|---|---|
| **进程隔离** | ❌ 子 Agent 在主 Agent 上下文内，已有 SKILL.md 全文等其他信息 | ✅ 全新进程，context 完全重置 |
| **router 路径保真** | ⚠️ "提示词模拟"——再怎么说"只看 description"，模型仍可能"偷看" | ✅ 真实 Claude/Provider router 决策链；激活信号来自真实 `tool_use` 事件流 |
| **测什么** | "假设一个看过 description 的模型，会不会觉得这个 query 应该用这个 skill" | "在生产环境真实 router 路径上，这个 description 会不会触发激活" |
| **结论性质** | **approximate trigger rate**（近似触发率，看趋势） | **true trigger rate**（真实触发率，可作为 stakeholder 报告基准） |
| **跨 Provider 比较** | ⚠️ 不可比（不同子 Agent 模型阈值不同 + 同进程偏差不同） | ✅ 同 Provider 内可比；同次 diagnose 内不混用 Provider 时跨棘轮迭代有效 |
| **依赖** | 任何 IDE 内置子 Agent 机制即可 | 需安装并认证 CLI Provider |
| **典型用途** | 快速看趋势、回归检查、零依赖环境 | 给 stakeholder 报"真实触发率"、performance baseline、跨棘轮严格比较 |

> **理论依据**：trigger rate 测的是"router 决策"，而 router 决策**只能通过外部进程"重新进入 Provider 路由"才能保真**。子 Agent 在主 Agent 上下文里跑，会把 SKILL.md 整个上下文都看到，反而失真。这一洞察来自分析 [skill-creator](https://github.com/anthropics/skills/tree/main/skills/skill-creator) 的 `run_eval.py`：它**只在** trigger 评测一处用 `claude -p`（其他流程都靠 subagent），CLI 在那里不是性能优化，是保真度的硬性需求。

### 决策树（取代旧版"决策原则"）

```
问：你想得到什么？
├─ 想看 description 改写后的"趋势"，能升不能降即可
│  └─→ 路径 A（子 Agent 模拟）就够了
│
├─ 想给团队/上级报告"真实触发率 x%"，需要可信数字
│  └─→ 必须走路径 B（CLI 新进程）
│
├─ 棘轮迭代里要严格比较"新 desc 比旧 desc 触发率高 X 个百分点"
│  └─→ 路径 B 可比性强；路径 A 同进程偏差不稳定，建议谨慎解读绝对值差
│
└─ 没装 CLI / 装了但启动失败 / Node 版本不够
   └─→ 路径 A 兜底（明示用户保真度损失，见 §CLI 失败降级规则）
```

### CLI 失败降级规则

> **核心原则**：路径 B 失败时按固定优先级链自动尝试下一个 Provider，全链失败才退回路径 A（子 Agent），全程**绝不静默**。

#### 降级优先级链

```
用户选择的 Provider（已失败）
    ↓ 失败（命令不存在 / 启动崩溃 / 认证失败 / 超时 / 网络不可达）
codebuddy（通用）
    ↓ 失败
claude-internal（需 IOA 登录）
    ↓ 失败
路径 A · 子 Agent 模拟（approximate trigger rate，兜底）
```

**跳过规则**：若用户已选择链中某一级，降级时从其**下一级**开始尝试（不重复）：
- 用户选 `codebuddy` 失败 → 跳过 codebuddy，直接试 `claude-internal` → 子 Agent
- 用户选 `claude-internal` 失败 → 跳过前两级，直接进子 Agent
- 用户选 `claude` 失败 → 从 `codebuddy` 开始完整链

**Node 版本不足例外**：`codebuddy` 启动报 `requires Node.js v18.20.8 or newer` 时**中断整个降级链**，让用户主动决策升级 Node（避免静默掩盖环境问题）；可改选 `claude-internal` 或 `claude` 继续。

| 失败场景 | 检测信号 | 降级动作 | 必须告知用户 |
|---|---|---|---|
| Provider 命令不存在 | `which {cmd}` 返回非零 | 按链尝试下一个 | 「⚠️ `{cmd}` 未安装，尝试 `{next}`...」|
| Provider 启动崩溃 | `returncode != 0` 或 `FileNotFoundError` | 按链尝试下一个 | 「⚠️ `{cmd}` 启动失败：{stderr 首行}，尝试 `{next}`...」|
| Provider 认证失败 | `-p "ping"` 返回 401/403/未授权 | 按链尝试下一个，同时给出 login 命令供用户修复 | 「⚠️ `{cmd}` 未认证（可跑 `{login_cmd}` 修复），尝试 `{next}`...」|
| Provider subprocess 超时 | 单条 query > 5 分钟无响应 | 终止进程，按链尝试下一个 | 「⚠️ `{cmd}` 超时，尝试 `{next}`...」|
| Provider 网络不可达 | 连续 3 次网络层错误 | 同上 | 同上 |
| Provider Node 版本不足 | stderr 含 `requires Node.js v` | **中断整个链**，提示升级或换 Provider | 「❌ `{cmd}` 要求 Node ≥ {min_ver}，当前 {cur_ver}；升级：`nvm install 20`，或改选 `claude-internal` / `claude`」|
| 全链失败 | 所有 CLI Provider 均失败 | 退回路径 A 子 Agent | 「⚠️ 所有 CLI Provider 均不可用，已降级路径 A（approximate trigger rate）」|

> **关键规则**：
> - **降级自动执行**，不需要用户重新确认（避免棘轮迭代被频繁打断）
> - **首次降级每级都显式告知**（长版）；同级重复降级压缩为单行 status
> - **进入路径 A 时必须**出现 "approximate trigger rate" 字样
> - **`results.tsv` 同步打标**：`optimizer_path` 记录完整降级路径，如 `cli:claude→cli:codebuddy→fallback:subagent_sim`

### 路径 B 已验证的 Provider

| Provider | 适用场景 | 安装 | 命令名 | 认证 | 底层模型 | Node 要求 | 接口同构度 | 实测状态 |
|---|---|---|---|---|---|---|---|---|
| `codebuddy` | **通用**（推荐首选）| `npm i -g @tencent-ai/codebuddy-code`（[文档](https://www.codebuddy.ai/docs/zh/cli/installation)） | `codebuddy`（别名 `cbc`） | 企业微信 OAuth（首次启动引导）| GPT-5 / 接入模型 | **≥ 18.20.8** | **100%** | ✅ v2.94.0 实测：`-p / --system-prompt / --max-turns / --output-format text` 均通 |
| `claude-internal` | **需 IOA 登录**（已有内部权限）| 内部分发渠道（[iWiki](https://iwiki.woa.com/p/4015845000)） | `claude-internal` | IOA / `CODEBUDDY_API_KEY`（**仅 `-p` 模式**）| **Claude 4.6 Opus**（默认）/ **Claude 4.7 Opus**（`/model claude-opus-4-7`）| 实测 v20.19.6 | **100%** | ✅ v1.1.6 实测均通；⚠️ `-p` 模式有 3s stdin 等待，追加 `< /dev/null` 可消除 |
| `claude` | **Anthropic，海外账号** | `npm i -g @anthropic-ai/claude-code` | `claude` | `claude login` 或 `ANTHROPIC_API_KEY` | Claude Sonnet/Opus | 18+ | 基准 | 基准 |

> **同构度 100% 的含义**：所有 Provider 的 `-p` / `--print` / `--output-format` / `--input-format` / `--max-turns` / `-c` / `-r` / `--system-prompt` / `--append-system-prompt` / `--agents` / `--allowedTools` / `--disallowedTools` 参数全部同名同义。**只需把命令名换掉，其他参数原样保留即可**——加速器调用层不需要 if-else 分支。
>
> 未来新增的 claude-compatible CLI（如 OpenCode、Cursor CLI 的 `cursor-agent -p` 等）只要满足"`-p "query"` 输出文本响应"即可作为 Provider，**不需要改 skill-assistant 代码**。

#### Provider 选择建议

| 你的情况 | 推荐 Provider | 理由 |
|---|---|---|
| 通用（默认首选）| **`codebuddy`** | 无需特殊账号，企业微信 OAuth 即可；v2.94.0 实测通过 |
| 已有 IOA 登录权限 | **`claude-internal`** | 底层 Claude 4.6/4.7 Opus，接口同构 100%；v1.1.6 实测通过 |
| Anthropic 海外账号 | `claude` | 直连 Anthropic 原版，配额自管 |
| 跨棘轮严格比较 | 同次 diagnose 内**只用一个**（不同模型阈值不同）| — |
| 想"对照"看共识 | 各跑一次，**单独**记录，不在同一棘轮内混用 | — |

#### claude-internal 合规要点

- ⚠️ `claude-internal --help` 警示：「未经平台方许可，私自逆向调用平台方的模型 API，将被视为不瑞雪行为」——使用范围以 `-p` 等标准接口为限，**绝不**尝试逆向 API 协议
- 当月配额耗尽时**会自动切换为内部模型**（非 Claude 模型）——若加速器跑到中途切换，**触发率绝对值不可与之前数据严格对比**（已由"同次不混 Provider"NEVER 覆盖，但因模型可能在同 Provider 内静默切换，建议监控 `claude-internal` 输出中的模型字段）
- `CODEBUDDY_API_KEY` 模式仅支持 `-p`——这正好是我们加速器需要的模式，没影响

---

## trigger-queries.json 文件 schema

```json
[
  {
    "id": 1,
    "scenario": "should_trigger",
    "query": "帮我把这个 PDF 文件每页都转成竖屏的",
    "expected": true,
    "note": "明确触发场景：用户提到核心动作"
  },
  {
    "id": 2,
    "scenario": "should_trigger",
    "query": "把 report.pdf 横过来",
    "expected": true,
    "note": "短句 + 缩写（横过来 = 旋转）"
  },
  {
    "id": 3,
    "scenario": "should_not_trigger",
    "query": "我想压缩一下这个 PDF",
    "expected": false,
    "note": "反例：相似领域但不同动作（压缩 ≠ 旋转）"
  },
  {
    "id": 4,
    "scenario": "ambiguous",
    "query": "PDF 显示有点问题",
    "expected": null,
    "note": "歧义场景：可触发可不触发，单次结果不计分，看 3 次重复的方差"
  }
]
```

**字段说明**：
- `expected: true` → 应该触发，trigger rate 越高越好
- `expected: false` → 不应该触发，trigger rate 越低越好（false positive 越少越好）
- `expected: null` → 歧义，仅记录方差，不计入触发率

**数量建议**：每类 4-6 条，total ≤ 20，能覆盖核心 + 边界 + 反例即可，避免过度工程。

---

## 路径 A：本地子 Agent 模拟（默认）

### 执行步骤

```
1. 读取 trigger-queries.json
2. 60/40 split（防止 description 改写过拟合）：
   - train_set: 前 60% 用于优化反馈
   - test_set: 后 40% 用于"未见过的查询"评估
3. 对每条 query，spawn 独立子 Agent N=3 次（重复以降方差）：
   投喂 prompt：
   ─────────────────────────────────────
   你是一个 Skill 路由器。下面是一个候选 Skill 的 description：

   {当前 description}

   用户输入："{query}"

   仅基于 description 判断：是否应该激活这个 Skill 来响应？
   回答只输出一个 token：YES 或 NO。
   ─────────────────────────────────────
4. 统计 trigger rate：
   - 对 expected=true 的 query：YES 率 = recall
   - 对 expected=false 的 query：NO 率 = precision
   - 综合分 = (recall + precision) / 2
5. 主 Agent 收集 train_set 上的失败案例，提出新 description（必须 ≤ 1024 字符）
6. 用新 description 在 train + test 上重新跑（步骤 3-4）
7. 棘轮决策：test_set 综合分 > 旧 test_set 综合分 → keep；否则 revert
8. 最多迭代 5 轮，或连续 2 轮无改进则 break
```

### 关键约束

- **1024 字符硬上限**：description frontmatter 字段在 Skill router 中会被截断，超过 1024 字符的部分不参与匹配。每轮新 description 生成后**必须**先做长度检查；超长则返回到 step 5 重写"在 1024 字符内的精简版"。
- **以 test_set 为最终评估**：避免 description 过拟合 train_set 的措辞。
- **每轮只改 description**：不要顺手改 SKILL.md body，保证短板归因清晰。
- **方差控制**：每条 query 跑 3 次取均值；单次结果不可信。

### 子 Agent 调用示例

```
spawn 子 Agent，subagent_type=generalPurpose（或 IDE 等价机制），prompt 为：
─────
你扮演 Skill 路由器。判断下面用户查询是否应该激活给定的 Skill。

【候选 Skill description】
{current_description}

【用户查询】
{query}

【判断规则】
1. 仅基于 description 判断，不要假设你知道 Skill 内部细节
2. 看 description 是否描述了能解决该查询的能力
3. 若描述模糊或不直接相关，回答 NO

【输出格式】
仅输出一行：YES 或 NO

不要输出任何其他内容（包括解释、推理过程、标点）。
─────
```

> **NEVER**：不要把 SKILL.md body 也投给子 Agent——真实 router 决策只基于 description，body 信息会让评测虚高。

---

## 路径 B：Claude-compatible CLI 加速（可插拔 Provider）

### Provider 配置

在 diagnose 启动加速器路径 B 时，由用户从 §路径 B 已验证的 Provider 表中**显式选择**（或环境快照自动检测优先级）。配置以**运行时变量**形式传给执行脚本，**不持久化、不写明文凭据**。

| 变量 | 含义 | 示例 |
|---|---|---|
| `CLI_PROVIDER_CMD` | Provider 命令名（必填） | `claude` / `codebuddy` |
| `CLI_PROVIDER_AUTH_HINT` | 给用户看的认证提示 | `claude login` / `codebuddy login`（仅展示，不替用户跑） |
| `CLI_PROVIDER_MODEL` | 指定模型（可选） | `--model sonnet` / `--model gpt-5` |
| `CLI_PROVIDER_EXTRA_ARGS` | Provider 特有参数（可选） | `-y`（codebuddy 在 `-p` 模式下涉及读写时通常需要） |

> 选择来源优先级：用户显式指定 > 环境快照检测到的可用 CLI > 默认 `claude`（若可用）。

### 前置条件示例

**Provider = claude**（基准）：

```bash
npm install -g @anthropic-ai/claude-code

claude login                              # OAuth，复用 Pro/Max 订阅
# 或
export ANTHROPIC_API_KEY=sk-ant-...       # API key 计费
```

**Provider = codebuddy**：

```bash
# 1. Node ≥ 18.20.8（codebuddy 启动会强制校验，低于此版本直接拒绝）
node --version

# 2. 安装
npm install -g @tencent-ai/codebuddy-code

# 3. 认证（首次 codebuddy 启动会引导）
codebuddy   # 进交互模式完成首次登录后即可在 -p 模式复用 session
```

环境快照中相关字段：`CLI_CLAUDE` / `CLI_CODEBUDDY`（皆 `which <cmd>` 探测，记录可用性，不记录凭据）。

### 执行方式（Provider 无关的统一调用形态）

skill-creator 上游的 `run_loop.py` 内部 `subprocess.run(["claude", "-p", ...])` 必须先做命令名注入。skill-assistant 的执行包装如下（伪代码）：

```python
def run_optimizer_via_cli(provider_cmd: str, queries_path: str,
                           skill_dir: str, max_iterations: int = 5,
                           extra_args: list[str] | None = None) -> dict:
    """以可插拔 Provider 调用 description 优化循环。

    provider_cmd: 'claude' 或 'codebuddy' 或任意 claude-compatible CLI
    extra_args:   provider 特有附加参数（如 codebuddy 的 ['-y']）
    """
    base_args = [provider_cmd, "-p", "--output-format", "json", "--max-turns", "8"]
    if extra_args:
        base_args.extend(extra_args)

    # 1. 准备 prompt（注入 SKILL.md + trigger-queries.json + 评分规则）
    prompt = render_optimizer_prompt(skill_dir, queries_path, max_iterations)

    # 2. 调 Provider
    # 降级链：codebuddy → claude-internal → subagent_sim（跳过已失败的 provider）
    FALLBACK_CHAIN = ["codebuddy", "claude-internal"]  # 子 Agent 为最终兜底，不在链中

    try:
        proc = subprocess.run(base_args, input=prompt, capture_output=True, text=True, timeout=600)
    except FileNotFoundError:
        notify_user(f"⚠️ `{provider_cmd}` 未安装，按降级链尝试下一个...")
        return _try_next_in_chain(provider_cmd, FALLBACK_CHAIN, queries_path, skill_dir, max_iterations)
    except subprocess.TimeoutExpired:
        notify_user(f"⚠️ `{provider_cmd}` 超时，按降级链尝试下一个...")
        return _try_next_in_chain(provider_cmd, FALLBACK_CHAIN, queries_path, skill_dir, max_iterations)

    if proc.returncode != 0:
        if "requires Node.js" in proc.stderr:
            # Node 版本不足：中断整个降级链，让用户主动决策
            raise NodeVersionError(provider_cmd, proc.stderr)
        notify_user(f"⚠️ `{provider_cmd}` 失败（退出码 {proc.returncode}），按降级链尝试下一个...")
        return _try_next_in_chain(provider_cmd, FALLBACK_CHAIN, queries_path, skill_dir, max_iterations)

    # 3. 解析 JSON 拿 best_description
    result = parse_optimizer_output(proc.stdout)
    result["optimizer_path"] = f"cli:{provider_cmd}"
    return result


def _try_next_in_chain(failed_provider: str, chain: list[str],
                        queries_path: str, skill_dir: str, max_iterations: int,
                        tried: list[str] | None = None) -> dict:
    """三级降级链：从 chain 中找到 failed_provider 之后的下一个可用 Provider 依次尝试。

    chain 固定为 ["codebuddy", "claude-internal"]，子 Agent 是最终兜底。
    tried 记录本次已尝试过的 provider，避免重复。
    """
    tried = tried or [failed_provider]
    # 找下一个尚未试过的 Provider
    next_providers = [p for p in chain if p not in tried and shutil.which(p)]
    if next_providers:
        next_cmd = next_providers[0]
        notify_user(f"  → 尝试 `{next_cmd}`...")
        return run_optimizer_via_cli(next_cmd, queries_path, skill_dir, max_iterations,
                                     extra_args=PROVIDER_EXTRA_ARGS.get(next_cmd),
                                     tried=tried + [next_cmd])
    # 全链失败 → 子 Agent 兜底
    return _fallback_to_subagent_sim(
        reason="所有 CLI Provider 均不可用",
        queries_path=queries_path, skill_dir=skill_dir, max_iterations=max_iterations,
        original_provider=tried[0] if tried else failed_provider,
        full_chain_tried=tried,
    )


def _fallback_to_subagent_sim(reason: str, queries_path: str, skill_dir: str,
                               max_iterations: int, original_provider: str | None = None,
                               full_chain_tried: list[str] | None = None) -> dict:
    """最终降级：全链失败 → 子 Agent 模拟。

    - 必须在主 Agent 输出层显式打印降级提示（首次降级长版，后续压缩为单行 status）
    - results.tsv 的 optimizer_path 记录完整降级路径（如 cli:claude→cli:codebuddy→fallback:subagent_sim）
    - 保真度提示：明确告知用户结果是 'approximate trigger rate'
    """
    chain_str = "→".join(f"cli:{p}" for p in (full_chain_tried or [])) + "→fallback:subagent_sim"
    notify_user(f"⚠️ {reason}；已降级路径 A（approximate trigger rate）")
    result = run_optimizer_via_subagent_simulation(queries_path, skill_dir, max_iterations)
    result["optimizer_path"] = chain_str if full_chain_tried else "subagent_sim"
    result["fidelity"] = "approximate"  # 标记保真度
    return result
```

> 因为 `claude` 与 `codebuddy` 的 `-p / --output-format json / --max-turns` 参数 100% 同名同义（已验证），**同一份代码无需 if-else 分支即可同时支持二者**。

跑完读取返回的 `best_description`，写回 `{target_skill_dir}/SKILL.md` 的 frontmatter。

### 何时优先选 B

- **要拿"真实触发率"数字**（生产环境路由路径上的激活率），路径 A 给不出可靠绝对值
- **棘轮迭代严格比较新旧 description**——CLI 同进程隔离才能保证两次测量条件一致
- 触发集 ≥ 15 条，路径 A 在主 Agent 上下文里跑要消耗 N×3×5=超过 200 次子 Agent 调用，token 压力大时
- 本机已装任一兼容 CLI 且用户明确希望"挂着跑"
- 国内网络条件下 `claude` 不稳定时，可改用 `codebuddy` 作为兜底（接口同构，无需改流程）
- 需要 subprocess 重试机制以提升鲁棒性

### 何时只用路径 A 即可

- 早期探索阶段，只看"改了 description 触发率有没有上升"的趋势
- 临时机器无 CLI 安装权限 / 公司网络隔离无法访问 Provider 后端
- 跑回归 smoke test，不需要 stakeholder 级数字

### NEVER

- **NEVER 在路径 B 启动前不检查 Provider 可用性** — `subprocess.run([provider_cmd, ...])` 失败会抛 `FileNotFoundError`，必须先 `which <provider_cmd>` 并把 stdout 反馈给用户
- **NEVER 假设 Provider 默认认证已就绪** — 首次调用 Provider 前应在 dry-run 中跑 `<provider_cmd> -p "ping"` 验证身份；失败时引导用户跑对应的 login 命令
- **NEVER 把任何 Provider 的 API key 写到代码或 yaml 里** — 仅用环境变量；记录 sources.yaml 时只记 `cli_provider: codebuddy`，不记凭据
- **NEVER 在 CLI 失败时硬中止流程** — 必须自动降级到路径 A 子 Agent 模拟，让棘轮迭代继续；唯一例外是 Node 版本不足（应中断让用户主动决策）
- **NEVER 静默降级** — 自动降级**必须**在主 Agent 输出层显式打印降级提示（首次长版 + 后续单行 status），且在 `optimizer_path` 列追加 `→fallback:subagent_sim` 标记
- **NEVER 在降级数据里隐藏保真度损失** — 降级后的触发率必须打 `fidelity: approximate` 标签，跨棘轮比较时不可与纯 CLI 路径数字混算
- **NEVER 在 codebuddy / 其他非 Anthropic Provider 模式下宣称"使用 Claude 模型"** — 报告中如实记录"路径 B Provider = codebuddy（GPT-5 模型）"或"= claude（Sonnet 模型）"，避免误导
- **NEVER 跨 Provider 直接对比触发率绝对值** — 不同模型的 router 模拟阈值不同；同一次 diagnose 内只用同一个 Provider 横跨棘轮迭代
- **NEVER 把路径 A 数字当作"真实触发率"对外汇报** — 路径 A 是 approximate，对外报告必须明确标注"基于子 Agent 模拟"或走路径 B 重新测算

---

## 与 diagnose 棘轮的衔接

加速器是 diagnose Step 4 棘轮循环里的**一个特殊 P1 子分支**，不替代主棘轮：

```
Step 4.1.1 锁定本轮短板
  │
  ├─ 短板在 description 触发率（缺 trigger 关键词 / 触发率 < 60%）
  │   │
  │   └─→ 路由到 Step 4.6 加速器
  │       ├─ 用户选 [手动改写]：原路径，主 Agent 改完进 4.1.4 评估
  │       ├─ 用户选 [路径 A 子 Agent 模拟]：跑本文 §路径 A 流程，5 轮内出 best_description（approximate）
  │       └─ 用户选 [路径 B CLI 新进程]：跑本文 §路径 B 流程，subprocess 输出 best_description（true rate）
  │             │
  │             └─ 启动失败 / 认证失败 / 超时（非 Node 版本不足）
  │                 └─→ 自动降级到路径 A，明示用户保真度损失
  │
  │   加速器产出 best_description 后：
  │     - 写回 SKILL.md frontmatter
  │     - git add + commit -m "diagnose-iter: description-optimizer-{path}: trigger {x}→{y}"
  │     - 进 Step 4.1.4 三维 + 实测重评
  │     - 进 Step 4.1.5 棘轮决策（综合分必须 > 旧分才 keep）
  │
  └─ 短板在其他维度（约束/冗余/工作流等）→ 走 Step 4.1.2 原流程
```

**关键约束**：
- 加速器**只优化 description**，不动 SKILL.md body
- 加速器跑完仍然要进 Step 4.1.5 棘轮决策——综合分（含 darwin 输出质量维度）严格 > 旧分才 keep
- 加速器单独 commit，方便单独 revert

---

## results.tsv 新列

为了记录加速器使用情况，`results.tsv` 在 `eval_mode` 列后追加 `optimizer_path`：

```tsv
timestamp	commit	skill	old_score	new_score	status	dimension	note	eval_mode	optimizer_path
2026-04-28T10:00	a1b2c3d	target-skill	72	78	keep	约束	补 NEVER	full_test	manual
2026-04-28T10:08	b2c3d4e	target-skill	78	84	keep	description	加速器 trigger 60→85	full_test	subagent_sim
2026-04-28T10:14	c3d4e5f	target-skill	84	86	keep	description	CLI 5 轮 best	full_test	cli:claude
2026-04-28T10:21	d4e5f6a	target-skill	86	89	keep	description	国内网络兜底	full_test	cli:codebuddy
```

`optimizer_path` 取值：
- `manual`：用户手动改写 description
- `subagent_sim`：路径 A 本地子 Agent 模拟（用户主动选）
- `cli:<provider>`：路径 B CLI Provider 成功执行，`<provider>` 为命令名（如 `cli:claude` / `cli:codebuddy`）
- `cli:<provider>→fallback:subagent_sim`：用户选了路径 B，但 Provider 启动 / 认证 / 超时失败，**自动降级**到子 Agent 模拟。事后分析时这一行的触发率是 approximate，不可与纯 `cli:<provider>` 行作严格比较
- `-`：非 description 维度的迭代

> **兼容**：旧有 `claude_cli` 视同 `cli:claude`，`cli:<provider>` 在发生降级时才追加 `→fallback:` 后缀，分析脚本应同时识别三种写法。

---

## 异常 / 边界处理

| 场景 | 触发 | 处理 |
|---|---|---|
| `trigger-queries.json` 缺失 | 用户首次跑加速器 | 进入设计阶段（参考 `test-prompts.json` 设计流程，覆盖 should_trigger / should_not_trigger / ambiguous 三类），完成后用户确认再跑 |
| 路径 A 子 Agent 输出非 YES/NO | 子 Agent 多输出了解释 / 输出 "Y" 或 "yes" | 容错解析：`re.match(r'^\s*(YES|Y|yes|是|应该)', text)`；超过 30% 解析失败时切到路径 B 或人工介入 |
| 1024 字符超限重写仍超 | 路径 A 连续 2 次重写仍 > 1024 | 主 Agent 强制截断到 1024 + 警告用户"description 过长已截断，请人工 review" |
| test_set 综合分始终未超 train | 5 轮后 test 反而下降 | 判定"过拟合"，回滚到 baseline，记录 `status=overfit` 让用户决定换路径或调整测试集 |
| 路径 B Provider 命令不存在 | `which {provider_cmd}` 失败 | 按三级链尝试下一个（codebuddy → claude-internal → 子 Agent），每步明示原因，**不静默** |
| 路径 B subprocess 超时 | `<provider_cmd> -p` 超过 5 分钟 | 终止 subprocess，按三级链尝试下一个，全链失败才退回路径 A |
| Provider Node 版本不足 | codebuddy 启动报 `requires Node.js v18.20.8 or newer` | **中断整个降级链**，明确提示"请升级 Node 到 ≥ 18.20.8"或改选 `claude-internal` / `claude`（避免用户被动降级体验）|
| Provider 首次未认证 | `<provider_cmd> -p "ping"` 返回认证错误 | 按链尝试下一个，同时输出当前 Provider 的 login 命令供用户后续修复 |
| 触发集 < 5 条 | 用户写得太少 | 拒绝执行，给出"加速器要求至少 5 条 query 才有统计意义"，引导用户补充 |
| 综合分提升 < 3 分 | 5 轮跑完只涨 1-2 分 | 标注"加速器收益边际"，建议改投资到其他维度 |

---

## 与 inspect 模块的联动

inspect D10「实测可验证性」含子项 D10.2「触发率可验证性」：

| 子项 | 检查 | 评分 |
|---|---|---|
| **D10.1 输出质量可验证性**（原 D10） | 是否有 `test-prompts.json`？ | 0-50 |
| **D10.2 触发率可验证性** | 是否有 `trigger-queries.json`？是否覆盖 should/should_not/ambiguous 三类？ | 0-50 |

D10 总分 = D10.1 + D10.2，仍不进主评分公式（独立分）。

D10.2 < 30 时建议：「补充 `trigger-queries.json`：覆盖 should_trigger（4-6 条）+ should_not_trigger（3-5 条）+ ambiguous（2-3 条），作为后续 description 加速器的输入」。

---

## NEVER（加速器自身约束）

- **NEVER 不做 60/40 split** — description 在 train_set 上"调教"出来的措辞容易过拟合，必须留独立 test_set 把关
- **NEVER 单次评估** — 子 Agent 单次输出方差大，每条 query 至少 N=3 次重复
- **NEVER 跳过 1024 字符检查** — 这是 Skill router 的硬约束，超长会截断，加速器必须守门
- **NEVER 把 SKILL.md body 投给路由模拟子 Agent** — 真实 router 只看 description，body 信息会让评测虚高
- **NEVER 改完不进棘轮** — 加速器产出仍要进 Step 4.1.5 综合棘轮决策，不绕过 darwin 风格的输出质量评测
- **NEVER 静默退化路径** — A/B 路径切换必须明示用户

---

## 与 darwin / creator 的差异化

| 能力 | darwin-skill | skill-creator | skill-assistant 加速器 |
|---|---|---|---|
| 评测「输出质量」 | ✅ Phase 1 spawn 子 agent | ❌ | ✅（复用 darwin Step 4.1.4） |
| 评测「触发率」 | ❌ | ✅ run_eval.py | ✅ 路径 A 子 Agent 模拟 + 路径 B CLI |
| 60/40 split | ❌ | ✅ | ✅ |
| 1024 字符硬约束 | ❌ | ✅ | ✅ |
| 跨 IDE 通用 | ✅ | ❌（依赖 CLI） | ✅（路径 A 默认） |
| 棘轮 + git revert | ✅ | ❌（in-memory） | ✅ |
| 人在回路 | ✅ | ❌ | ✅ |
| **CLI Provider 可插拔** | — | ❌（硬编码 `claude`） | ✅（`claude` / `codebuddy` / 任意 claude-compatible CLI） |
| `.skill` 打包 | ❌ | ✅ package_skill.py | 暂不集成 |

> **设计原则**：把 darwin 的协议化 + creator 的量化引擎在「短板路由」处汇合，而不是简单拼接。短板在 description → 走 creator 风格的量化优化；短板在 workflow/约束 → 走 darwin 风格的协议化重构。

---

## 相关文档

- 诊断主流程：详见 `modules/diagnose.md`（Step 4.6 入口）
- 质检 D10 维度：详见 `modules/inspect.md`（D10.2 触发率可验证性）
- 测试 prompt 设计：详见 `modules/diagnose.md` Step 0
- 上游参考：[anthropics/skills/skills/skill-creator](https://github.com/anthropics/skills/tree/main/skills/skill-creator)
