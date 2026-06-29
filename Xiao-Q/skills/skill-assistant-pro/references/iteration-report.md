# iter-summary.html 单轮摘要报告模板

> 每轮棘轮迭代结束时，主 Agent 用 `templates/iteration-report.html` 渲染一份**单轮摘要** HTML 报告，落到 `<workspace>/iteration-N/iter-summary.html`。报告整合：决策徽章 + 分数走势 + N 重复跑 benchmark + Comparator 盲评 + Grader critique evals + Analyzer 归因 + 反馈时间线 + 折叠 transcript。

> **与 detailed-report.html 的区别**：
> | 文件名 | 触发 | 内容范围 | 何时生成 |
> |---|---|---|---|
> | `iter-summary.html`（本文件描述）| 自动 | 单轮迭代摘要（决策 + benchmark + 折叠 transcript） | 每轮 4.1.6.5 后立即 |
> | `detailed-report.html` | **自动**| 完整诊断报告（用户视角 8 章节，详见 [full-report.md](./full-report.md)）| 每轮 4.1.6.5 内 iter-summary 之后立即，无条件生成 |
> | `final-report.html` | Step 5| 跨轮汇总 + 总评分变化曲线 | Step 5 收尾 |

---

## 何时渲染

由 `modules/diagnose.md` 在以下时机触发：

```
Step 4.1.4 重新评估完成（benchmark.json 已写）
       ↓
Step 4.1.4.5 盲评（仅 blind_hybrid，comparison.json 已写）
       ↓
Step 4.1.5 棘轮决策（决策已定）
       ↓
Step 4.1.6 post-hoc 归因（仅 blind_hybrid，analysis.json 已写）
       ↓
✦ 渲染 iteration-N/iter-summary.html ✦   ← 这里
       ↓
Step 4.1.7 体积守门
```

只有当本轮**至少跑了 dynamic 评测**才渲染——纯 static 模式下无 benchmark / Comparator / Analyzer 数据，没意义。

---

## 占位符清单

模板使用 `{{XXX}}` 占位符，主 Agent 渲染时**逐个**用 manifest / benchmark.json / grading.json / comparison.json / analysis.json 中的数据替换。

### 头部 / 元数据

| 占位符 | 取值来源 | 示例 |
|---|---|---|
| `{{SKILL_NAME}}` | `manifest.skill.name` | `english-exam-writing-reviewer` |
| `{{SKILL_ASSISTANT_VERSION}}` | `manifest.skill_assistant_version` | `1.7.1` |
| `{{ITERATION_N}}` | `manifest.current_iteration` | `3` |
| `{{MAX_ITERATIONS}}` | `manifest.max_iterations` | `5` |
| `{{SHORT_BOARD}}` | `manifest.iterations[N-1].short_board` | `D2` |
| `{{STRATEGY_ID}}` | `manifest.iterations[N-1].strategy_id` | `P2.1` |
| `{{TIMESTAMP_HUMAN}}` | now → `YYYY-MM-DD HH:mm` | `2026-04-28 17:42` |
| `{{EVAL_MODE}}` | `manifest.evaluation.eval_mode` | `blind_hybrid` |
| `{{WORKSPACE_PATH}}` | `manifest.workspace.absolute_path` | `/Users/.../skill-assistant-workspace/foo` |
| `{{REPORT_PATH}}` | 当前文件路径（相对项目根）| `<workspace>/iteration-3/iter-summary.html` |
| `{{INITIAL_COMMIT}}` | `manifest.skill.initial_commit` 短 hash | `a1b2c3d` |
| `{{CURRENT_COMMIT}}` | `git rev-parse --short HEAD` | `f4e5d6c` |
| `{{CLI_PROVIDER}}` | `manifest.iterations[N-1].accelerator.provider` 或 `n/a`（本轮没跑加速器时）| `claude-internal` |
| `{{FIDELITY}}` | `approximate_trigger_rate` / `true_trigger_rate` / `n/a` | `true_trigger_rate` |
| `{{LOCK_PID}}` / `{{LOCK_ACQUIRED}}` | `manifest.session_lock.*` | `78342` / `2026-04-28T17:00` |
| `{{ITER_DURATION}}` | `iter.completed_at - iter.started_at` | `42m 13s` |

### 决策徽章

| 占位符 | 取值 | 备注 |
|---|---|---|
| `{{DECISION_LABEL}}` | `KEEP` / `REVERT` / `UNCHANGED` | manifest.iterations[N-1].decision 大写 |
| `{{DECISION_CLASS}}` | `keep` / `revert` / `unchanged` | 控制颜色 |

### 分数概览

| 占位符 | 取值来源 |
|---|---|
| `{{SCORE_BEFORE}}` | `manifest.iterations[N-1].score_before` 保留 1 位小数 |
| `{{SCORE_AFTER}}` | `manifest.iterations[N-1].score_after` 保留 1 位小数 |
| `{{STDDEV_BEFORE}}` / `{{STDDEV_AFTER}}` | benchmark.json 上轮和本轮 stddev |
| `{{N_BEFORE}}` / `{{N_AFTER}}` | benchmark.json 上轮和本轮 N_repeats |
| `{{DELTA_VALUE}}` | `+2.6` / `-1.3` / `±0.0`（带正负号）|
| `{{DELTA_CLASS}}` | `delta-positive` / `delta-negative` / `delta-neutral` |
| `{{THRESHOLD_FORMULA}}` | 动态 t 分布阈值公式字符串，如 `"t(0.10,df=2) × σ/√N = 1.886 × σ/√3"`（N=3）；若 N=2 走兼容降级则填 `"0.5σ (N_repeats_too_small)"` |
| `{{THRESHOLD_VALUE}}` | 公式计算后的实数（如 `8.71`）；用 `mean ± THRESHOLD_VALUE` 做 keep/revert/unchanged 三档决策 |

### Sparkline 走势

`{{SPARKLINE_SVG}}` 是一段需要主 Agent 现场拼装的 SVG 内容，规则：

- viewBox `0 0 600 60`，X 轴均分给所有 iterations，Y 轴 0=底部=最低分 / 60=顶部=最高分
- 折线 + 面积，最后一个点标 `pt-current`（当前轮）
- `decision=revert` 的点标 `pt-revert`（红色）
- 每个点旁标小号文本：迭代号 + 分数

```html
<!-- 渲染示例（4 轮历史 + 当前第 5 轮）：-->
<path class="area" d="M 0 50 L 150 30 L 300 35 L 450 20 L 600 18 L 600 60 L 0 60 Z"/>
<path class="line" d="M 0 50 L 150 30 L 300 35 L 450 20 L 600 18"/>
<circle class="pt"         cx="0"   cy="50" r="3"/>
<circle class="pt"         cx="150" cy="30" r="3"/>
<circle class="pt-revert"  cx="300" cy="35" r="4"/>
<circle class="pt"         cx="450" cy="20" r="3"/>
<circle class="pt-current" cx="600" cy="18" r="5"/>
<text class="label" x="0"   y="58">i1</text>
<text class="value" x="0"   y="46">72</text>
<text class="label" x="150" y="58">i2</text>
<text class="value" x="150" y="26">78</text>
<text class="label" x="300" y="58">i3 ↩</text>
<text class="value" x="300" y="31">75</text>
...
```

### Benchmark 表（每条 scenario 一行）

`{{BENCHMARK_ROWS}}` 由主 Agent 拼接每条 scenario 的 `<tr>`，模板内已有占位示例。每行字段：

```
| scenario | baseline mean | with_skill mean | Δ | stddev (with) | min/max | Grader pass_rate |
```

Δ 的 `.pill` 类：`pass`（增）/ `fail`（减）/ `tie`（无显著）。

### Comparator 盲评（仅 blind_hybrid）

| 占位符 | 取值 |
|---|---|
| `{{WINNER_LABEL}}` | `A` / `B` / `TIE` |
| `{{WINNER_BANNER_CLASS}}` | 空（A/B winner）/ `tie` |
| `{{WINNER_REASONING}}` | comparison.json `.reasoning` |
| `{{CONFIDENCE_CLASS}}` / `{{CONFIDENCE_LABEL}}` | `high` `HIGH` / `medium` `MEDIUM` / `low` `LOW` |
| `{{A_ROLE}}` / `{{B_ROLE}}` | 揭盲后 baseline / with_skill / iteration-N（来自 anon_mapping.json）|
| `{{A_OVERALL_SCORE}}` / `{{B_OVERALL_SCORE}}` | comparison.json `.rubric.{A,B}.overall_score` |
| `{{A_RUBRIC_BARS}}` / `{{B_RUBRIC_BARS}}` | 每个 criterion 一段 `.rubric-bar` |

`.rubric-bar` 渲染示例：

```html
<div class="rubric-bar">
  <div class="row"><span>正确性</span><span class="v">5/5</span></div>
  <div class="track"><div class="fill" style="width: 100%"></div></div>
</div>
```

> `style="width: X%"` 用 score/5×100 计算（如 4/5 → 80%）。

> ⚠️ 即便 eval_mode ≠ blind_hybrid（无盲评数据），section 03 也保留——主 Agent 用单段说明 "本轮 eval_mode={{EVAL_MODE}}，未做盲评" 替换 `{{WINNER_REASONING}}`，并把 winner-banner 整段 fallback 为静态文本。**不要**整段删 section（保持模板结构稳定）。

### Grader / D10.3 stat

| 占位符 | 取值 |
|---|---|
| `{{GRADER_PASSED}}` / `{{GRADER_TOTAL}}` | grading.json `.summary.passed/.total` |
| `{{GRADER_PASS_RATE}}` | `passed/total × 100` 整数 |
| `{{HEALTH_SCORE}}` | grading.json `.critique_summary.test_set_health_score` |
| `{{HEALTH_CLASS}}` | health_score ≥80 → `success` / 60-79 → `warn` / <60 → `danger` |
| `{{D10_3_SCORE}}` | `health_score × 0.25`（保留整数；nullable→`N/A`）|
| `{{DISCRIMINATING_COUNT}}` | `.critique_summary.discriminating_assertions` |
| `{{LOOSE_COUNT}}` | `.critique_summary.loose_assertions` |
| `{{MISSING_COUNT}}` | `.critique_summary.missing_assertions` |
| `{{CRITIQUE_SUGGESTIONS}}` | grading.json `.eval_feedback.suggestions[]` 拼接 `<li>` |

`{{CRITIQUE_SUGGESTIONS}}` 每条渲染：

```html
<li class="warn">
  <strong>{{loose|missing|too_strict 的中文标签}}：</strong>"{{assertion 原文（如有）}}" — {{reason}}
  <span class="meta">
    <strong>discriminating_power:</strong> {{low|missing_assertion|high}}
    {{有 assertion 时}}&nbsp;·&nbsp;<strong>assertion_id:</strong> #{{idx}}
  </span>
</li>
```

### Analyzer 归因（仅 blind_hybrid，analysis.json 已存在）

| 占位符 | 取值 |
|---|---|
| `{{WINNER_STRENGTHS}}` | analysis.json `.winner_strengths[]` 每条一个 `<li>` |
| `{{LOSER_WEAKNESSES}}` | analysis.json `.loser_weaknesses[]` 每条一个 `<li class="danger">` |
| `{{IMPROVEMENT_SUGGESTIONS}}` | analysis.json `.improvement_suggestions[]` 每条一个 `<li>` |
| `{{CARRY_KEEP}}` / `{{CARRY_STRENGTHEN}}` / `{{CARRY_DROP}}` | analysis.json `.carry_over_to_next_iteration.*` 数组 → 中文 markdown 子弹列表（`• xxx<br>• yyy`）|

每条 strength 渲染：

```html
<li>
  <strong>{{claim}}</strong>
  <span class="meta">
    SKILL.md: <strong>{{evidence_skill_md}}</strong>
    {{有 transcript evidence 时}}&nbsp;·&nbsp;rubric: <strong>{{rubric_criterion_impacted}}</strong>
  </span>
</li>
```

每条 improvement 渲染（priority pill）：

```html
<li>
  <span class="pill {{priority}}">{{priority|upper}}</span>&nbsp;{{concrete_change 截断 100 字符}}
  <span class="meta"><strong>category:</strong> {{category}} · <strong>target:</strong> {{change_target 文件相对路径}}</span>
</li>
```

> 若本轮非 blind_hybrid（无 analysis.json）：整段 section 05 输出"本轮未跑 blind_hybrid，跳过 post-hoc 归因"；同样**不要**删 section。

### 反馈时间线

`{{FEEDBACK_TIMELINE}}` 来自 manifest.feedback_history[]，每条：

```html
<div class="item {{accepted|rejected}}">
  <div class="ts">{{timestamp}} · iteration-{{iteration}}</div>
  <div class="body">{{notes}}</div>
</div>
```

按 `iteration` 升序，本轮在最底（最新）。

### 折叠 transcript

`{{TRANSCRIPT_DETAILS}}` 由主 Agent 遍历 `<workspace>/iteration-N/eval-XXX/{baseline,with_skill}/transcript.md`：

```html
<details class="transcript">
  <summary>{{scenario_id}} · {{baseline|with_skill}} · run {{i}} of {{N}} · {{duration}}s · {{tool_calls}} tool calls</summary>
  <div class="body">{{transcript_content_html_escaped}}</div>
</details>
```

> ⚠️ 必须 HTML escape transcript 内容（至少 `&` → `&amp;`、`<` → `&lt;`、`>` → `&gt;`），避免 transcript 中含 HTML 标签污染报告布局。

> ⚠️ 单条 transcript 超过 5000 字时，body 头部加一行：「⚠️ 已截断（原 X 字符），完整版见 transcript.md」并保留前 5000 字。

> 默认全部折叠；用户在浏览器内按 `E` 一键展开，按 `C` 一键折叠（已内置 JS 监听）。

---

## 渲染流程伪代码

主 Agent 执行：

```python
def render_iteration_report(workspace: Path, iter_n: int, manifest: dict) -> Path:
    """渲染 iteration-N/iter-summary.html。"""
    template = (workspace.parent.parent.parent  # → skill-assistant 根
                / ".cursor/skills/skill-assistant/templates/iteration-report.html"
               ).read_text()

    # 1. 收集所有数据源
    benchmark = json.loads((workspace / f"iteration-{iter_n}/benchmark.json").read_text())
    grading_files = list((workspace / f"iteration-{iter_n}").glob("eval-*/grading.json"))
    comparison_files = list((workspace / f"iteration-{iter_n}").glob("eval-*/comparison.json"))
    analysis_files = list((workspace / f"iteration-{iter_n}").glob("eval-*/analysis.json"))
    feedback_history = manifest.get("feedback_history", [])

    # 2. 计算派生字段（DELTA_CLASS / HEALTH_CLASS / sparkline 坐标 / ...）
    placeholders = build_placeholders(manifest, iter_n, benchmark, grading_files,
                                       comparison_files, analysis_files, feedback_history)

    # 3. 占位符替换
    for key, value in placeholders.items():
        template = template.replace("{{" + key + "}}", html_escape_value(value))

    # 4. 落盘
    report_path = workspace / f"iteration-{iter_n}/iter-summary.html"
    report_path.write_text(template, encoding="utf-8")
    return report_path
```

> **不需要**真正的 jinja / mustache 引擎——朴素 `str.replace` 足够；占位符全大写下划线 + 双花括号，与正文不冲突。

> 占位符**未替换**的情况（数据缺失）：用 `—` 或 `n/a` 兜底，**绝不**留 `{{XXX}}` 在产物里（用户看到会很糟糕）。最后渲染完做一次 sanity check：`assert "{{" not in rendered, "占位符未全部替换"`。

---

## 用户交互入口

棘轮决策完成后主 Agent 输出：

```
✓ iteration-3 完成（KEEP，分数 75.2 → 78.4，Δ +3.2）
✓ 评测产物已落盘 <workspace>/iteration-3/

📊 单轮摘要报告: <workspace>/iteration-3/iter-summary.html
   含分数走势 / Comparator 盲评 / Grader critique evals / Analyzer 归因 / 反馈时间线 / 折叠 transcript

[1] 在浏览器打开报告
[2] 进入下一轮（iteration-4）
[3] 收尾（Step 5 汇总报告）
[4] 看 manifest 详情
```

> **不要**自动打开浏览器（用户的开发环境可能没有 GUI）；只列出路径让用户复制。

---

## 三种报告的关系

| 报告 | 范围 | 触发 | 何时生成 |
|---|---|---|---|
| `iteration-N/iter-summary.html` | 单轮摘要 | 自动 | 每轮 4.1.6 后立即 |
| `iteration-N/detailed-report.html` | 完整诊断报告（用户视角 8 章节）| 用户主动（Step 6 [1]）| 棘轮收尾或评测结束时 |
| `final-report.html` | 跨轮汇总 + 总评分变化曲线 | Step 5 自动 | Step 5 收尾 |
| `final-card.png` | 成果卡片（社交分享尺寸） | 用户主动（Step 6 [2]）| 按需 |

> 命名约定：**摘要 (summary) vs 详细 (detailed) vs 跨轮 (final)** 三档清晰区分。

---

## NEVER

- **NEVER 在没替换完所有占位符的情况下落盘** — 部署前必须 sanity check
- **NEVER 把 transcript 原文不 escape 直接塞进 HTML** — XSS 风险（本地查看也不该有 stray `<script>`）
- **NEVER 改 CSS class 名** — 模板与 reference 的占位符约定耦合，改类名会 break 渲染脚本
- **NEVER 自动打开浏览器** — 让用户主动选择
- **NEVER 整段删除某个 section**（即使数据缺失） — 用 fallback 文本替代，保持报告结构稳定，便于跨轮对比
