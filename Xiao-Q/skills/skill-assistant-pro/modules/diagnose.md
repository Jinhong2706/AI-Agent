# 诊断模块

基于 Prompt 效能模型 + 知识增量分析 + **棘轮迭代闭环（融合自 darwin-skill）**对已有 Skill 进行诊断与重构。

> **核心理念**：Skill 是 LLM 的运行时上下文注入。评估 Skill 不看结构是否"干净"，而看注入后 LLM 的任务完成质量是否提升。每个 Token 都参与 LLM 每一步推理的注意力计算。
>
> 本模块的 Step 0（测试 prompt 设计）和 Step 4.1.4（独立子 Agent 双跑）被 [inspect.md `eval_mode=dynamic/hybrid`](inspect.md) 复用——评审时即可跑动态评测，无需先进 diagnose。**复用边界**：inspect 跑动态评测后**不**自动进入棘轮迭代（不改文件）；用户在 inspect 报告末尾点 `[1] 进入 diagnose 棘轮迭代` 才进入本模块的 Step 4。

---

## Skill 类型谱系

诊断前必须先识别目标 Skill 的类型——不同类型适用不同诊断权重：

| 类型 | 特征 | 核心价值在 | 示例 |
|------|------|-----------|------|
| **执行型** | 输入 → 确定性操作 → 输出 | Script | pdf-editor, image-rotator |
| **流程型** | 多步骤、有分支的工作流 | Script + Prompt | deploy-tool, ci-pipeline |
| **规范型** | 标准、约束、质量要求 | Prompt + Reference | code-style, brand-guide |
| **认知型** | 设计哲学、领域知识 | Prompt | skill-creator, architecture-guide |

从左到右，Prompt 中的内容从"可下沉的逻辑"过渡为"不可替代的知识注入"。

---

## 三维诊断框架

### 1. 指令 (Directive) — 权重 40%

驱动 LLM 做对事的 Token。三种来源：

| 来源 | 机制 | 示例 |
|------|------|------|
| **激活** (Activate) | 触发 LLM 已有但默认不用的能力 | "使用祈使句"——LLM 会，但不提醒就不做 |
| **注入** (Inject) | 注入训练数据中不存在的知识 | 公司内部 API Schema、私有业务规则 |
| **锚定** (Anchor) | 在长上下文中维持注意力焦点 | 核心原则的反复呼应 |

**缺指令 = Skill 加载后 LLM 行为几乎没变化。这是最严重的问题。**

### 2. 约束 (Constraint) — 权重 30%

防止 LLM 犯错的 Token。检查要点：常见错误/反模式禁止、边界条件覆盖、渐进式披露（发现层/激活层/执行层内容是否各归其位）。

**缺约束 = LLM 会犯 Skill 设计者已知但未声明的错误。**

### 3. 冗余 (Redundancy) — 权重 30%

对任务无贡献的 Token（类似死代码）。使用**知识三分法**精确分类每段内容：

| 类别 | 定义 | 处理 |
|------|------|------|
| **Expert（专家知识）** | LLM 真的不知道的领域知识 | 必须保留——Skill 的核心价值 |
| **Activation（激活知识）** | LLM 知道但可能想不到的 | 简短保留——起提醒作用 |
| **Redundant（冗余知识）** | LLM 肯定知道的基础内容 | 应删除——浪费上下文窗口 |

**冗余的典型来源**：
- 角色扮演（"你是一个专业的..."）
- 与 scripts/ 重复的逻辑
- LLM 已具备的常识和标准教程
- SKILL.md 与 references/ 的内容重叠
- 行业标准术语的定义

**SKILL.md body Token > 6000 时，低频内容必须拆分到 references/**。

**关键区分**：看起来像冗余但实际在构建指令的 Token（如认知型 Skill 的背景知识注入），不是冗余。判断标准：删掉后 LLM 的任务表现是否下降？

**知识比例基准**：
- 优秀 Skill：Expert 70%+ / Activation < 20% / Redundant < 10%
- 合格 Skill：Expert 40-70% / Activation < 30% / Redundant < 30%
- 劣质 Skill：Expert < 40% / Redundant > 40%

### 效能分计算

```
效能分 = 指令评级 × 40 + 约束评级 × 30 + (1 - 冗余率) × 30
```

| 分数区间 | 等级 | 含义 |
|----------|------|------|
| 85-100 | A | 优秀 |
| 70-84 | B | 良好，可选择性优化 |
| 50-69 | C | 需要重构 |
| 30-49 | D | 急需重构 |
| 0-29 | F | 建议重写 |

---

## 工作区前置准备

> 本步骤**首次进入 diagnose / 任何 inspect 动态评测时**自动跑一次；后续步骤的所有产物落到这里。**绝不在被评测 skill 目录内**写测试输出 / transcript / benchmark.json。

#### W.1 解析 workspace 路径

> ⚠️ **不得手拼路径、不得重新实现解析逻辑**——`scripts/resolve_workspace.py` 是唯一权威入口。重复实现会导致漂移（真实事故：未走解析直接建 `.cursor/skills/<skill>-workspace/`，27 个产物文件被迫迁移）。

**标准调用**（读 `config/sources.yaml` 的 `preferences.workspace.layout`，默认 `sibling_of_skills_dir`）：

```bash
python3 ../scripts/resolve_workspace.py \
  --skill <skill_path> \
  --layout <layout_from_sources.yaml> \
  --check-existing      # 同时扫现有 sibling workspace 验证路径模板一致性
```

**输出契约**：
- `stdout` 单行打印 workspace 绝对路径（即将创建或复用）
- `stderr` 打印解析说明 + sibling 列表
- exit `0` = 路径合法可用 / exit `1` = 路径不合法或 sibling 模板不一致 / exit `2` = CLI 参数错误

**内部实现参考**（仅供阅读理解 · **不要在 Agent 流程里手抄这段代码**，必须调脚本）：

<details>
<summary>resolve_workspace_path() 伪代码</summary>

```python
def resolve_workspace_path(skill_path: Path, layout: str) -> Path:
    if layout == "sibling_of_skills_dir":
        return skill_path.parent / "skill-assistant-workspace" / skill_path.name
    elif layout == "external":
        root = Path(cfg["workspace"]["workspace_root"]).expanduser()
        return root / f"{skill_path.name}-workspace"
    elif layout == "project_local":
        return (find_git_root(skill_path) or Path.cwd()) / ".skill-doctor" / skill_path.name
```

</details>

**双层防御**：
1. **L3 工具层**：`resolve_workspace.py` 自带 `validate_workspace_path()`，解析出来的路径若不在 `skill-assistant-workspace/` 下（或对应布局根下），脚本本身 exit 1
2. **L4 落盘层**：`scripts/manifest_io.py write_manifest_atomic()` 在写之前再做一次 `validate_workspace_path(data["workspace_root"], layout)`，路径不合法直接抛 `ValueError` 拒绝写入

完整路径解析规则 + 边界处理：[references/workspace-layout.md](../references/workspace-layout.md)。

#### W.2 manifest 三态判定

```
路径不存在
  → 创建目录树 + 写 README.md + 写 .gitignore（auto_gitignore=true）+ 初始化 manifest.yaml
  → 进入 W.4 写 session_lock

路径存在 + manifest.yaml 不存在
  → 警告："检测到 workspace 目录但无 manifest（疑似手工建立 / 历史残留）"
  → 让用户选择：[A] 接管现有目录（创建 manifest 但保留现有文件） [B] 备份后重建 [C] 改用其他 layout

路径存在 + manifest.yaml 存在
  → 校验 manifest_version 与 skill_assistant_version
  → 校验 skill.initial_skill_hash 与当前 skill 目录 hash
  → 进入 W.3 处理 session_lock + status
```

详细 manifest schema：[references/manifest-schema.md](../references/manifest-schema.md)。

#### W.3 session_lock + status 处理

| manifest 现状 | 处理 |
|---|---|
| `session_lock` 不存在或 `enabled=false` | 直接进入下一步 |
| `session_lock.pid` 存活 + 未过期 | **阻断**，菜单：[A] 强制接管（kill 旧 + 接管） [B] 等待重试（每 30s × 5 次） [C] 放弃本次 |
| `session_lock.pid` 存活但已过期（` > timeout_hours`） | 自动清锁 + 提示用户「检测到过期锁，已清理」+ 进入 |
| `session_lock.pid` 不存活 | 视为崩溃残留 + 自动清锁 + 进入 |
| `status=in_progress` + 无活锁 | **resume 菜单**：[A] 续跑（从 current_iteration 中断点继续） [B] 丢弃当前 iteration 重跑 [C] 关闭会话 |
| `status=completed` + 无活锁 | 询问 [A] 沿用现有 workspace 跑新一轮 [B] 归档（移到 archive/）后重新开始 [C] 改用别处 |
| `skill.initial_skill_hash` 与当前不一致 | 提示「skill 被外部修改」，菜单：[A] 重置基线（更新 hash + 重起棘轮） [B] 沿用旧 hash（继续旧轮） [C] 中止 |

#### W.4 写 session_lock

```yaml
session_lock:
  enabled: true
  pid: <当前 agent 进程 pid>
  hostname: <hostname>
  ide: <cursor/codebuddy/cli>
  acquired_at: <now ISO8601>
  expires_at: <now + session_lock_timeout_hours>
```

每次写 manifest 必须刷新 `expires_at`。退出时（含正常完成 / aborted）将 `pid` 置 null。

#### W.5 初始化目录结构

```
<workspace>/
├── manifest.yaml              # W.1-W.4 写入
├── README.md                  # 自动生成，说明用途
├── .gitignore                 # auto_gitignore=true 时生成
├── trigger-queries.json       # 后续 inspect 引导用户写（D10.2 验证用）
├── test-prompts.json          # 【共享基线】Step 0 引导用户写/迭代中可更新
├── skill-snapshot/            # Step 1 进入前 cp -r 整个 skill 目录
├── results.tsv                # Step 4 棘轮决策时写入；表头预留
└── iteration-N/               # 每轮棘轮迭代的产物（N=1,2,3...）
    ├── test-prompts-snapshot.json  # 【本轮快照】迭代开始时自动 cp 共享基线
    ├── diagnosis-report.md
    ├── benchmark.json
    └── ...
```

**test-prompts.json 位置与版本策略**：

| 文件 | 位置 | 用途 | 谁来写 |
|---|---|---|---|
| `<workspace>/test-prompts.json` | workspace 根 | **共享基线**，当前活跃版本，可在迭代间优化 | Step 0 / D.0 交互式写入 |
| `<workspace>/iteration-N/test-prompts-snapshot.json` | 每轮迭代目录 | **本轮快照**，确保迭代审计可追溯 | 每次进入 Step 4 棘轮前自动 cp |
| `<skill_dir>/test-prompts.json` | skill 目录（旧位置）| 旧版兼容，**新版不再写入** | 仅兼容读取 |

> **设计理念**：测试集本身应随 skill 成熟而优化（所以共享基线可更新），但每轮迭代必须有当时用的测试集快照（所以自动 cp 快照）。
> 这样既支持"测试集本身也在改进"，又保证每轮棘轮决策的可复现性。

> **迁移提示**：检测到旧 `.skill-doctor/<skill>/` 目录时，提示用户「检测到旧版本评测产物，是否迁移到新 workspace？」用户拒绝则旧目录不动、新 workspace 从空开始。

---

## 交互流程（严禁跳步）

### Step -1：eval_mode 确认（所有 Step 之前必须执行，不可跳过）

**除非用户在进入 diagnose 时已明确说明评审策略，否则必须停下来展示以下菜单：**

```
🔍 请选择评审策略（eval_mode）：

  [0] ⚡ preview（30s-2 min · 快速预览）
      → 单条 P0 happy prompt × 1 次，看个大方向
      → 适合：完整评测前的 sanity check / 不确定要不要花 30 分钟
      → 结果不写 results.tsv 主分，仅决策下一步

  [1] static（2-5 min · 结构分析）
      → 只做三维评分 + 知识分类 + 病症检测
      → 无需测试集

  [2] dynamic（10-20 min · 仅实测）
      → 跳过结构分析，直接 spawn 子 Agent 双跑 test-prompts.json
      → 需要先有测试集

  [3] hybrid（15-30 min · 双轨独立）★ 推荐
      → 结构分析 + 子 Agent 实测双轨，各自独立评分
      → 需要测试集

  [4] blind_hybrid（20-40 min · 盲评消除身份偏置）
      → hybrid 基础上用 Comparator 子 Agent 盲评 A/B
      → 最严格，适合对外发布前的正式评审

当前已有测试集：{test_prompts_exist}
{IF previous_eval_exists: 检测到上次评测：{date} · 综合分 {prev_score} · 模式 {prev_mode}}
```

**以下情况视为"用户已明确"，可跳过此菜单**：
- 用户输入中含 "preview" / "预览" / "快速看一下" → `eval_mode=preview`
- 用户输入中含 "static" / "静态" / "structure" → `eval_mode=static`
- 用户输入中含 "dynamic" / "动态" / "实测" → `eval_mode=dynamic`
- 用户输入中含 "hybrid" / "混合" / "双轨" → `eval_mode=hybrid`
- 用户输入中含 "blind" / "盲评" → `eval_mode=blind_hybrid`
- 用户输入中含 "只看结构" / "不跑测试" → `eval_mode=static`

> ⚠️ **NEVER 跳过此步骤直接进入 Step 0**——eval_mode 决定后续整个流程。静态模式不用测试集，动态/混合模式必须先确认测试集存在再继续。

> **preview 模式特别处理**：选 [0] 时**不进**棘轮迭代主流程，跑完单点采样后展示 4 选项菜单（继续 hybrid / 跳到 static / 看 transcript / 结束），用户选完后才进 Step 4 棘轮或退出 diagnose。详见 [inspect.md 入口菜单 preview 模式执行细节](inspect.md#评测形态选择v150-入口--v201-批次-c-增-preview--重排)。

---

### Step 0：测试 Prompt 确认与诊断

> **任何时候进入 diagnose 都必须执行此步骤**——无论是首次还是重复迭代。没有经过确认的测试集，棘轮迭代的"keep/revert"决策无可信依据，所有优化停留在结构层面只是在猜。

#### 0.1 走共用流程

测试集的定位 / 展示 / 丰富度诊断 / 用户确认全部走 [references/test-prompts-design.md](../references/test-prompts-design.md) 共用流程（5 步 P.1-P.5），与 inspect 一致。

执行分支：

```
调用 test-prompts-design Step P.1 定位测试集
├─ 找到 → P.2-P.4 展示 + 丰富度诊断 + STOP 用户确认 → P.5 写 hash
├─ 旧位置 → 迁移后同上
└─ 不存在 → 进入 0.2 选择生成模式（diagnose 特有），生成完后再走 P.2-P.5
```

**同会话跳过**：

- 用户从 inspect 报告 [1] 进入棘轮时，inspect 已写过 `manifest.test_prompts_confirmation.hash`
- diagnose Step 0 计算当前 test-prompts.json hash，与 manifest 中一致 → **跳过 P.2-P.4** 重复确认，仅简短打印「✓ 测试集与本会话上次确认一致 · {N} 条 prompt · 覆盖 {M} 模块」
- hash 不一致（用户中途改了文件 / 跨会话）→ **强制走完整 P.2-P.4**
- 用户输入"review test-prompts" → **强制走完整 P.2-P.4**，无视 hash

详见共用模块的「同会话跳过逻辑」段。

> 用户提供的是文本片段而非目录、或明确说"只看结构不实测"时，跳过本步骤，并在最终报告里标注 `eval_mode=structure_only`。

#### 0.2 选择生成模式（仅 0.1 找不到 test-prompts.json 时执行）

向用户提供两条路径：

| 模式 | 适用 | 工作量 | 输出粒度 |
|---|---|---|---|
| **★ 自动模式（推荐）** | 中等 / 复杂 skill，自己不确定怎么写测试集 | 用户审 1-2 次 ≈ 5 分钟 | 5 大类 × 多 scope × 细粒度 yes/no judgement，**与 D10.3 critique evals 对齐** |
| **手动模式** | 简单 skill，已经有清晰测试想法；或自动模式生成结果不满意 | 用户写 2-3 条 prompt + expected | 自由文本 expected，依赖 Grader 自由打分 |

#### 0.3 自动模式（默认推荐）

按 [references/auto-judgement-generator.md](../references/auto-judgement-generator.md) 的 5 阶段流程执行：

```
Phase 1 收集与分析  → 读 SKILL.md + references + README，抽工作流 / 规则 / 输出格式
Phase 2 推断 scopes → 识别多个执行路径；至少有 `all` scope
   ↓ STOP 用户确认 scopes
Phase 3 5 大类生成 → A 加载 / B 工作流 / C 输出质量 / D scope 特有 / E 准则合规
Phase 4 呈现给用户 → 按 scope 分组表格
   ↓ STOP 用户确认 judgements
Phase 5 写入 test-prompts.json（schema 含 scope + judgements + negative_judgements）
Phase 6（可选）跑 critique evals → Grader 反向质询，标记太宽松/太严苛/缺位置指引的项 → 回 Phase 3 微调
```

**自动模式产出的 test-prompts.json schema**：

```json
[
  {
    "id": 1,
    "scenario": "happy_path",
    "scope": "all",
    "prompt": "用户会说的话",
    "expected": "自由文本期望（给 Grader 看）",
    "judgements": [
      {"name": "skill-invoked", "category": "A_loading",
       "question": "检查 SKILL.md 是否被读取——transcript 中应看到 Read 调用 ..."}
    ],
    "negative_judgements": [
      {"name": "no-forbidden-artifact",
       "question": "**不**应该生成 X.md ..."}
    ]
  }
]
```

> **向后兼容**：`scope` / `judgements` / `negative_judgements` 缺失时退化（Grader 仅按 expected 自由打分），旧 test-prompts.json **照样可用**。

#### 0.4 手动模式（原流程）

阅读 SKILL.md 后设计 **2-3 条**测试 prompt，覆盖：

- **Happy path**：最典型的使用场景（用户最常说的那句话）
- **复杂或歧义场景**：边界 / 多步骤 / 含模糊指令的真实案例
- （可选）**反例场景**：用户说了"似是而非"的话，期望 Skill 不被错误激活

写入 `<workspace>/test-prompts.json`（**绝不**写到 skill 目录内，保持 skill 目录纯净）。

#### 0.5 共同收尾

**STOP**：展示给用户，确认后再进入 Step 1。测试 prompt 的质量直接决定后续优化方向是否正确。

> 用户提供的是文本片段而非目录、或明确说"只看结构不实测"时，跳过本步骤，并在最终报告里标注 `eval_mode=structure_only`。

### Step 1：诊断报告

1. 运行结构探测脚本获取事实数据：
   ```bash
   python3 scripts/diagnose_skill.py <target-skill-directory>
   ```
   用户提供文本片段而非目录路径时，跳过脚本执行。

2. 阅读目标 Skill 完整内容，参阅 [references/diagnosis-calibration.md](../references/diagnosis-calibration.md) 中的评分校准表和 Token 分类示例，完成三维语义评估。

3. 输出诊断报告（模板见 [assets/diagnosis-report-template.md](../assets/diagnosis-report-template.md)），保存到 `<workspace>/iteration-1/diagnosis-report.md`。报告须包含：
   - 知识比例分析：Expert / Activation / Redundant 各占百分比
   - 病症检测：对照常见病症库标注命中项
   - 三维评分：指令 / 约束 / 冗余 各维度评级

4. **帕累托收敛判定**：效能分 ≥ 80 且三个维度均不低于"中" → 已收敛。
   - 已收敛：输出帕累托分析，说明每个优化建议的代价，流程结束。
   - 未收敛：正常进入 Step 2。

5. **STOP**：等待用户确认。

### Step 2：逻辑蓝图

用户确认 Step 1 后：

1. 参照 [assets/logic-blueprint-template.md](../assets/logic-blueprint-template.md) 模板格式，输出重构蓝图。

2. 核心不是"把东西从 Prompt 移到 Script"，而是**让每个 Token 在最适合它的层工作**：
   - LLM 擅长 → Prompt（意图理解、知识框架、设计哲学）
   - CPU 擅长 → Script（确定性计算、格式转换、正则匹配）

3. **STOP**：等待用户确认。

### Step 3：最终交付

用户确认 Step 2 后，生成：
1. 优化后的 SKILL.md（指令和约束增强，冗余移除）
2. 脚本文件（`scripts/`）
3. 参考文档（`references/`，如需要）

> **单轮交付即满足时直接结束**。如用户希望继续迭代到收敛或希望对实测效果做闭环验证 → 进入 Step 4 棘轮迭代。

### Step 4：棘轮迭代（融合 darwin-skill / autoresearch）

适用场景：用户说「迭代到收敛」/「再优化一轮」/「改完跑测试看看真的更好吗」/「自动优化」。

> **核心机制**：评估 → 改进 → 实测 → 决策（保留/回滚）→ 重新评估，直到瓶颈或预算用尽。**每一轮只改一个最低维度，避免多变更无法归因**。

#### 4.0 准备

```
1. 确认 workspace 已初始化（W.1-W.5 已跑），manifest.session_lock 由本会话持有
2. 检查 git 仓库状态（git rev-parse），不在 git 仓库时降级为 cp 备份（异常处理见下表）
   另在 <workspace>/skill-snapshot/ 做一份 cp -r 完整快照，独立于 git，作为终极兜底
3. 分支策略选择
4. 初始化 <workspace>/results.tsv（不存在则建表头）
5. 读取 <workspace>/test-prompts.json（来自 Step 0）
6. 在 manifest.iterations[] 追加新条目（status=in_progress）
7. **时间预算初始化**：按 eval_mode 查 [references/time-budget.md](../references/time-budget.md) 默认表
   写 manifest.evaluation.time_budget = { soft_deadline_seconds, hard_deadline_seconds, started_at, elapsed_checkpoints: [] }
   告知用户："本轮 iteration 预计 X 分钟，soft 提醒 Y、hard 降级 Z"
   每完成 scenario 后追加 elapsed_checkpoints；soft 超时 STOP 弹菜单（5 选项 a-e）；hard 超时按 time-budget.md 表自动降级
   partial 评测（hard 降级触发）results.tsv 加 time_budget=hard_exceeded，4.1.5 棘轮决策跳过判 unchanged
```

**Step 4.0.3 分支策略选择菜单**

向用户展示：

```
🌿 选择分支策略：

  [1] 新建独立分支（默认推荐·单 skill 优化）
      → git checkout -b auto-optimize/{skill-name}-YYYYMMDD-HHMM
      → 完全隔离，任何时候可 git revert 精确回滚
      → ⚠️ 同一仓库下并行优化多个 skill 时会冲突（同一时刻只能 checkout 一条分支）

  [2] 在当前分支直接修改（多 skill 并行友好）
      → 不切换分支，依赖 workspace/skill-snapshot/ 的文件快照做兜底
      → 支持同一仓库不同 skill 同时在不同终端 / IDE 窗口里并行跑
      → 回滚时从 skill-snapshot/ 手动恢复文件，或通过 manifest 记录的 commit hash 精准 revert

  [3] git worktree（高级·真正并行推荐）
      → git worktree add ../worktree-{skill-name} -b auto-optimize/{skill-name}-YYYYMMDD-HHMM
      → 同一 repo 不同 worktree 各自独立工作目录 + 独立分支，互不干扰
      → 完成后 git worktree remove + 合并回主分支
      → 前置条件：git 2.5+（绝大多数环境已满足）
```

> **何时选哪个**：
> - 只优化一个 skill，或顺序优化：选 **[1]**（最安全，有完整 git history）
> - 同一仓库里多个 skill 同时跑（不同终端/窗口并行）：选 **[2]**（快，靠 workspace 快照兜底）或 **[3]**（真隔离，推荐团队协作场景）
> - 用户未做选择时默认 **[1]**，并提示"如果需要并行优化多个 skill，可选 [2] 或 [3]"

#### 4.1 棘轮循环（每个 Skill 独立执行）

```
round = 0
old_score = Step 1 报告的总分
while round < MAX_ROUNDS（默认 3）:
    round += 1

    # 4.1.1 诊断 — 锁定本轮要攻击的最低维度
    取三维（指令/约束/冗余）+ 知识三分法中得分最低的一项

    # 4.1.2 改进方案
    针对该最低维度，按"优化策略库 P0-P3"（见下）生成 1 个具体方案：
      - 改什么（具体段落/行）
      - 为什么（对应的诊断条目）
      - 预期 Δ 分数

    # 4.1.3 执行改进
    编辑 SKILL.md → git add → git commit -m "diagnose-iter: {skill}: {改进摘要}"

    # 4.1.4 重新评估（关键：用独立子 Agent 评分，N 重复跑）
    # 子 Agent 装配 / 落盘 / 收尾校验全流程见 references/sub-agent-protocol.md
    a. 结构维度：主 Agent 重新跑 Step 1 三维评分
    b. 实测维度（可选但强烈推荐）：spawn 独立子 Agent
       - 对 test-prompts.json 中每条 scenario 执行 **N_repeats(prompt) 次双跑**：
         - N_repeats 按 prompt 优先级差异化分配预算（P0=5 / P1=3 / P2=2 / 缺字段=3）
         - 默认表（用户可在 manifest.iterations.n_repeats_policy 覆盖）：
           ```
           priority=P0 → N_repeats = 5    # 核心场景，高样本量降低 stddev
           priority=P1 → N_repeats = 3    # 次要场景，原默认
           priority=P2 → N_repeats = 2    # 锦上场景，低成本
           缺 priority 字段（旧 schema） → N_repeats = 3
           ```
         - 与 4.1.5 动态阈值（t 分布）联动：N=2 时 df=1 阈值过宽，强制降级 0.5σ + confidence=low；
           N=5 阈值约 0.66σ；N=10 阈值约 0.44σ —— 优先级越高决策越严谨
         - with_skill: 加载新版 SKILL.md 跑该 prompt
         - baseline: 不加载 Skill 跑同一 prompt
         - 输出落到 <workspace>/iteration-N/eval-XXX/{baseline,with_skill}/run-{1..N}/outputs/
         - **fidelity_mode**（ 新增，从 manifest.evaluation.fidelity_mode 读，默认 `subagent_default`）：
           * `subagent_default`：spawn 子 Agent 跑（耗时 1.0×），常规棘轮迭代用这个
           * `cli_fresh_process`：用 inspect.md D.0.2 选好的 CLI Provider 启全新 OS 进程跑（耗时 1.5-2×），适合上线决策 / 怀疑 context 污染时
           * 升级到 `cli_fresh_process` 必须用户明示，不允许主 Agent 默认升档；results.tsv 加 `fidelity` 列一行可见
       - 评分模式按 eval_mode 分支：
         * preview                 — N=1，1 条 P0 happy prompt，主 Agent 评
         * static / dry_run        — 主 Agent 自评（兼容旧路径，留作降级）
         * dynamic / hybrid        — 调用 Grader 子 Agent 评每跑（agents/grader.md）；产出 grading.json
         * blind_hybrid             — 4.1.4.5 调用 Comparator 子 Agent 盲评 A/B；产出 comparison.json
       - 聚合 N 次：算 mean / stddev / min / max 写入 <workspace>/iteration-N/benchmark.json
         **每 prompt 独立记录 N**（schema 加 `per_prompt_runs: {prompt_id: N}`），不再用单一 N 描述整轮
    c. 子 Agent 不可用时降级为 dry_run（**强制落盘**）：主 Agent 模拟典型 prompt 的执行思路，但**推演结果必须以 dynamic 模式同款 schema 写文件**——只在对话记忆里推演 = 报告阶段读不到数据 = `{{EVAL_CONTENT}}` 留空。
       **dry_run 落盘最小必填集**（每条 test-prompt 一组）：
       ```
       <workspace>/iteration-N/eval-<scenario>/
       ├── eval_metadata.json          必填字段：scenario（须为 5 类枚举值之一）/ prompt（完整原文）/ eval_mode: "dry_run" / functional_module（来自 test-prompts.json）/ priority（P0/P1/P2）
       ├── baseline/run-1/
       │   ├── outputs/report.md       ← 主 Agent 推演的 baseline 输出全文（标记"⚠️ dry_run 推演"）
       │   └── grading.json            ← { passed_count, total_count, expectations: [{text, passed, evidence}] }
       └── with_skill/run-1/
           ├── outputs/report.md       ← 主 Agent 推演的 with_skill 输出全文
           └── grading.json            ← 同上 schema
       ```
       grading.json 的 expectations 数组**必须**逐条对应 test-prompts.json 的 judgements，每条标 `passed: true|false` + `evidence` 引用推演输出文本片段；不允许"全 passed=true 不附 evidence"的偷懒写法。

       **🛡️ dry_run 落盘后立即 sanity check**：

       每条 test-prompt 写完 grading.json 后，主 Agent 必须**就地**校验下面 7 项，任一失败立刻回写本条不进 4.1.5：
       ```
       ✓ 1. <eval-scenario>/baseline/run-1/grading.json 存在且 size > 50 字节
       ✓ 2. <eval-scenario>/with_skill/run-1/grading.json 存在且 size > 50 字节
       ✓ 3. 两个 grading.json 均含 expectations[] 且 length == test-prompts.json 中该 scenario 的 judgements 数量
       ✓ 4. 每条 expectation 含 {text|question, passed, evidence} 三字段
       ✓ 5. evidence 不为空字符串、不为 "见上文"/"如前所述" 这种空话
       ✓ 6. with_skill grading 不允许"全 passed=true"（baseline 也不允许"全 passed=false"）—— 这种是没用心推演
       ✓ 7. outputs/report.md 的首行明确含 "⚠️ dry_run 推演" 标记，让下游一眼看出是模拟数据
       ✓ 8. eval_metadata.json 存在，且同时包含：
              - scenario（值必须属于 ['happy_path','complex','edge','negative','error'] 之一）
              - prompt（完整字符串，非空、非占位符）
              - functional_module（来自对应 test-prompts.json 条目，不得为空）
              - priority（P0/P1/P2）
              ↳ 此检查对应报告 ④ 章节"测试用例覆盖矩阵"和每个 eval-card 中的 prompt 显示；
                缺任一字段时 generate-full-report.mjs 会静默降级（显示 unassigned / 无 prompt 记录），不报错，故必须在写入阶段校验。
       ```

       任何一条失败 → 主 Agent 回到本条 prompt 重写 grading.json + outputs/report.md，**不进 4.1.5**。这套校验和 Step 6 的 [generate-full-report.mjs](../scripts/generate-full-report.mjs) sanity check 是**冗余兜底关系**（前者抓未落盘 / 落盘伪造，后者抓渲染产物缺章节）；两道关都不能省。

       **🛡️ 第 1.5 道关·schema 校验器**——上面 8 项内容 sanity 不能抓 schema 字段名错（如 `summary.passed/total + judgements[]` 看似等价但脚本字面读 `passed_count + expectations[]`）。落盘后**必须立即跑**：

       ```bash
       python3 .cursor/skills/skill-assistant/scripts/validate_eval_artifacts.py \
           <workspace>/iteration-N/
       ```

       退出码：`0`=全过进 4.1.5；`1`=ERROR 必须回写 grading.json；`2`=WARN 可进但下轮升级 schema；`3`=路径错。**禁止用 `--skip-validator` 绕过**——这是修过的真实事故的最后一道关。

       results.tsv 同时追加一行，`eval_mode=dry_run`。

    # 4.1.4.5 盲评（仅 eval_mode=blind_hybrid）
    对每条 scenario 的每次重复：
       1. 主 Agent 随机决定 mapping = {A: baseline, B: with_skill} 或 {A: with_skill, B: baseline}
       2. 把两份 outputs 软链 / 复制到 <workspace>/iteration-N/eval-XXX/_anonymous/{A,B}/outputs/
       3. mapping 写到 anon_mapping.json（不提供给 Comparator）
       4. 调用 Comparator 子 Agent（agents/comparator.md），产出 comparison.json
       5. 主 Agent 揭盲：用 anon_mapping 反推 winner_role
       6. 即将进入 4.1.6 post-hoc 归因

    # 4.1.5 棘轮决策
    eval_mode in [static, dry_run, dynamic_dry_run]:
        if 新分 > old_score(严格大于) → keep；else → revert
        results.tsv 追加行（标 confidence=approximate）

    eval_mode in [dynamic, hybrid, blind_hybrid] 且 N_repeats >= 2:
        # ——— 固定 0.5σ 阈值在 N=3 时假阳性率 ~30%，必须按 N 动态调整 ———
        new_mean, new_stddev = benchmark.json[mean, stddev]

        # Step A: 高方差兜底（先于阈值判断）
        coef_of_var = new_stddev / max(abs(new_mean), 1e-6)
        if coef_of_var > 0.30 and N_repeats < 5:
            status = high_variance；提示用户："本轮变异系数 CV={cv:.2f} > 0.30，N_repeats={N} 偏小。
                建议 [a] 把 N_repeats 升到 5 或 7 重跑本轮 [b] 接受高方差直接以 0.5σ 判定（不推荐）"
            **STOP**：等用户选 [a]/[b]；选 [a] 重跑 4.1.4，选 [b] 走老的 0.5σ 路径
            results.tsv 标 eval_quality=high_variance

        # Step B: 动态阈值（标准 t 分布单边 α=0.10 临界值 × stddev / sqrt(N)）
        # df = N - 1；查 t 表的工程化简表：
        t_table = { 2: 1.886, 3: 1.638, 4: 1.533, 5: 1.476, 6: 1.440, 7: 1.415, 8: 1.397, 9: 1.383, 14: 1.345, 19: 1.328, 29: 1.311 }
        df = N_repeats - 1
        t_alpha = t_table[df] if df in t_table else 1.282  # 大样本回退到 z=1.282
        threshold = t_alpha × new_stddev / sqrt(N_repeats)
        # 直观示例（每条 prompt 满分 100）：
        # N=3, stddev=8 → threshold = 1.886 × 8 / √3 ≈ 8.71 分
        # N=5, stddev=8 → threshold = 1.476 × 8 / √5 ≈ 5.28 分
        # N=10, stddev=8 → threshold = 1.383 × 8 / √10 ≈ 3.50 分

        # Step C: 三档决策
        if new_mean > old_mean + threshold:
            status = keep；old_mean = new_mean；old_stddev = new_stddev
        elif new_mean < old_mean - threshold:
            status = revert; git revert HEAD; break
        else:  # 在 t 分布噪声范围内
            status = unchanged; old 不变；记录但不 break
        results.tsv 追加行（mean/stddev/N/df/t_alpha/threshold/status；眼见为实）

    > **理由**：固定 0.5σ 在 N=3 时（df=2，t=4.303）远低于统计显著门槛——一次 +5 分的"提升"在 stddev=10 的样本里假阳性率 ~30%。动态阈值用 N 调节门槛：N 小则严格，N 大则放松，统计学意义稳定。
    > **N_repeats 的选择策略**：默认 3（速度优先）；首轮 high_variance 警告后建议升 5；研究级深度评测建议 7-10。N=2 时 df=1，t 阈值过宽，**强制降级为 0.5σ 老路径并标 confidence=low**（results.tsv 含 N_repeats_too_small 标记）。

    # 4.1.5.5 Grader vs static 交叉一致性校验
    # 共用规则见 inspect.md D.3.5
    static_score = 4.1.4.a 算出的 10 维度静态分（已 0-100 归一）
    dynamic_score = 4.1.4.b 聚合的总动态分（mean × 10，0-100）
    delta = abs(static_score - dynamic_score)
    consistency = "critical" if delta > 25 else ("warning" if delta > 15 else "consistent")
    写 <workspace>/iteration-N/consistency.json：
       { static, dynamic, delta, consistency, pattern: "static_high"/"dynamic_high"/null,
         d10_3_score: <来自 grader critique evals>, alert_message: <人话> }
    consistency != consistent 时：
       - 在本轮 4.1.6.5 报告 Must-Read 顶部加红/橙色警告（generate-full-report.mjs 读 consistency.json 自动渲染）
       - 4.1.5 棘轮决策不受影响（动态分仍按 t 阈值判 keep/revert），但若 delta>25 + 判 keep，提示用户："本轮 keep 了，但静态-动态强烈分歧，建议先复核测试集判别力"
       - 若 D10.3 测试集判别力 < 0.5，警告升级为"测试集可能没区分度"，建议回 Step 0 重做 test-prompts

    # 4.1.6 post-hoc 归因（仅 eval_mode=blind_hybrid）
    对该 iteration 选最有代表性的 1 条 scenario（默认 winner_role=baseline 的，否则 confidence=high 的）：
       调用 Analyzer 子 Agent（agents/analyzer.md），产出 analysis.json，含：
         - structural_differences / instruction_following
         - winner_strengths / loser_weaknesses（必带 SKILL.md 行号引用）
         - improvement_suggestions（priority high/medium/low）
         - carry_over_to_next_iteration: { should_keep, should_strengthen, should_drop }
       主 Agent 把 carry_over_to_next_iteration 注入下一轮 4.1.2 改进方案的 prompt 上下文

    # 4.1.6.5 渲染全景报告（每轮强制执行，不按 eval_mode 条件触发）
    无论 eval_mode 是 static / preview / dynamic / hybrid / blind_hybrid / dry_run，**每轮都必须**生成两份 HTML：

    【A】单轮摘要 iter-summary.html（用 templates/iteration-report.html 模板 + 朴素 str.replace 渲染）：
       - 占位符全清单 + 渲染规则见 references/iteration-report.md
       - 数据源：manifest.yaml + benchmark.json + grading.json[] + comparison.json[] + analysis.json[]
       - static 模式下 benchmark/comparison 数据缺失时用模板内置 fallback 文案渲染（不报错）
       - 单轮 transcript HTML escape 后塞进 <details>；超 5000 字截断
       - 落盘后 sanity check："{{" not in rendered_html

    【B】完整详细报告 detailed-report.html（调用 scripts/generate-full-report.mjs，每轮强制生成）：
       ```bash
       node .cursor/skills/skill-assistant/scripts/generate-full-report.mjs \
         <workspace>/iteration-N \
         <workspace>/iteration-N/detailed-report.html
       ```
       - 脚本内含 validate_eval_artifacts.py 前置校验 + 落盘后 3 项 sanity check
       - Step 6 菜单选 [1]/[3] 时**不重复生成**，直接复用本步产物（除非用户明确说"重跑报告"）

    完成后提示用户：两份报告路径 + [1] 在浏览器打开 detailed-report [2] 下一轮 [3] 收尾 [4] 看 manifest

    > **强制理由**：历史 iter-6 / iter-7 只落盘 report.md 而缺 HTML，事后补生成需用户二次指令——违背"每次评测都要有可归档的可视化产物"原则。static 模式同样需要 HTML（分数卡 + 诊断结论 + git diff 对用户同样有价值）。

    # 4.1.7 体积守门
    if 新 SKILL.md 体积 > 原始 × 1.5:
        拒绝提交，回 4.1.2 重做（要求精简方案，删冗余/合并重复）

# === 检查点：每个 Skill 优化完后人工确认 ===
展示该 Skill 的：
  1. git diff（改前 vs 改后）
  2. 各维度分数变化曲线
  3. 测试 prompt 输出对比（如跑过实测）
  4. 累计 Δ 分数
**STOP**：等用户确认 OK 才继续；用户说"不好" → 回滚到该 Skill 优化前版本（git reset 到分支 base）
```

#### 4.2 探索性重写（Phase 2.5 fallback）

当 hill-climbing 在 round 1 即 break（连续 1-2 个维度都涨不动）时，提议**一次** 探索性重写：

```
1. git stash 保存当前最优版本
2. 不微调，从结构和表达方式整体重新组织 SKILL.md
3. 重新执行 4.1.4 评估
4. if 重写版总分 > stash 版: 采用重写版（git stash drop）
   else: git stash pop 恢复
```

> 解决 hill-climbing 局部最优——有时需"先拆后建"才能突破瓶颈。**必须征得用户同意**后执行。

#### 4.3 results.tsv 格式

文件位置：`.skill-doctor/{skill-name}/results.tsv`

```tsv
timestamp	commit	skill	old_score	new_score	status	dimension	note	eval_mode
2026-04-27T15:00	baseline	target-skill	-	72	baseline	-	初始评估	full_test
2026-04-27T15:08	a1b2c3d	target-skill	72	78	keep	约束	补充 NEVER 列表 + 原因	full_test
2026-04-27T15:14	b2c3d4e	target-skill	78	77	revert	冗余	过度精简删错指令	dry_run
2026-04-27T15:20	c3d4e5f	target-skill	78	84	keep	指令	补充触发关键词	full_test
```

#### 4.4 异常 / 边界处理

| 场景 | 触发 | 处理 |
|---|---|---|
| 不在 git 仓库 | `git rev-parse` 失败 | 提示用户「建议 git init」；拒绝则用 `cp SKILL.md SKILL.md.bak.YYYYMMDD-HHMM` 文件备份代替 revert |
| results.tsv 损坏 | 列数不匹配 / 非 TSV | 备份为 `.bak.{timestamp}` 后重建表头，告知用户 |
| 分支已存在 | `git checkout -b` 失败 | 末尾加 `-2`/`-3`；第 3 次失败问用户「继续现有 / 新起」 |
| `git revert` 冲突 | 工作树脏 | `git stash` 重试；仍失败则从上一个 commit 取 SKILL.md 内容覆盖恢复 |
| MAX_ROUNDS 触顶 | 已跑 3 轮仍有短板 | 不强制 break，问用户「继续 +1 轮 / 进入 4.2 探索性重写 / 收工」 |
| 体积超 150% | 新 SKILL.md > 原 × 1.5 | 拒绝提交，回到 4.1.2 重做精简方案 |
| test-prompts.json 缺失 | Step 0 跳过 | 整个 Step 4 降级为 `eval_mode=structure_only`，仅做三维结构分迭代 |
| 子 Agent 不可用 | 超时 / 环境限制 | 维度评估降为 `dry_run`，标注后继续 |
| 三轮全 revert | 当前 Skill 已收敛或方向错 | break + 在最终报告标注「该 Skill 已达局部最优，建议人工介入」 |

> **原则**：异常先告知用户再按规则处理；绝不静默跳过或静默失败。

#### 4.5 优化策略库（融合 darwin-skill 的 P0-P3，按 Skill-Assistant 三维改造）

按优先级，每轮只做最高优先级的**一个**：

| 优先级 | 类型 | 典型问题 | 处方 |
|---|---|---|---|
| **P0** | 实测发现的效果偏差 | 测试输出偏离用户意图 / 带 Skill 比 baseline 还差 / 输出格式跑偏 | 检查误导性指令 / 是否过度约束 / 补输出模板 |
| **P1** | 指令缺位 | description 缺触发词 / 缺 Activate 类指令 / "When to use" 写错位置 | 补 description WHEN + 关键词 / 补"当 X 时使用 Y"句型 |
| **P1.5** | description 触发率可量化优化 | 触发率 < 60% / false positive 高 / description 写得啰嗦但击不中关键词 | 路由到 [Step 4.6 加速器](#step-46description-量化加速器v160-融合-skill-creator)：双路径 5 轮自动迭代，受 1024 字符硬约束 |
| **P2** | 约束缺位 | 缺 NEVER 列表 / 反模式描述模糊 / 缺边界条件 | 替换为具体 NEVER + WHY / 补 fallback 路径 |
| **P3** | 冗余过载 | 教程式解释 LLM 已知概念 / SKILL.md 与 references 内容重叠 / 过度工程文件 | 删基础解释 / 拆分到 references 并加触发器 / 删非 Agent 必需文件 |

#### Step 4.6：Description 量化加速器

**触发条件**：Step 4.1.1 锁定的本轮短板属于 P1.5（description 触发率），或用户明确说「优化 description / 提升触发率 / 跑加速器」。

**与 P1 的区别**：
- P1（手工改写）：主 Agent 凭经验补关键词、改 WHEN 句型，靠主 Agent 自评判断好坏
- P1.5（加速器）：用独立子 Agent N 次模拟 router 决策，在 train/test 上量化触发率（recall/precision），用迭代选优代替凭感觉

##### 4.6.1 准备测试集

```
1. 检查 {skill_dir}/trigger-queries.json 是否存在：
   - 不存在 → 进入设计阶段：生成 8-15 条覆盖 should_trigger / should_not_trigger / ambiguous 三类的查询，写入 trigger-queries.json，STOP 等用户确认
   - 已存在 → 展示给用户，问「复用 / 重写 / 追加」三选一
2. 检查触发集规模：< 5 条直接拒绝（统计意义不足），引导用户补充
3. 60/40 split：前 60% 为 train_set（用于优化反馈）、后 40% 为 test_set（用于"未见过的查询"评估）
```

##### 4.6.2 选路径

向用户展示菜单：

```
✨ Description 量化加速器 — 选择执行路径

  [A] 本地子 Agent 模拟（默认推荐，零依赖）
      → 主 Agent 在当前会话内 spawn 子 Agent N=3 次/query 模拟 router 决策
      → 跨 IDE 通用，不需要外部 CLI
      → 5 轮预算约 200-400 次子 Agent 调用，token 压力中

  [B] CLI 新进程·保真路径（可插拔 Provider，失败自动降级）
      → 通过 -p / --output-format / --max-turns 等同构参数启全新进程，重走真实 router 决策链
      → 这是 true trigger rate（生产环境真实激活率），不是 approximate
      → 已验证 Provider（共 3 个，-p / --system-prompt / --max-turns 全部实测通过）：
         · codebuddy ✅       （通用；v2.94.0 实测通过；npm i -g @tencent-ai/codebuddy-code, Node ≥ 18.20.8）
         · claude-internal ✅  （需 IOA 登录；v1.1.6 实测通过；iWiki:4015845000；注意：-p 模式追加 < /dev/null 可消除 stdin 等待）
         · claude             （Anthropic，海外账号；npm i -g @anthropic-ai/claude-code → claude login）
      → 环境快照中 CLI_CODEBUDDY / CLI_CLAUDE_INTERNAL / CLI_CLAUDE 任一为 available 时此选项默认高亮
      → 选用时让用户显式指定 Provider；不同 Provider 跨棘轮迭代时不混用（避免阈值漂移）
      → 推荐优先级：codebuddy（通用）> claude-internal（需 IOA 登录）> claude（海外账号）
      → 失败时按三级链自动降级：
           用户选择的 Provider 失败 → codebuddy → claude-internal → 路径 A 子 Agent
           （每级失败都明示原因；Node 版本不足中断整个链，让用户主动决策）

  [C] 跳过加速器，回到 P1 手工改写
```

环境快照见 [search.md Step 0.5 环境快照](search.md)；当所有已知 CLI Provider 都不可用时 `[B]` 仍可选——会自动降级到 `[A]` 并打 `→fallback:subagent_sim` 标，**绝不静默**。

##### 4.6.3 执行迭代

无论选哪条路径，**核心算法相同**（详见 [references/description-optimizer.md](../references/description-optimizer.md)）：

```
iter = 0
old_test_score = 在 test_set 上跑 baseline description 的综合分（recall + precision 均值）
while iter < 5:
    iter += 1

    # 4.6.3a 在 train_set 上识别失败案例
    failed_cases = 跑 train_set，找出 expected != actual 的 query

    # 4.6.3b 生成新 description（受 1024 字符硬约束）
    new_desc = 主 Agent 基于 failed_cases 重写 description
    if len(new_desc) > 1024:
        提示模型在 1024 字符内重写，最多重试 2 次
        if 仍 > 1024:
            主 Agent 强制截断 + 警告用户

    # 4.6.3c 在 test_set 上评估（关键：以 test 而非 train 决策）
    new_test_score = 跑 test_set 综合分

    # 4.6.3d 子棘轮决策
    if new_test_score > old_test_score（严格大于）:
        old_test_score = new_test_score
        best_description = new_desc
    else:
        记录 fail，连续 2 轮无改进 → break

# 4.6.3e 写回
SKILL.md frontmatter 的 description 替换为 best_description
git add SKILL.md && git commit -m "diagnose-iter: description-optimizer-{path}: trigger {old}→{new}"
```

##### 4.6.4 接回主棘轮

加速器产出 `best_description` 后，**仍然进入 Step 4.1.4 综合重评 + Step 4.1.5 棘轮决策**——综合分（含 darwin 风格的输出质量评测维度）必须严格 > 旧分才 keep。这保证 description 优化不破坏整体效果。

> **关键设计**：加速器不绕过主棘轮，只是在 description 这个细分维度上提供量化迭代器。最终的 keep/revert 仍由综合分裁决。

##### 4.6.5 results.tsv 新列

加速器执行时在 `eval_mode` 列后追加 `optimizer_path`：
- `manual`（手工改写）
- `subagent_sim`（路径 A 子 Agent 模拟，approximate trigger rate）
- `cli:<provider>`（路径 B CLI Provider 成功执行，true trigger rate；如 `cli:claude` / `cli:codebuddy`；旧 `claude_cli` 视同 `cli:claude`）
- `cli:<provider>→fallback:subagent_sim`（用户选了路径 B 但 Provider 启动/认证/超时失败，自动降级；本行数据是 approximate，不可与纯 cli 行作严格比较）
- `-`（非 description 维度迭代）

完整 schema + 降级触发条件 + 通知文案见 [references/description-optimizer.md](../references/description-optimizer.md) §CLI 失败降级规则 / §results.tsv 新列。

##### 4.6.6 异常 / 边界

| 场景 | 处理 |
|---|---|
| 路径 A 子 Agent 输出非 YES/NO | 容错正则 + 30% 解析失败时切路径 B 或人工介入 |
| 1024 字符两次重写仍超 | 强制截断 + 警告用户 review |
| test_set 反向下降 | 判定过拟合，回滚 baseline，记录 `status=overfit` |
| **路径 B Provider 命令不存在** | 自动降级路径 A，明示「⚠️ Provider 未安装，已降级 approximate trigger rate」+ 给安装命令；`optimizer_path` 标 `cli:<cmd>→fallback:subagent_sim` |
| **路径 B Provider 认证失败** | 自动降级路径 A，明示「⚠️ Provider 未认证，请先跑 `<login_cmd>`」+ 引导后续可手动重跑路径 B |
| **路径 B Provider 超时** | 先试备选 Provider（claude ↔ codebuddy）；全失败再降级路径 A，明示尝试结果 |
| **路径 B Node 版本不足** | 中断让用户主动决策：升级 Node（推荐 `nvm install 20`）/ 改用其他 Provider；目的是避免环境问题被静默掩盖 |
| 加速器涨幅 < 3 分 | 标注边际收益，建议改投资其他维度 |
| 同次 diagnose 内首次降级 | 输出长版降级提示（含原因、影响、修复建议）；后续重复降级压缩为单行 status |

详见 [references/description-optimizer.md](../references/description-optimizer.md) §异常 / 边界处理。

##### 4.6.7 NEVER

- **NEVER 不做 60/40 split** — 会过拟合训练措辞
- **NEVER 单次评估** — 子 Agent 单次输出方差大，至少 N=3
- **NEVER 把 SKILL.md body 投给路由模拟子 Agent** — 真实 router 只看 description
- **NEVER 改完不进主棘轮** — 加速器产出仍要进 Step 4.1.5 综合棘轮决策
- **NEVER 静默退化路径** — A/B 路径切换必须明示用户

### Step 5：迭代汇总报告

棘轮迭代结束后输出：

```markdown
## 优化报告 — {skill-name}

### 总览
- 迭代轮次：N（其中 keep X / revert Y / 探索性重写 Z）
- 实测验证：A 次 full_test / B 次 dry_run / C 次 structure_only
- 体积变化：{原始 lines} → {最终 lines}（{比例}%）

### 三维分数变化
| 维度 | Before | After | Δ |
|---|---:|---:|---:|
| 指令 (40%) | xx | xx | +x |
| 约束 (30%) | xx | xx | +x |
| 冗余率 (30%) | xx% | xx% | -x% |
| **效能分** | xx | xx | **+x** |

### 实测对比（如跑过 full_test）
| Test Prompt | Baseline 输出 | With-Skill 输出 | 提升评分 |
|---|---|---|---|
| #1 happy path | ... | ... | +X/10 |
| #2 复杂场景 | ... | ... | +X/10 |

### 主要改进
1. [指令] 补充了 description 触发词，可发现性提升明显
2. [约束] 加入 NEVER 列表 + WHY，反模式覆盖完整
3. ...

### 收敛状态
- ✅ 已达帕累托收敛（效能分 ≥ 80 且三维均不低于"中"）
- 或 ⚠️ 局部最优瓶颈（连续 N 轮无法改进，建议人工介入）
- 或 🔄 用户主动收工（达成预期目标）
```

### Step 6（必须执行）：报告与成果卡片

> ⚠️ **本步骤不可跳过**——无论是单次 diagnose 还是多轮棘轮收敛后，**都必须展示此菜单等待用户选择**。
> 直接结束而不展示此菜单 = 执行错误（对应 SKILL.md NEVER 规则）。
> 即使用户已明确说"不用报告 / 不需要 / skip"，也必须至少展示一次菜单 + STOP 等用户明确选 [4]。
>

Step 5 汇总报告输出后，**立即展示**以下菜单（含跨次对比提示）：

```
✨ 优化收尾 — 选择报告形式：

{IF prev_eval_exists:
  📈 检测到上次评测：{prev_score} 分（{prev_date} · {prev_eval_mode}）→ 本轮 {new_score} 分（趋势 {sign}{delta}）
  完整报告会自动渲染"上次 → 本次"对比图
}

  [1] 在浏览器打开完整 HTML 报告
      → 用户视角 8 章节（核心结论 / 必读建议 / 评分总览 / 测试覆盖 / 评分详情 / 测试数据 / 改动详情 / 评分标准）
      → 路径：<workspace>/iteration-N/detailed-report.html（每轮必存）
      → 仅触发 Start-Process / open 打开浏览器，<1 秒

  [2] 追加生成成果卡片 PNG（分享用）
      → PNG：分数对比 / 三维变化 / 关键改进 4 条
      → 输出位置：<workspace>/iteration-N/result-card-{timestamp}.png
      → 约 5-10 秒生成，2x 高清

  [3] [1] + [2] 都要（打开 HTML + 追加生成 PNG）

  [4] 不额外操作，直接结束（HTML 报告仍已落盘归档）
```

**STOP**：等用户明确输入 [1]/[2]/[3]/[4]。**用户说"不需要"/"不用"/"skip"等不算明确选择**——必须输出确认提示：

```
您说"不需要报告" — 这等同选 [4] 不生成，直接结束吗？
  [4] 是，结束本次评测       [1] 改主意，要完整报告
```

> **设计原则**：
> 1. **不可跳过**：即使用户表达过"不用"，也要给一次确认机会，避免后悔——很多用户事后想要报告归档却已结束会话
> 2. **"不需要" ≠ [4]**：自然语言"不需要"可能只是"现在不急"或"嫌慢"，必须显式 STOP 确认
> 3. **跨次提示前置**：用户决策前就让他知道"如果选 [1]，会看到上次 vs 本次的对比"，这往往会改变选择

**说明**：`detailed-report.html` 在 Step 4.1.6.5 每轮强制生成落盘，此处仅负责**打开**：

```powershell
# Windows
Start-Process "<workspace>/iteration-N/detailed-report.html"
# macOS
open <workspace>/iteration-N/detailed-report.html
```

若用户显式要求"重新生成/刷新报告"（非默认路径），才重新调用 `scripts/generate-full-report.mjs`，**严禁**主 Agent 自己拼接 HTML：

```bash
node .cursor/skills/skill-assistant/scripts/generate-full-report.mjs \
  <workspace>/iteration-N \
  <workspace>/iteration-N/detailed-report.html
```

脚本内部会：
1. 读取 `templates/full-report.html` 模板（含 `{{EVAL_CONTENT}}` / `{{NEVER_CHECKS}}` / `{{TREND_ROWS}}` 等占位符）
2. 从以下来源收集数据并替换占位符：
   - `<workspace>/iteration-N/diagnosis/diagnosis-report.md`（Step 1 产物）
   - `git diff` HEAD~1..HEAD（实际改动）
   - `<workspace>/results.tsv`（分数走势）
   - `<workspace>/iteration-N/benchmark.json`（dynamic/hybrid 时存在，eval 统计）
   - `<workspace>/iteration-N/eval-*/grading.json`（dynamic / hybrid / **dry_run** 时存在，逐条 eval 打分；dry_run 落盘要求见 4.1.4.c）
   - `<workspace>/iteration-N/comparison.json`（blind_hybrid 时存在）
   - `manifest.yaml`（元数据 / session 信息）
3. 生成自包含 HTML（无外部依赖，可离线查看）
4. 完成后 `open` 自动打开

**主 Agent 落盘后强制做一次 sanity check**：
- ✅ `eval-*/grading.json` 至少存在 1 个（任何非 `static` 模式都该有）
- ✅ 渲染产物中无残留的 `{{` 或 `}}` 占位符
- ✅ 渲染产物中包含 `eval-card` 或"static 模式"明确说明文本之一
- 任一不通过 → 不交付报告，回到 4.1.4.c 补落盘后重跑脚本

> **绝对禁止**：用 Write 工具直接拼接 HTML 输出绕过 `generate-full-report.mjs`——这会跳过 `{{EVAL_CONTENT}}` 注入和 sanity check，必然导致 Eval 章节空洞。手写 HTML 仅在脚本本身报错（如 Node 不可用）且已记入 `results.tsv` 异常行后才允许，且必须以 `templates/full-report.html` 为母版手工替换全部占位符（不能从零写）。

**选 [2] 或 [3] 时** — 调用 `scripts/render-card.mjs`（现有流程）

详细生成流程见 [references/result-card.md](../references/result-card.md) 和 [references/full-report.md](../references/full-report.md)。

> detailed-report.html 每轮强制落盘到 workspace，**不污染** skill 目录；PNG 成果卡片仍为按需生成（耗时更长）。无论用户选哪项，HTML 报告都已归档，事后随时可打开。

---

## 常见病症库（9 种失败模式）

诊断时对照以下常见病症，快速定位问题根因：

| 病症 | 症状 | 根因 | 处方 |
|------|------|------|------|
| **教程病** | 解释 LLM 已知的基础概念 | 误把 Skill 当教学，Expert 知识 < 30% | 删除所有基础解释，只保留专家知识增量 |
| **堆砌病** | SKILL.md 800+ 行无拆分 | 缺乏渐进式披露设计 | body 保留路由和决策树（≤ 300 行），详情移入 references/ |
| **孤儿引用** | references/ 存在但从未被加载 | 缺加载触发器 | 在工作流决策点添加 "MANDATORY — READ ENTIRE FILE" |
| **清单流程** | Step 1/2/3 纯机械步骤 | 缺思维框架，只有操作没有思考 | 转化为 "Before doing X, ask yourself..." 框架 |
| **模糊警告** | "注意错误""小心边界" | 反模式不具体，缺踩坑经验 | 替换为具体 NEVER 列表 + WHY |
| **隐身病** | 内容好但从不被激活 | description 差，缺 WHEN 和关键词 | 重写 description：WHAT + WHEN + KEYWORDS |
| **错位触发** | "When to use" 写在 body | 误解三层加载系统 | 移到 description 中 |
| **过度工程** | README/CHANGELOG/CONTRIBUTING 齐全 | 把 Skill 当软件项目 | 删除所有 Agent 不需要的文件 |
| **自由度错配** | 创意任务用死板脚本 | 未校准任务风险 | 创意→原则框架，脆弱→精确脚本 |

---

## 诊断反模式

- **安全评分陷阱**：给所有 Skill 默认 60-70 分。应严格评分，敢于给高分或低分
- **误判知识注入**：把认知型 Skill 的背景知识当冗余删掉（用知识三分法区分 Expert vs Redundant）
- **越步执行**：在 Step 1 就给出具体重构代码
- **忽视重叠**：不检查 SKILL.md 与 references/ 的内容重复
- **单维偏见**：只关注冗余消减而忽略指令和约束
- **强行优化陷阱**：对已收敛的 Skill 仍进入 Step 2/3
- **自评偏差**：在同一上下文里"改完直接评"——必须用独立子 Agent 跑实测维度，否则容易把"自我说服"当成改进
- **静默 revert**：棘轮回滚后不在 results.tsv 记录失败原因，导致下次还撞同一个坑
- **跳过 Step 0**：没设计 test-prompts.json 就直接进 Step 4，等于关掉了实测维度的反馈回路

**优化优先级**：指令不足 > 约束不足 > 冗余过多

---

## 同步主 SKILL.md 的能力声明

### 模块概览

诊断模块基于 Prompt 效能模型 + **棘轮迭代闭环（融合 darwin-skill + skill-creator）**：
- 三维效能分（指令 40% / 约束 30% / 冗余 30%）
- Step 0 测试 prompt 设计 → Step 1-3 一次性诊断 + 重构 → **Step 4 棘轮迭代（评估 → 改进 → 实测 → 保留/回滚 + Step 4.6 description 量化加速器）→ Step 5 汇总报告 → Step 6 成果卡片**
- 子 Agent 独立评分避免自评偏差，git revert 棘轮防止退步，体积守门防越改越臃肿
- Step 0 / Step 4.1.4 双跑机制被 inspect 的 `eval_mode=dynamic/hybrid` 复用
- 触发词："优化 skill"、"诊断 skill"、"迭代到收敛"、"自动优化"、"棘轮"、"darwin"、"达尔文"、"成果卡片"、"出张图"、"优化 description"、"提升触发率"、"跑加速器"、"trigger eval"、"用 codebuddy 跑加速器"、"换 CLI provider"、"CLI 失败降级"、"approximate trigger rate"、"true trigger rate"
