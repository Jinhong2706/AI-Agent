# 子 Agent 调用协议（sub-agent-protocol）

> 共用规则文件 | 把"主 Agent 启动子 Agent → 子 Agent 落盘 → 主 Agent 校验"的协议从 `modules/inspect.md` D.1 / `modules/diagnose.md` 4.1.4 / `agents/grader.md` / `agents/comparator.md` / `agents/analyzer.md` 五处重复内容收敛成一处。

---

## 三个子 Agent 的角色与产物

| 子 Agent | 主要文件 | 核心产物 | 当前 eval_mode |
|---|---|---|---|
| **Grader** | `agents/grader.md` | `grading.json`（每条 expectation 的 passed/evidence + critique evals） | `dynamic` / `hybrid` / `blind_hybrid` |
| **Comparator** | `agents/comparator.md` | `comparison.json`（A/B 盲评 winner + content/structure rubric 分） | `blind_hybrid` 专属 |
| **Analyzer** | `agents/analyzer.md` | `analysis.json`（structural diff / winner_strengths / carry_over） | `blind_hybrid` 专属 |

---

## 主 Agent 装配协议（启动子 Agent 前必填）

无论调用哪个子 Agent，主 Agent 在 spawn 前**必须装配**以下信息，写入 `<workspace>/iteration-N/eval-XXX/_subagent_input.json`，然后通过 prompt 把这个 JSON 内容传给子 Agent（用 here-doc 或 inline 引用都行）：

```jsonc
{
  "scenario_id": "happy-1",
  "scenario_priority": "P0",
  "functional_module": "search",

  "prompt": "<原始 user prompt>",
  "expectations": [                                  // 来自 test-prompts.json[scenario].judgements
    "review.json 包含 task_subtype 字段",
    "..."
  ],
  "skill_dimensions_being_evaluated": ["D1", "D3"],  // 仅 Grader 用，Comparator/Analyzer 可省

  "transcript_path": "<absolute path to baseline/run-K transcript.md>",
  "outputs_dir":     "<absolute path to baseline/run-K/outputs/>",
  "output_path":     "<absolute path to grading.json | comparison.json | analysis.json>",

  // —— Comparator 盲评专属（其余子 Agent 不填） ——
  "output_a_path":   "<absolute path to _anonymous/A/outputs/>",
  "output_b_path":   "<absolute path to _anonymous/B/outputs/>",
  "anon_mapping_hidden": true,                       // 必须 true，否则破坏盲评设计

  // —— Analyzer post-hoc 专属 ——
  "winner_role":     "with_skill",                   // Comparator 揭盲后的真相
  "comparison_path": "<comparison.json 路径>",
  "skill_md_path":   "<被评测 SKILL.md 当前 commit 的路径>"
}
```

**装配 NEVER**：

- **NEVER 不读 test-prompts.json 就装配 expectations** — expectations 必须来自该 scenario 的 `judgements` 字段，不是主 Agent 现编
- **NEVER 给 Comparator 传 `winner_role` / `mapping`** — 那是揭盲后的信息，泄漏 = 盲评失效
- **NEVER 把 expectations 数组裁切到子集** — 子 Agent 必须见到该 scenario 的全部 judgement，否则评分维度不全
- **NEVER 复用上一轮的 transcript_path** — 每轮 iteration 必须重新跑双跑，禁止"transcript 没变就跳过子 Agent 评"

**落盘 NEVER**：

- **NEVER 自创 grading.json schema**— 顶层必须 `passed_count` + `total_count` + `expectations[]`，不是 `summary.passed/total` + `judgements[]`/`negative_judgements[]`。后者会导致 `generate-full-report.mjs` 读不到、报告 ⑥ 段空白、且老版 sanity check 误以为通过——曾有事故因此发生——两套 schema 看似等价，但脚本读 schema 是字面读取
- **NEVER 跳过 `eval_metadata.json`**— 每个 `eval-*/` 目录下必须有 `eval_metadata.json`（字段表见上方）；缺失时报告 ⑥ 段会用目录 basename 兜底，priority/functional_module 标签会消失
- **NEVER 落盘后不调 `scripts/validate_eval_artifacts.py`**— 这是第 1.5 道关，专抓 schema 错配；validator failed (exit=1) 必须修后才能调 `generate-full-report.mjs`，绝不允许 `--skip-validator` 绕过

---

## 子 Agent 落盘约定

每个子 Agent 只能写**自己唯一的产物文件**到 `output_path`，不允许写到其他位置（防止越权污染 manifest / results.tsv）：

| 子 Agent | output_path 默认 | 必填顶层字段|
|---|---|---|
| Grader | `<eval-XXX>/<role>/run-K/grading.json` | `scenario_id` · `passed_count` · `total_count` · `expectations[]` · `critique_evals?` |
| Comparator | `<eval-XXX>/comparison.json`（与 _anonymous 同级父目录）| `scenario_id` · `winner` ∈ {A, B, TIE} · `confidence` · `rubric_scores` · `reasoning` |
| Analyzer | `<eval-XXX>/analysis.json` | `scenario_id` · `structural_differences` · `winner_strengths` · `loser_weaknesses` · `improvement_suggestions[]` · `carry_over_to_next_iteration` |

### `grading.json` 完整 schema

> ⚠️ 这是 dry_run 主 Agent / 真子 Agent 都必须遵守的 schema。`scripts/validate_eval_artifacts.py` 用这份字段表做强校验（exit=1 阻断报告生成）。**不允许凭直觉自拟字段名**——历史事故：写成 `summary.passed/total + judgements[]` 导致 `generate-full-report.mjs` 读不到、报告 ⑥ 段空白且 sanity check 误以为通过。

```json
{
  "scenario_id":  "eval-out-of-scope-ielts",
  "scenario":     "eval-out-of-scope-ielts",
  "prompt_id":    30,
  "side":         "with_skill | baseline | old_skill",
  "run":          1,
  "dry_run":      true,
  "passed_count": 4,
  "total_count":  4,
  "pass_rate":    1.0,
  "expectations": [
    {
      "name":        "refuse-ielts",
      "category":    "E_compliance",
      "expectation": "Skill 拒绝按雅思标准批改（不输出 Band 5.5 / 6.0 / 7.0 这类雅思 Band Score）",
      "passed":      true,
      "evidence":    "输出『抱歉，本 Skill 不批改雅思作文』+ 未输出 Band Score"
    }
  ],
  "critique_evals": [
    {
      "expectation_name": "refuse-ielts",
      "critique":         "judgement 太宽松 / 太严苛 / 缺位置指引",
      "severity":         "minor | major"
    }
  ]
}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|:-:|---|
| `scenario_id` | string | ✅ | 与 `_subagent_input.json` 一致；防子 Agent 错乱 |
| `passed_count` | int | ✅ | 通过的 expectation 数（不是 `score` / `summary.passed`）|
| `total_count` | int | ✅ | expectation 总数（不是 `total` / `summary.total`）|
| `pass_rate` | float | 推荐 | `passed_count / total_count`，给报告渲染用 |
| `expectations[]` | array | ✅ | 不是 `judgements[]` / `results[]`——脚本兼容旧字段但推荐用 `expectations` |
| `expectations[].name` | string | 推荐 | 唯一标识，便于 critique 反向引用 |
| `expectations[].category` | enum | 推荐 | `A_loading` / `B_workflow` / `C_output` / `D_scope_specific` / `E_compliance` |
| `expectations[].expectation` | string | ✅ | 检查内容（不是 `text` / `description` / `question`）|
| `expectations[].passed` | bool | ✅ | 不允许 `result: "pass"` 字符串|
| `expectations[].evidence` | string | ✅ | 具体证据；不允许 `"见上文" / "如前所述" / "" / "略"`（validator 抓） |
| `dry_run` | bool | dry_run 时必填 | 主 Agent 自己当 Grader 时为 `true` |
| `critique_evals[]` | array | 可选 | D10.3 维度，反向质询 expectation 本身的判别力 |

### `eval_metadata.json` 字段表（每个 `eval-*/` 目录下必有）

> 没有 `eval_metadata.json`，`generate-full-report.mjs` 会用目录 basename 兜底，但 priority / functional_module 标签会缺失，⑥ 段 eval-card 信息不完整。

```json
{
  "eval_name":         "eval-out-of-scope-ielts",
  "scenario":          "eval-out-of-scope-ielts",
  "prompt_id":         30,
  "prompt":            "<原始 user prompt 字符串>",
  "expected":          "<给 Grader 的自由文本期望>",
  "priority":          "P0 | P1 | P2",
  "functional_module": "out_of_scope_refusal",
  "scope":             "all | <custom>",
  "dry_run":           true,
  "evaluator":         "skill-assistant.inspect.blind_hybrid (dry_run降级)"
}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|:-:|---|
| `eval_name` | string | ✅ | 与目录名一致 |
| `scenario` | string | ✅ | 与 test-prompts.json 中的 scenario / id 对得上 |
| `prompt` | string | ✅ | 原始 user prompt（脚本 ⑥ 段渲染时引用）|
| `priority` | enum | 推荐 | P0 / P1 / P2，用于 ⑥ 段 pri-tag 染色 |
| `functional_module` | string | 推荐 | 用于 ⑥ 段 moduleTag 标签 |

---

## 主 Agent 收尾校验（共用 7 项 sanity check）

子 Agent 退出后主 Agent**必须**就地校验，任一失败立即 `回写 + 重 spawn 一次`，两次失败才允许走 dry_run 降级：

```
✓ 1. output_path 文件存在且 size > 50 字节
✓ 2. JSON 解析通过
✓ 3. scenario_id 与装配输入一致（防子 Agent 错乱）
✓ 4. expectations / rubric_scores 字段长度与装配输入对得上
✓ 5. evidence / reasoning 不为空、不为 "见上文"/"如前所述" 这种空话
✓ 6. 不允许"全 PASS / 全 winner=A"等懒人输出（Grader 全 passed=true 必须复跑；Comparator 连续 5 条都 winner=A 也复跑）
✓ 7. 时间戳合理（now − sub_agent_finished_at < 1h；过老视为缓存复用，作废）
```

> **复用关系**：这 7 项与 `modules/diagnose.md` 4.1.4.c / `modules/inspect.md` D.1 中的 dry_run 落盘 sanity check **共用同一套规则**——dry_run 的 grading.json 也是按照本协议生成的，只是"子 Agent"换成"主 Agent 自己"。

---

## 为什么不让子 Agent 自己读 test-prompts.json

历史方案曾让 Grader 自己 `Read(<workspace>/test-prompts.json)` 找当前 scenario，结果 3 个问题：

1. **scenario 漂移**：子 Agent 可能选到错误的 scenario（特别是 prompt 文本相似时）
2. **数据 inflation**：子 Agent 容易扫描整个 test-prompts 而不是只看本条
3. **盲评破坏**：Comparator 一旦能读 test-prompts.json，就能从 metadata 反推 with_skill 身份

**现行规则**：所有上下文由主 Agent 装配后**单向传递**给子 Agent；子 Agent 只读 `_subagent_input.json` + `transcript_path` + `outputs_dir`，不读 manifest / test-prompts。

---

## 与已有机制的关系

| 机制 | 协作 |
|---|---|
| [test-prompts-design.md](./test-prompts-design.md) | 它管"测试集长什么样、用户怎么确认"；本文管"测试集如何分发给子 Agent" |
| [time-budget.md](./time-budget.md) | hard 超时降级时，子 Agent 调用直接跳过，主 Agent 切 dry_run 复刻协议 |
| [manifest-schema.md](./manifest-schema.md) atomic write | `_subagent_input.json` 不是 manifest，可用普通 write_text；但每个子 Agent 完成后主 Agent 把指针写回 manifest 时必须走 atomic |
| 一致性校验 | Grader 输出的 grading.json 是 `static_score vs dynamic_score` 校验中 dynamic_score 的源头；本协议保证它的可信度 |

---

## NEVER（汇总）

- **NEVER 让子 Agent 自己读 test-prompts.json** — 必须由主 Agent 装配后传入
- **NEVER 给 Comparator 任何能反推身份的信息**（winner_role / anon_mapping / SKILL.md 路径）
- **NEVER 跳过 7 项收尾校验**——子 Agent 输出"看起来很完整"和"实际有效"是两回事
- **NEVER 在主 Agent 调用子 Agent 前不显式声明 scenario_id**——多 scenario 评测必须有 ID 维度，否则后续 results.tsv 无法对位
- **NEVER 复用上一轮的子 Agent 产物**——每轮都得重跑，不允许"transcript 没变就跳过"
