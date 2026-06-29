# 工作区目录规范

> 让 diagnose / inspect / 加速器的所有产物有**统一、可定位、可清理**的落盘位置；让"工作区"成为 skill-assistant 的一等公民概念，不再临时拼路径。

---

## 核心原则

1. **数据集中**：一个 `skill-assistant-workspace/` 容器装下所有评测产物，不污染被评测 skill 自身目录、不污染项目根
2. **按 skill 隔离**：容器下每个被评测 skill 占一个同名子目录
3. **跟随 skill 容器**：workspace 紧贴被评测 skill 所在的 skills 容器，方便就近查看 + 自然 .gitignore 共用
4. **配置可覆盖**：默认策略适合大多数场景，高级用户可在 `config/sources.yaml` 改写为 `external` 集中或 `project_local` 项目内
5. **可恢复**：每个评测会话有 `manifest.yaml`，中断后可续跑；`session_lock` 防并发

---

## 三种工作区布局策略

| 策略名 | 路径模板 | 默认？ | 适用场景 |
|---|---|---|---|
| **`sibling_of_skills_dir`**（默认推荐） | `<被评测 skill 父目录的同级>/skill-assistant-workspace/<skill-name>/` | ✅ | 大多数 IDE Skill 评测——workspace 就在 `.cursor/skills/` 隔壁，路径短、易看 |
| `external` | `~/.skill-assistant/workspaces/<skill-name>-workspace/` | — | 跨多机器同步评测产物 / 想完全独立于源代码仓库 |
| `project_local` | `<当前项目根>/.skill-doctor/<skill-name>/` | — | 评测产物希望随项目走（仍要 .gitignore） |

### 默认策略下的实际路径示例

被评测 skill 位置 | 解析得到的 workspace 路径
---|---
`.cursor/skills/english-exam-writing-reviewer/` | `.cursor/skills/skill-assistant-workspace/english-exam-writing-reviewer/`
`~/.cursor/skills-cursor/babysit/` | `~/.cursor/skills-cursor/skill-assistant-workspace/babysit/`
`/Users/me/proj/.codebuddy/skills/foo/` | `/Users/me/proj/.codebuddy/skills/skill-assistant-workspace/foo/`
`tmp/audit_diagnose/darwin-skill/` | `tmp/audit_diagnose/skill-assistant-workspace/darwin-skill/`

> **解析规则**：取被评测 skill 路径的**父目录**（即 skills 容器目录），在该容器下创建 / 复用 `skill-assistant-workspace/` 子目录，再在其中按 skill 名建子目录。**不是**在被评测 skill 目录内建 workspace（那会污染）。

### 路径解析伪代码

```python
def resolve_workspace_path(skill_path: Path, layout: str = "sibling_of_skills_dir",
                            config: dict | None = None) -> Path:
    """根据布局策略解析 workspace 绝对路径。

    layout = "sibling_of_skills_dir": skill 父目录同级
    layout = "external":              ~/.skill-assistant/workspaces/<name>-workspace/
    layout = "project_local":         <repo_root>/.skill-doctor/<name>/
    """
    skill_name = skill_path.name
    skills_container = skill_path.parent  # 例：.cursor/skills/

    if layout == "sibling_of_skills_dir":
        return skills_container / "skill-assistant-workspace" / skill_name
    elif layout == "external":
        root = Path(config.get("workspace_root", "~/.skill-assistant/workspaces")).expanduser()
        return root / f"{skill_name}-workspace"
    elif layout == "project_local":
        repo_root = find_git_root(skill_path) or Path.cwd()
        return repo_root / ".skill-doctor" / skill_name
    else:
        raise ValueError(f"未知 workspace.layout: {layout}")
```

---

## 标准目录结构

```
<skills_container>/skill-assistant-workspace/
├── .gitignore                      # 自动生成，默认忽略全部产物（manifest.yaml 之外）
├── README.md                       # 自动生成，说明这是 skill-assistant 工作区
├── english-exam-writing-reviewer/
│   ├── manifest.yaml               # 元数据 + 当前 iteration 指针 + session_lock
│   ├── trigger-queries.json        # 触发率测试集
│   ├── test-prompts.json           # 共享测试集（输出质量）
│   ├── skill-snapshot/             # 优化前完整 cp -r 快照（独立于 git）
│   │   └── ...                     # 整个 skill 的 SKILL.md + references 等
│   ├── iteration-1/
│   │   ├── config.yaml             # 该轮特有配置（eval_mode / cli_provider / N_repeats）
│   │   ├── eval-cet4-news/         # 描述性命名（来自 test-prompts.json 的 scenario 字段）
│   │   │   ├── baseline/outputs/
│   │   │   ├── with_skill/outputs/
│   │   │   ├── transcript.md       # 子 Agent 完整 transcript
│   │   │   ├── timing.json
│   │   │   ├── grading.json        # schema：passed_count/total_count/expectations[]，详见 sub-agent-protocol.md
│   │   │   └── eval_metadata.json   # 字段：eval_name/scenario/prompt_id/prompt/priority/functional_module/scope
│   │   ├── eval-postgrad1b-cartoon/
│   │   ├── benchmark.json          # aggregate（mean/stddev/min/max，N 重复后的统计）
│   │   ├── trigger-eval.json       # 加速器路径 A/B 触发率结果（含 fidelity 字段）
│   │   ├── iter-summary.html       # 单轮摘要报告
│   │   └── feedback.json           # 用户反馈（下轮自动 carry over）
│   ├── iteration-2/                # 同上结构
│   ├── results.tsv                 # 全部历史日志（11 列）
│   ├── final-report.html           # Step 5 汇总
│   └── final-card.png              # Step 6 成果卡片
├── huashu-proofreading/            # 另一个被评测 skill 的子目录
└── batch-baseline-2026-04-28/      # mode=batch_baseline 的扫描结果
    └── leaderboard.json
```

### 各文件用途速查

| 文件 / 目录 | 用途 | 谁写谁读 |
|---|---|---|
| `manifest.yaml` | 工作区元数据 + 当前进度指针 | diagnose 写 / setup 读 / resume 读 |
| `trigger-queries.json` | description 触发率测试集 | inspect 引导用户写 / 加速器读 |
| `test-prompts.json` | 输出质量测试集 | diagnose Step 0 引导用户写 / Step 4.1.4 读 |
| `skill-snapshot/` | 优化前完整快照 | diagnose Step 1 写 / 失败回滚读 |
| `iteration-N/config.yaml` | 该轮配置（不污染主 manifest） | 棘轮每轮开头写 |
| `iteration-N/eval-XX/` | 单条测试用例的所有产物 | 子 Agent 写 / grader 读 |
| `iteration-N/eval-XX/eval_metadata.json` | 单 case 元数据（priority / functional_module / prompt） | 主 Agent 写 / 报告 ⑥ 段渲染读 |
| `iteration-N/eval-XX/<role>/run-K/grading.json` | 逐条 expectation 评分 | 子 Agent / dry_run 主 Agent 写·schema 见 sub-agent-protocol.md |
| `iteration-N/eval-XX/<role>/run-K/outputs/report.md` | baseline / with_skill 输出 | 子 Agent / dry_run 主 Agent 写·首行须含 dry_run 标记 |
| `iteration-N/analysis.json` | D 维度评分镜像（喂报告雷达图） | inspect 收尾 / diagnose 4.1.5 写 / 报告读 |
| `iteration-N/comparison.json` | Comparator 盲评聚合（含 winner / anon_mapping） | Comparator 子 Agent 写 / 报告读 |
| `iteration-N/benchmark.json` | N 重复跑统计聚合 | aggregate 脚本写 / Step 4.1.5 决策读 |
| `iteration-N/trigger-eval.json` | 加速器触发率结果 | 加速器写 / 决策读 |
| `iteration-N/iter-summary.html` | 单轮摘要 HTML 报告| 4.1.6.5 自动写 / 用户看 |
| `iteration-N/detailed-report.html` | 完整详细 HTML 报告| Step 6 [1] 用户主动触发 / 用户看 |
| `iteration-N/feedback.json` | 用户反馈 | UI 写 / 下轮 prompt 读 |
| `results.tsv` | 全部历史扁平日志 | 每轮决策后追加 |
| `final-report.html` | 收尾汇总 | Step 5 写 |
| `final-card.png` | 成果卡片 | Step 6 写（按需） |

---

## `.gitignore` 自动生成策略

`auto_gitignore: true`（默认开启）时，初始化 workspace **首次创建** `skill-assistant-workspace/` 目录会同时生成：

```gitignore
# Auto-generated by skill-assistant — DO NOT manually edit
# 默认忽略所有评测产物，仅保留共享测试集和 manifest 元数据

# 大目录全部忽略
*/iteration-*/
*/skill-snapshot/
*/final-card.png
*/results.tsv
batch-baseline-*/

# 但保留共享测试集与 manifest
!*/manifest.yaml
!*/trigger-queries.json
!*/test-prompts.json
```

> **设计意图**：测试集是有沉淀价值的资产（应该 commit 让团队共享）；评测产物量大且与具体环境相关（不应入库）；manifest 是元数据可入库便于事后回溯。

> 用户可手动改写本文件以保留更多产物——`auto_gitignore` 仅控制初次生成。

---

## 跨 skill 比较 / batch_baseline

`mode=batch_baseline`扫描所有已装 skill 时，产物落在：

```
<skills_container>/skill-assistant-workspace/batch-baseline-<timestamp>/
├── leaderboard.json                # 排行榜（按分数从低到高 + 共性问题 TOP N）
├── per-skill/
│   ├── english-exam-writing-reviewer.json
│   └── ...
└── iter-summary.html
```

不进入按 skill 隔离的子目录——它本身就是跨 skill 视角的产物。

---

## 配置项

`config/sources.yaml` 的 `preferences.workspace` 段：

```yaml
preferences:
  workspace:
    # 工作区布局策略，三选一
    # sibling_of_skills_dir：默认；放在被评测 skill 父目录的同级 skill-assistant-workspace/
    # external:              ~/.skill-assistant/workspaces/<skill>-workspace/
    # project_local:         <当前项目根>/.skill-doctor/<skill>/
    layout: sibling_of_skills_dir

    # 仅 layout=external 时生效：workspace 根目录
    workspace_root: ~/.skill-assistant/workspaces

    # 保留多少代历史
    # all     — 全保留（推荐，磁盘便宜，归因可追溯）
    # last_N  — 仅保留最近 N 代（如 last_5）
    keep_iterations: all

    # 旧代是否压缩（节省磁盘；保留 last_3 不压缩，更早代压缩为 .tar.gz）
    compress_old_iterations: true

    # 自动生成 .gitignore（首次创建 workspace 时）
    auto_gitignore: true

    # 共享测试集复用（同 skill 跨棘轮迭代是否复用 test-prompts.json / trigger-queries.json）
    shared_test_sets: true

    # 是否启用 session_lock（多窗口并发 diagnose 防撞车）
    session_lock_enabled: true

    # session_lock 的过期时间（小时，避免崩溃后永远锁住）
    session_lock_timeout_hours: 4
```

### 默认值合理性

| 字段 | 默认 | 为什么 |
|---|---|---|
| `layout` | `sibling_of_skills_dir` | Q1 用户决策；workspace 紧贴 skill，路径直观 |
| `keep_iterations` | `all` | Q2 用户决策；归因可追溯优先于磁盘 |
| `compress_old_iterations` | `true` | 平衡历史保留与磁盘占用，最近 3 代不压缩，更早代 tar.gz |
| `auto_gitignore` | `true` | 防止用户误把 ~MB 评测产物 commit 入库 |
| `shared_test_sets` | `true` | 测试集是沉淀资产，跨棘轮复用 |
| `session_lock_enabled` | `true` | 多 IDE 窗口同跑会互相覆盖文件 |
| `session_lock_timeout_hours` | `4` | 长 diagnose 不应超过 4h；过期可强制解锁 |

---

## 工作区初始化流程

由 `modules/diagnose.md` 在 Step 0 调用：

```
1. 解析 workspace 路径 = resolve_workspace_path(skill_path, layout=preferences.workspace.layout)
2. 检查路径是否存在
   ├─ 不存在 → 创建目录树 + 写 README.md + 写 .gitignore（如 auto_gitignore=true）+ 写 manifest.yaml
   └─ 已存在 → 读 manifest.yaml
       ├─ session_lock 有效 + pid 存活 → 阻断："另一个会话正在运行（pid=X，开始于 Y），是否强制接管？"
       ├─ session_lock 过期（> session_lock_timeout_hours）→ 自动清锁 + 提示用户
       ├─ session_lock 不存在但 status=in_progress + 有未完成 iteration → 提示"检测到未完成的 iteration-N，是否续跑？"
       └─ status=completed → 询问"沿用现有 workspace 还是新起一轮？"
3. 写入 / 更新 session_lock
4. 进入正常 diagnose 流程
```

详细 manifest schema 见 [manifest-schema.md](./manifest-schema.md)。

---

## 边界 / 异常处理

| 场景 | 处理 |
|---|---|
| 被评测 skill 路径不可写（read-only） | 不影响 workspace（workspace 在父目录的 sibling，与 skill 是否可写无关） |
| 父目录不可写（如评测全局 skill `~/.cursor/skills-cursor/`） | 自动 fallback 到 `external` 布局，写 `~/.skill-assistant/workspaces/`，明示用户 |
| skill 在 `/tmp/` 等临时位置 | 仍按 sibling 解析（`/tmp/skill-assistant-workspace/`），但 manifest 标 `volatile=true` 警示用户 |
| 同一 skill 被两个 IDE / 两个 skills 容器同时安装 | 各容器独立 workspace，不混淆（每个 skills 容器有自己的 sibling） |
| skill 路径含中文 / 空格 | 路径透明承载，但 .gitignore / 脚本调用时必须用引号包裹（已在伪代码中体现） |
| workspace 目录被外部进程占用（其他工具误写） | session_lock 检测；冲突时让用户决定接管 / 让出 |
| 磁盘空间不足 | 写 manifest / .gitignore 失败时立即中止 diagnose，明示用户清理 |
| 用户改变 layout（中途改 sibling → external） | 不自动迁移（保留旧路径 + 新路径并行，避免数据丢失），明示用户手动 mv |

---

## NEVER（工作区设计自身约束）

- **NEVER 把评测产物落到被评测 skill 目录里** — 那会污染源文件、影响 git 状态、混淆"原 skill"和"评测产物"
- **NEVER 在没有 manifest.yaml 的情况下进入 diagnose** — 进入前必须初始化或读取已有 manifest
- **NEVER 跳过 session_lock 检查** — 多窗口并发会损坏 results.tsv 和 iteration 数据
- **NEVER 静默改变工作区路径** — `layout` 配置项变化必须明示用户旧路径在哪，避免找不到历史数据
- **NEVER 自动删除旧 iteration**（即使 `keep_iterations=last_5`） — 应压缩 + 移到 `archive/` 子目录，让用户决定何时彻底删
- **NEVER 把凭证 / API Key 写到 workspace** — 凭证只在 `config/.credentials.yaml`，workspace 是评测产物专用

---

## 与既有概念的关系

| 既有概念 | 关系 |
|---|---|
| `_skill_meta.json`（每个已装 skill 的元数据） | 不变，仍在 skill 目录下；workspace 是评测产物，与元数据正交 |
| `results.tsv`（darwin 棘轮历史） | 从 `.claude/skills/darwin-skill/results.tsv` 移到 `<workspace>/<skill>/results.tsv`——按被评测 skill 隔离，不再共享单文件 |
| `.skill-doctor/` | 弃用——已不再使用，检测到时提示用户迁移到新 workspace 路径 |
| `_runtime/`（其他 skill 偶尔用的运行时目录） | 不冲突；workspace 专为 skill-assistant 评测产物 |
| install 模块 | install 写入 skill 目录；workspace 由 diagnose / inspect 写入；分工清晰 |

---

## 旧版迁移策略

如果你之前用 `.skill-doctor/<skill>/` 临时方案：

1. 第一次跑 diagnose 时检测到 `.skill-doctor/<skill>/` → 提示用户「检测到旧版本评测产物，是否迁移到新 workspace？」
2. 用户同意 → `mv .skill-doctor/<skill>/* <new_workspace>/<skill>/`
3. 用户拒绝 → 新 workspace 从空开始，旧 `.skill-doctor` 不动

> **不强制迁移**——尊重用户选择；但提示频率每次 diagnose 提一次（直到迁移或显式拒绝）。

---

## 相关文档

- manifest.yaml schema：[manifest-schema.md](./manifest-schema.md)
- diagnose 模块工作区初始化：详见 `modules/diagnose.md` Step 0
- setup 引导工作区选择：详见 `modules/setup.md` Step 4
- 加速器触发率落盘格式：[description-optimizer.md](./description-optimizer.md) §results.tsv 新列
