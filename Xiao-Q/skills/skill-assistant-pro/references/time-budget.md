# 时间预算控制（time-budget）

> 共用规则文件 | 解决"评测一跑就半小时无回音 / 子 Agent 卡死无人察觉 / N×scenario 组合后超用户预期 5 倍"等真实事故。

每个 `eval_mode` 都有**默认 deadline**和**超时降级路径**，主 Agent 必须**显式声明开始时间 + 显式校对剩余预算**，不能等到用户问"还要多久"才发现已超时。

---

## 默认预算表

| eval_mode | soft_deadline（提醒） | hard_deadline（强制降级）| 主要耗时构成 | 超时降级策略 |
|---|---:|---:|---|---|
| `preview` | 90s | 3 min | 1 prompt × 1 次 × 双跑 | hard 超时 → 直接结束本次 preview，告诉用户"30 分钟级评测被节流到 1 分钟样本，请回 [3] hybrid 跑完整版" |
| `static` | 60s | 2 min | 10 维度静态扫描 | soft 超时 → 提示"D8 安全扫描很慢，要不要跳过（仅本次）"；hard 超时 → 跳过 D8 + 标 confidence=low |
| `dynamic` | 6 min | 10 min | N×scenarios × 双跑 + Grader | soft → 减半剩余 N_repeats（P0 优先保留）；hard → 切到 dry_run 完成剩余 prompt 并标 partial |
| `hybrid` | 8 min | 12 min | static + dynamic | 与 dynamic 同；超时优先牺牲 dynamic 的 P2 prompt |
| `blind_hybrid` | 12 min | 20 min | static + dynamic + Comparator + Analyzer | soft → 跳过 Analyzer（保留 Comparator）；hard → 切 dry_run + 仅保留 P0 scenario |
| `batch_baseline` | 5 min/skill | 8 min/skill | per-skill structure scan | per-skill hard 超时 → 跳过该 skill 写 `aborted=timeout` 一行 |
| 加速器路径 B（CLI） | 60s/iter | 90s/iter | CLI fresh process | hard 超时 → 切下一 Provider（按 description-optimizer.md 三级链） |

> 表中所有值都是**主 Agent 自检的提醒/降级触发点**，不依赖外部 timeout 信号——主 Agent 必须自己记 `start_time` 并在每个 prompt / 每个 scenario 边界检查 `elapsed`。

---

## 实施约定

### 1. 主 Agent 必须做的

```
开始评测前：
  manifest.evaluation.time_budget = {
    eval_mode: "<mode>",
    started_at: "<ISO8601>",
    soft_deadline_seconds: <N>,
    hard_deadline_seconds: <M>,
    elapsed_checkpoints: []     # 每完成一条 prompt / 一个 scenario 追加一条
  }

每完成一个 scenario 后：
  now = ISO8601()
  elapsed = now - started_at
  manifest.evaluation.time_budget.elapsed_checkpoints.append(
    { scenario_id, completed_at: now, elapsed_s: elapsed }
  )
  if elapsed > soft_deadline:
    展示 soft 超时菜单（见下方"用户菜单"）
  if elapsed > hard_deadline:
    强制走对应 eval_mode 的"超时降级策略"，无须用户确认
    results.tsv 该行加 `time_budget=hard_exceeded` 标记
```

### 2. soft 超时用户菜单（统一格式）

```
⏱  评测耗时已超出预期：
    模式: hybrid
    soft_deadline: 8 min（已用 8.5 min）
    剩余: {Y} 个 prompt × {N} 次

请选择：
  [a] 减半剩余 N_repeats（P0 prompts 仍跑满）
  [b] 跳过 P2 prompts，只跑 P0 + P1
  [c] 全部切 dry_run（速度快但无 baseline 真值，仅作占位）
  [d] 继续等（自动撤掉 soft 提醒，10 分钟内不再打扰）
  [e] 中止评测（保留已完成的，写 aborted_reason="user_cancel_at_soft"）
```

> **STOP**：等用户选 [a]/[b]/[c]/[d]/[e]，**不可主 Agent 自行选择**。

### 3. hard 超时（自动执行，事后告知）

hard 超时**不再询问用户**——直接按表中策略执行降级，并在 results.tsv 该行追加：

```
time_budget=hard_exceeded
degraded_action="<a/b/c>对应的策略名"
elapsed_at_hard=<秒数>
prompts_completed=<X>/<Y>
```

报告渲染时 `renderMustReadItems` 必须把这条信息以 `priority=high` 加到 Must-Read 顶部，并在结论里明示"本次评测因预算限制为 partial 状态，分数仅供参考"。

---

## manifest 字段约束

```yaml
evaluation:
  eval_mode: "hybrid"
  time_budget:
    soft_deadline_seconds: 480       # 8 min
    hard_deadline_seconds: 720       # 12 min
    started_at: "2026-04-29T15:30:00+08:00"
    elapsed_checkpoints:
      - { scenario_id: "happy-1", completed_at: "...", elapsed_s: 95 }
      - { scenario_id: "edge-2",  completed_at: "...", elapsed_s: 240 }
    soft_exceeded_action: null       # 用户选了 [a-e] 后填这里
    hard_exceeded_action: null       # 自动降级动作名
```

---

## NEVER

- **NEVER 不显式记 `started_at` 就开跑评测** — 没有起点就无法判断 elapsed
- **NEVER 把 hard_deadline 直接当 soft 用** — soft 必须先于 hard 触发，给用户一次缓冲
- **NEVER 在 hard 超时降级后不写 results.tsv 标记** — partial 评测必须可追溯，下次 ratchet 决策才不会误把 partial 分当真分
- **NEVER 在 dynamic 超时时优先牺牲 P0 prompt** — 时间预算的牺牲顺序必须是 P2 → P1 → P0
- **NEVER 用单个 deadline 数字覆盖所有 eval_mode** — preview / blind_hybrid 耗时差 6×，必须分开

---

## 与已有机制的关系

| 已有机制 | 与 time-budget 的协作 |
|---|---|
| **session_lock**（manifest-schema.md） | session_lock 防止"两个会话同时改"，time-budget 防止"一个会话跑无止境"。两者独立，互相不替代 |
| **N_repeats 差异化** | hard 降级时优先减 P2 的 N，再减 P1 的 N；P0 的 N 永远保留（除非整个评测中止） |
| **dry_run 落盘 sanity check** | hard 超时切 dry_run 时，sanity 7 项**仍必须跑**——不允许"反正快超时了凑合一下" |
| **t 分布动态阈值** | 因 hard 超时被降级的 partial 评测不参与棘轮决策（status=partial，4.1.5 直接 unchanged） |

---

## 调用入口

| 入口 | 何时触发 |
|---|---|
| inspect.md D.0.3 | inspect 启动时根据 eval_mode 写 time_budget 默认值，告知用户 |
| diagnose.md Step 4.0 | 每一轮 iteration 启动时刷新 started_at（不复用上轮预算） |
| description-optimizer.md §路径 B | CLI 加速器单独使用 60s/90s 配置（不与 dynamic 的 6/10 min 共用） |
| generate-full-report.mjs | 报告渲染时读 manifest.evaluation.time_budget.hard_exceeded_action，存在则注入 Must-Read |
