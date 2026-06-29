# manifest.yaml Schema

> 评测会话的"账本"：记录工作区元数据、当前迭代指针、session_lock，让 diagnose / inspect / 加速器可中断、可续跑、可并发安全。

---

## 文件位置

```
<workspace>/<skill-name>/manifest.yaml
```

每个被评测 skill 一份，由 `modules/diagnose.md` Step 0 初始化或读取。

---

## 完整 Schema

```yaml
# ============================================================
# skill-assistant manifest — DO NOT manually delete
# ============================================================

# ── 元数据 ──
manifest_version: "1.0"               # schema 版本，用于未来兼容性
skill_assistant_version: "2.0.0"      # 创建时的 skill-assistant 版本
created_at: "2026-04-28T15:30:00+08:00"
updated_at: "2026-04-28T17:42:00+08:00"

# ── 被评测 skill 信息 ──
skill:
  name: "english-exam-writing-reviewer"
  path: ".cursor/skills/english-exam-writing-reviewer"   # 相对当前 cwd / 或绝对路径
  version: "1.0.0"                    # 来自 SKILL.md frontmatter
  initial_commit: "a1b2c3d"           # 进入 workspace 时 skill 所在仓库的 HEAD
  initial_skill_hash: "sha256:..."    # skill 目录内容 hash（用于检测外部修改）
  source:                             # 来自 _skill_meta.json（可空）
    type: "github"
    repo: "user/repo"
    path: "skills/english-exam-writing-reviewer"

# ── 工作区配置 ──
workspace:
  layout: "sibling_of_skills_dir"     # sibling_of_skills_dir / external / project_local
  absolute_path: "/Users/me/proj/.cursor/skills/skill-assistant-workspace/english-exam-writing-reviewer"
  shared_test_sets: true              # 是否复用同 skill 的 test-prompts.json / trigger-queries.json
  keep_iterations: "all"              # all / last_N
  compress_old_iterations: true

# ── 评测会话状态 ──
status: "in_progress"                 # initialized / in_progress / paused / completed / aborted
mode: "diagnose"                      # diagnose / inspect / batch_baseline / accelerator_only

# ── 当前迭代指针 ──
current_iteration: 3
max_iterations: 5                     # darwin 棘轮上限

iterations:
  - id: 1
    started_at: "2026-04-28T15:31:00+08:00"
    completed_at: "2026-04-28T16:05:00+08:00"
    status: "completed"
    decision: "improved"              # improved / regressed / unchanged
    score_before: 72
    score_after: 78
    short_board: "D2"
    strategy_id: "P2.1"
    notes: "补充 prompt injection 防御"

  - id: 2
    started_at: "2026-04-28T16:08:00+08:00"
    completed_at: "2026-04-28T16:50:00+08:00"
    status: "completed"
    decision: "regressed"
    score_before: 78
    score_after: 75
    short_board: "D2"
    strategy_id: "P2.4"
    notes: "策略过度，已 git revert"
    reverted_to: "iteration-1"

  - id: 3
    started_at: "2026-04-28T17:00:00+08:00"
    completed_at: null
    status: "in_progress"
    short_board: "D10.2"
    strategy_id: "P1.5"               # description 量化加速器
    notes: "通过加速器路径 B 优化触发率"
    accelerator:
      path: "B"                       # A / B
      provider: "claude-internal"     # claude / codebuddy / claude-internal
      fidelity: "true_trigger_rate"   # approximate_trigger_rate / true_trigger_rate
      fallback_used: false

# ── 评测配置（影响所有 iteration 的全局选项）──
evaluation:
  eval_mode: "hybrid"                 # static / hybrid / dynamic / blind_hybrid / preview / structure_only
  # ⚠️ eval_mode 是权威源（generate-full-report.mjs 优先读这里）。
  # 如果你只在 iterations[].eval_mode 写而不在 evaluation.eval_mode 写，
  # 未在此处写 eval_mode 的旧版本会 fallback 到 'static'，导致报告 ⑥ 段空白。
  # 推荐两处都写一致——iterations[].eval_mode 是历史快照；evaluation.eval_mode 是当前权威。
  N_repeats: 3                        # 同一 prompt 重复跑次数
  fidelity_mode: "subagent_default"   # subagent_default / cli_fresh_process
  cli_provider:                       # 加速器路径 B 偏好的 provider
    primary: "claude-internal"
    fallback_chain: ["claude", "codebuddy"]
  test_set_split:
    train_ratio: 0.6                  # description 加速器 train/test split
    seed: 42                          # 可复现
  time_budget:                        # 按 eval_mode 默认值见 references/time-budget.md
    soft_deadline_seconds: 480        # 8 min（hybrid 默认）
    hard_deadline_seconds: 720        # 12 min（hybrid 默认）
    started_at: "2026-04-29T15:30:00+08:00"
    elapsed_checkpoints: []           # 每完成 scenario 追加 { scenario_id, completed_at, elapsed_s }
    soft_exceeded_action: null        # 用户在 soft 菜单选的 a/b/c/d/e
    hard_exceeded_action: null        # 自动降级时填入策略名，例如 "switch_to_dry_run_for_remaining"

# ── session_lock ──
# 防止多窗口 / 多 IDE 同时评测同一 skill
session_lock:
  enabled: true
  pid: 78342                          # 当前持有锁的进程 pid（agent 启动时写入）
  hostname: "MacBook-Pro.local"
  ide: "cursor"                       # cursor / codebuddy / cli / other
  acquired_at: "2026-04-28T17:00:00+08:00"
  expires_at: "2026-04-28T21:00:00+08:00"   # acquired_at + session_lock_timeout_hours
  user_note: ""                       # 可选：让用户标注本次评测意图

# ── 测试集状态 ──
test_sets:
  test_prompts:
    path: "test-prompts.json"         # 相对 manifest 所在目录
    exists: true
    last_modified: "2026-04-28T15:25:00+08:00"
    scenario_count: 4
    sha256: "..."                     # 用于检测中途篡改
  trigger_queries:
    path: "trigger-queries.json"
    exists: true
    last_modified: "2026-04-28T15:25:00+08:00"
    should_trigger_count: 5
    should_not_trigger_count: 4
    ambiguous_count: 3
    sha256: "..."

# ── skill 快照 ──
skill_snapshot:
  path: "skill-snapshot/"
  created_at: "2026-04-28T15:30:30+08:00"
  size_bytes: 245678
  files: 12

# ── 历史结果 ──
results_tsv:
  path: "results.tsv"
  rows: 2                             # 每个完成的 iteration 写一行
  schema_version: "current"            # 含 optimizer_path 列

# ── 用户反馈累积 ──
feedback_history:
  - iteration: 1
    timestamp: "2026-04-28T16:06:00+08:00"
    accepted: true
    notes: "改进合理，继续"
  - iteration: 2
    timestamp: "2026-04-28T16:51:00+08:00"
    accepted: false
    notes: "回退；过度修改了 SKILL.md description 字段"

# ── 退出 / 失败原因（status = aborted 时填写）──
abort_reason: null                    # 例："user_cancel" / "session_lock_conflict" / "disk_full"
abort_details: null
```

---

## 字段约束

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `manifest_version` | string | ✅ | 当前固定 `"1.0"` |
| `skill.path` | string | ✅ | 优先存相对路径（便于跨机器同步），无法相对化时存绝对路径 |
| `skill.initial_skill_hash` | string | ✅ | sha256 + 16 进制；用于检测 workspace 复用时 skill 是否被外部改动 |
| `status` | enum | ✅ | `initialized` / `in_progress` / `paused` / `completed` / `aborted` |
| `current_iteration` | int | ✅ | 0 = 未开始；1+ 表示当前正在或刚完成的 iteration |
| `iterations[].decision` | enum | — | `improved` / `regressed` / `unchanged`；in_progress 时为 null |
| `session_lock.expires_at` | ISO8601 | ✅ if enabled | 用于自动过期清理 |
| `session_lock.pid` | int | ✅ if enabled | 检测进程是否仍存活的依据 |
| `evaluation.N_repeats` | int | — | 默认 1；推荐 3 |
| `evaluation.eval_mode` | enum | ✅ | `static` / `hybrid` / `dynamic` / `blind_hybrid` / `preview`。**权威源**——`generate-full-report.mjs` 按 `evaluation.eval_mode → iterations[id=N].eval_mode → 'static'` 顺序解析；只在 iterations 里写会被旧脚本读不到。 |

---

## session_lock 生命周期

```
┌─────────────────────────────────────────────────────────────┐
│ Step 0: diagnose 启动                                        │
│   ├─ manifest 不存在     → 创建 + 写 lock + 进入             │
│   └─ manifest 存在       → 读 session_lock                   │
│       ├─ enabled=false   → 跳过锁检查 + 写 lock + 进入       │
│       ├─ pid 不存活       → 视为崩溃残留 + 强夺锁 + 进入        │
│       ├─ now > expires_at → 视为过期 + 清锁 + 进入             │
│       └─ pid 存活 + 未过期 → 阻断（让用户决策）                  │
│                                                             │
│ Step N: 每次写 manifest 前刷新 expires_at                    │
│                                                             │
│ Step Final: 正常退出 / aborted                               │
│   └─ session_lock.pid = null + status 更新                  │
└─────────────────────────────────────────────────────────────┘
```

### 锁冲突时的用户菜单

```
检测到工作区已被另一个会话锁定：
  pid: 78342  hostname: MacBook-Pro.local  ide: cursor
  acquired_at: 2026-04-28T17:00 (2 小时前)
  expires_at:  2026-04-28T21:00 (还剩 2 小时)

请选择：
  A. 强制接管（终止旧会话，本次接管）
  B. 等待（每 30 秒重试一次，最多 5 次）
  C. 放弃本次 diagnose
```

---

## resume 流程

进入 diagnose 时检测到 `status=in_progress` 且当前无活锁：

```
检测到上次会话未完成：
  current_iteration: 3
  上次中断时间: 2026-04-28T17:42 (5 分钟前)
  iteration-3 状态: 子 Agent 评估完成，等待棘轮决策
  abort_reason: null（疑似 IDE 崩溃）

请选择：
  A. 续跑（从 iteration-3 棘轮决策步继续）
  B. 丢弃 iteration-3 重跑
  C. 关闭本次会话（不修改 manifest）
```

resume 时复用：
- ✅ `iteration-N/` 目录已有的 baseline / with_skill 输出
- ✅ `iteration-N/grading.json`、`benchmark.json`
- ✅ `feedback_history` 全部
- ❌ 不复用 `session_lock`（必须重新获取）

---

## 并发安全

| 场景 | 策略 |
|---|---|
| 同 IDE 两个窗口都跑同一 skill | session_lock 阻断后者，菜单提示 |
| 不同 IDE（Cursor + CodeBuddy）跑同一 skill | 同上；锁不区分 IDE，先到先得 |
| 同时跑两个不同的 skill | 互不影响（各自独立 manifest） |
| `mode=batch_baseline` 与单 skill diagnose 并发 | 各自独立目录（`batch-baseline-<ts>/` vs `<skill>/`），不冲突 |
| 写 manifest 时进程崩溃 | 使用临时文件 + atomic rename；保证 manifest 始终是有效 yaml |

### atomic write

> 历史教训：曾多次因主 Agent 直接 `path.write_text(yaml.dump(data))` 在 IDE 崩溃 / Ctrl-C 时机不当导致 `manifest.yaml` 残留半截 yaml，下次 resume 直接 YAML 解析失败。**任何写 manifest 的入口必须用 atomic 方式**——直写 = bug。

**统一 helper（推荐）**：`scripts/manifest_io.py` 提供 `write_manifest_atomic(path, data)` / `read_manifest_safe(path)`，主 Agent 调脚本即可，不允许内联 `write_text`。

**底层语义**（无脚本环境时主 Agent 复刻）：

```python
def write_manifest_atomic(path: Path, data: dict) -> None:
    """原子写：先写 .tmp，fsync，再 POSIX rename，保证读到的 manifest 始终是完整 yaml。"""
    import os, yaml
    tmp = path.with_suffix(".yaml.tmp")
    payload = yaml.safe_dump(data, allow_unicode=True, sort_keys=False)
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(payload)
        f.flush()
        os.fsync(f.fileno())          # 强制刷盘后才 rename，避免断电半写
    tmp.replace(path)                 # POSIX rename 原子
```

**调用约束**：

1. **每次刷新都走 atomic**——包括 session_lock 的 expires_at 续命、iterations 追加、time_budget.elapsed_checkpoints 追加，都不允许 in-place 编辑
2. **写前必读**：`current = read_manifest_safe(path); current.update(diff); write_manifest_atomic(path, current)`，避免并发覆盖
3. **session_lock 续命场景**：每次 atomic 写完成后都顺手刷新 `expires_at = now + lock_timeout_hours`，让 atomic write 与锁保活共一次 IO
4. **崩溃残留 .tmp 的清理**：`read_manifest_safe` 启动时若发现 `manifest.yaml.tmp` 存在但 `manifest.yaml` 不存在，提示用户"上次写入崩溃，是否用 .tmp 兜底（要承担数据可能不完整的风险）"——不允许静默吃掉 .tmp

---

## 损坏 / 不一致检测

进入 diagnose 时校验：

| 检查 | 失败处理 |
|---|---|
| `manifest_version` 不在已知版本列表 | 阻断，提示用户升级 skill-assistant |
| `skill.initial_skill_hash` 与当前 skill 目录 hash 不一致 | 提示「检测到 skill 被外部修改」+ 让用户决定基于现状重置 / 放弃 |
| `iterations` 中存在 `status=in_progress` 但无 session_lock | 视为崩溃残留；进入 resume 流程 |
| `current_iteration > len(iterations)` | manifest 损坏；备份后重建 |
| `results.tsv` 行数与 `iterations` 不匹配 | 警告但不阻断；以 `iterations` 为准 |
| YAML 解析失败 | 备份为 `manifest.yaml.bak.<timestamp>` + 让用户从 iteration 目录手动恢复 |

---

## 多 skill 索引（可选）

未来可在 workspace 根（`skill-assistant-workspace/`）增加：

```yaml
# skill-assistant-workspace/index.yaml
last_active: "english-exam-writing-reviewer"
skills:
  - name: "english-exam-writing-reviewer"
    last_diagnose: "2026-04-28"
    score_latest: 84
  - name: "huashu-proofreading"
    last_diagnose: "2026-04-25"
    score_latest: 71
```

让用户 `@skill-assistant 看上次评测进度` 可快速定位最近活跃的 skill。

---

## NEVER

- **NEVER 把凭证 / API Key 写到 manifest** — 凭证只在 `config/.credentials.yaml`
- **NEVER 在 session_lock 持有者还活着的情况下静默改写 manifest** — 必须经用户确认
- **NEVER 删除 manifest** — 即使 status=aborted；保留供事后审计
- **NEVER 修改 `manifest_version`** 字段为未来版本号 — 写本字段必须忠于当前 skill-assistant 版本，迁移由读取方处理
- **NEVER 在 manifest 写大段输出内容** — 大块产物落到 `iteration-N/` 子目录，manifest 只存指针 / 摘要
- **NEVER 用 `path.write_text(yaml.dump(data))` 直接覆盖 manifest**— 必须走 atomic write（`.tmp` + `fsync` + POSIX `rename`）；推荐调 `scripts/manifest_io.py` helper
- **NEVER 在 atomic write 完成前就告诉用户"已保存"** — fsync 完才算落盘，半路打断的写法欺骗用户的"已保存"心智模型
- **NEVER 静默吃掉残留的 `manifest.yaml.tmp`** — 启动时发现 .tmp 存在必须告知用户上次崩溃，由用户决定是否信任 .tmp 兜底

---

## 相关文档

- 工作区目录规范：[workspace-layout.md](./workspace-layout.md)
- diagnose Step 0 初始化流程：详见 `modules/diagnose.md`
- setup workspace 选择引导：详见 `modules/setup.md`
