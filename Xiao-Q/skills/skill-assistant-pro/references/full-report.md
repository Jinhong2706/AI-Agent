# detailed-report.html 完整诊断报告

> 对应 `diagnose Step 6 [1]` 菜单选项，用户视角 8 章节结构

---

## 与其他报告的区别

| 报告类型 | 文件名 | 触发 | 适用场景 |
|---|---|---|---|
| **单轮摘要** | `iteration-N/iter-summary.html` | 自动（4.1.6.5）| 当轮迭代后即时回看决策 |
| **完整诊断报告** | `iteration-N/detailed-report.html`（本文件描述）| 用户主动（Step 6 [1]）| 归档 / 团队 review / 深度分析 |
| **跨轮汇总** | `final-report.html`（workspace 根）| Step 5 自动 | 多轮 diff + 总评分变化曲线 |
| **PNG 成果卡片** | `iteration-N/result-card.png` | 用户主动（Step 6 [2]）| 分享到群 / iWiki / 微信 |

> Step 6 选 `[3] 两者都要` 时同时生成 detailed-report.html + result-card.png。

---

## 八章节结构

> 阅读顺序自上而下：先看一句话结论与必读建议（30 秒决策），再看评分总览（1 分钟把握全貌），最后看详情与附录（按需深入）。

| # | 章节 | 数据来源 | 无数据时降级 |
|---|---|---|---|
| ① | **核心结论** | `analysis.json` + `results.tsv` 自动汇总 | 始终有内容（脚本基于分数自动生成等级判断）|
| ② | **必读建议** | `analysis.json.must_read_items` | 显示"未发现紧急必读项"占位 |
| ③ | **评分总览**（6 分数卡 + 走势表）| `results.tsv` + `manifest.yaml` + `analysis.json` | 使用诊断估算值 + 显示"无走势数据" |
| ④ | **测试用例覆盖**（4 维矩阵 + 覆盖率统计）| `<workspace>/test-prompts.json` 解析 functional_module / scenario / priority / category | 缺 test-prompts.json 时提示先走 auto-judgement-generator.md |
| ⑤ | **评分详情**（10 维度 + D10 子项 + 病症 + 帕累托）| `analysis.json.dimensions` / `analysis.json.d10` | 显示"—"，note 显示"待主 Agent 填充" |
| ⑥ | **测试数据与结果**（test-prompt + judgement + baseline vs with_skill 对比 + 折叠 transcript）| `eval-*/{baseline,with_skill}/run-*/{grading.json, outputs/report.md, transcript.md}` + `benchmark.json` + `comparison.json` | static 模式 / dry_run 落盘缺失警告横幅 |
| ⑦ | **改动详情**（git diff + 改动原因 + NEVER 检查 + 下一步建议）| `git diff HEAD~1..HEAD` + `analysis.json.never_results` + `manifest.iterations[].note` | 提示"无 git 仓库" / "本次为 static" |
| ⑧ | **评分标准参考**（附录：等级 / 维度权重 / 公式 / 测试集完整性标准）| 静态附录，模板内置 | 始终有内容 |

> **dry_run 模式同样要写 grading.json**：当 `eval_mode in [dry_run, dynamic_dry_run]` 时，主 Agent 必须按 dynamic 同款目录 schema 把推演结果落盘——参见 `modules/diagnose.md` Step 4.1.4.c 与 `modules/inspect.md` D.1。否则 ⑥ 测试数据章节只能渲染 dry_run 警告横幅。

---

## 调用方式

```bash
node .cursor/skills/skill-assistant/scripts/generate-full-report.mjs \
  <workspace>/iteration-N \
  <workspace>/iteration-N/detailed-report.html
```

脚本自动：

1. 读取 `manifest.yaml`（元数据 / session 信息）
2. 读取 `results.tsv`（分数走势 + 当轮 keep/revert）
3. 执行 `git diff HEAD~1..HEAD`（改动着色）
4. 扫描 `eval-*/` 目录（eval 数据）+ `<workspace>/test-prompts.json`（覆盖矩阵）
5. 读取 `analysis.json`（D0-D9 / D10 / must_read / never_results / next_steps）
6. 填充 `templates/full-report.html` 占位符（30+ 个）
7. **Sanity check**：
   - 渲染产物无残留 `{{...}}` 占位符
   - 包含 `eval-card` 或 `static 模式` 或 `dry_run` 任一标记
   - 非 static 非 dry_run 模式下 `eval-*/grading.json` 至少 1 个
   - 任一失败 → exit code = 3，但仍写文件让用户看出问题
8. 生成自包含 HTML（无外部依赖，可离线查看）
9. macOS / Linux / Windows 自动打开

---

## 数据文件位置

```
<workspace>/<skill-name>/
├── manifest.yaml
├── results.tsv
├── test-prompts.json                 ← ④ 覆盖矩阵的数据源
├── trigger-queries.json              ← D10.2 触发率（不直接渲染）
└── iteration-N/
    ├── diagnosis/
    │   └── diagnosis-report.md       ← ⑦ 改动详情末尾的折叠原文
    ├── analysis.json                 ← ① 核心结论 + ② 必读 + ③ 分数 + ⑤ 维度 + ⑦ NEVER + 下一步
    ├── benchmark.json                ← ⑥ N 重复跑统计（dynamic/hybrid 时有）
    ├── comparison.json               ← ⑥ Comparator 盲评（blind_hybrid 时有）
    ├── eval-<scenario-or-name>/
    │   ├── eval_metadata.json        ← scenario / prompt / functional_module / priority
    │   ├── with_skill/run-1/grading.json
    │   ├── with_skill/run-1/outputs/report.md      ← ⑥ 输出对比 with_skill 侧
    │   ├── with_skill/run-1/transcript.md          ← ⑥ 折叠 transcript with_skill
    │   ├── baseline/run-1/grading.json
    │   ├── baseline/run-1/outputs/report.md        ← ⑥ 输出对比 baseline 侧
    │   └── baseline/run-1/transcript.md            ← ⑥ 折叠 transcript baseline
    ├── iter-summary.html             ← 4.1.6.5 自动单轮摘要（不同文件）
    └── detailed-report.html          ← 本脚本输出
```

---

## analysis.json 推荐 schema

```json
{
  "must_read_items": [
    { "priority": "high",   "text": "D10.1 触发率 0% — 必须先跑加速器优化 description", "ref": "references/description-optimizer.md" },
    { "priority": "medium", "text": "D5 反模式清单缺位置指引", "ref": "SKILL.md L120-L145" },
    { "priority": "low",    "text": "body tokens 仍有 1500 余量", "ref": "—" }
  ],
  "dimensions": {
    "D0": { "score": 85, "note": "Expert 占比 70%，Activation 充分" },
    "D1": { "score": 90, "note": "frontmatter 完整，description 含 WHAT/WHEN/关键词" },
    "...": "..."
  },
  "d10": {
    "d10_1": { "score": 38, "note": "test-prompts 5 条，但 baseline 对比缺 3 条" },
    "d10_2": { "score": 45, "note": "trigger-queries 12 条，三类查询全覆盖" },
    "d10_3": { "score": 18, "note": "critique evals 标 2 条 assertion 太宽松" }
  },
  "directive_before": 76, "directive_after": 78, "directive_delta": "+2", "directive_note": "...",
  "constraint_before": 82, "constraint_after": 82, "constraint_delta": "0", "constraint_note": "...",
  "redundancy_before": 14, "redundancy_after": 8, "redundancy_delta": "-6pp", "redundancy_note": "...",
  "expert_pct": 58, "activation_pct": 34, "redundant_pct": 8,
  "symptoms": "轻微堆砌病（已改善）", "pareto": "✅ 已达帕累托收敛",
  "lines_before": 336, "lines_after": 301, "lines_delta": "-35",
  "tokens_before": "5,057", "tokens_after": "4,334", "tokens_delta": "-723 (-14%)",
  "never_results": [
    { "rule": "NEVER 在 dry_run 不落盘", "violated": false, "na": false, "note": "本次为 hybrid 模式" }
  ],
  "next_steps": [
    "下次评测使用 dynamic 模式以验证改动",
    "把 D10.3 critique evals 标的 2 条 assertion 改写"
  ],
  "change_reason": "本轮改动是 P3 冗余优化（模块概览压缩）"
}
```

> 字段全部可选——缺失时模板会显示"—"或"待主 Agent 填充"占位文本，但 sanity check 仍会通过（不阻断生成）。

---

## 降级策略

| 缺失 | 处理 |
|---|---|
| `results.tsv` | 分数卡用诊断估算值，走势表显示空行 |
| `diagnosis-report.md` | ⑦ 改动详情章节末尾不显示折叠原文 |
| `analysis.json` | 各维度显示"—"，note 显示"待主 Agent 填充" |
| `test-prompts.json` | ④ 覆盖矩阵显示"未找到 test-prompts.json，无法渲染" |
| git 仓库不存在 | ⑦ diff 区域显示"无 git 仓库" |
| `eval-*/` 为空（static 模式）| ⑥ 章节显示 static 说明文本 |
| `eval-*/` 为空（dry_run 模式）| ⑥ 章节显示**红色警告横幅**——主 Agent 没遵守落盘约定 |
| `benchmark.json` 缺失 | ⑥ 章节不显示 benchmark 统计行 |
| `comparison.json` 缺失 | ⑥ 章节不显示 Comparator 盲评区 |
| 任何 JSON 解析错误 | 继续生成，占位符替换为 `—` |

> 任何缺失都不会中断报告生成；但 sanity check 会发出警告（exit code 3）。

---

## NEVER 规则

- **NEVER 将 detailed-report.html 提交到 skill git 仓库** — 报告是评测产物，属于 workspace，不属于 skill
- **NEVER 在报告中内嵌外部 CDN 资源** — 报告必须自包含，可离线查看
- **NEVER 截断 transcript 超过 8,000 字符后不提示** — 截断处必须显示"…（截断，完整内容见文件）"
- **NEVER 用 Write 工具从零拼接 HTML 替代 `templates/full-report.html`**— 必须通过本脚本，或以模板为母版手工替换占位符。手写 HTML 会跳过新章节占位符（`{{COVERAGE_MATRIX}}` / `{{MUST_READ_ITEMS}}` / `{{D_DIMENSIONS_ROWS}}` / `{{EVAL_RESULTS_DETAIL}}`）注入和 sanity check
- **NEVER 在 dry_run 模式下不写 grading.json**— dry_run 不是"免落盘"。落盘 schema 与 dynamic 一致，`grading.json` 必须含 `passed_count` / `total_count` / `expectations[]`，每条 expectation 标 `passed` + `evidence`
- **NEVER 跳过落盘后的 sanity check**— 渲染完报告必须验证：① 无残留 `{{` 占位符 ② 包含 `eval-card` / `static 模式` / `dry_run` 任一标记 ③ 非 static 非 dry_run 模式下 `eval-*/grading.json` 至少存在 1 个；任一失败 exit code 3
- **NEVER 让 sanity check 用 'static 模式' 关键字命中 fallback 文案**— sanity 必须按 `evalModeResolved` 分情形：static/preview 模式才允许出现 static 标识；非 static 模式必须有 ≥1 张真实 `eval-card-header` **且严禁出现** "eval_mode=static" fallback 文案（说明 eval_mode 解析错了）
- **NEVER 跳过 `validate_eval_artifacts.py` 第 1.5 道关**— 子 Agent / dry_run 主 Agent 落盘后到调 `generate-full-report.mjs` 之前必须跑这个 validator，schema 错配类问题（`grading.json` 字段名错 / 缺 `eval_metadata.json` / `manifest` 缺 `eval_mode`）由它前置抓出。`generate-full-report.mjs` 启动时也会自动调一次兜底，**禁止用 `--skip-validator` 绕过**——只在已知 legacy 产物回放时使用
- **NEVER 把 ⑥ 测试数据章节降级为只显示 benchmark 不显示逐条 grading**— benchmark 只给统计，逐条 grading.json 才能看出"哪条用例 baseline 也过 / 哪条全失败"，是判别力诊断的关键
- **NEVER 在 ④ 覆盖矩阵中省略 functional_module 列**— 即使 test-prompts.json 没有 functional_module 字段也要显示 `unassigned` 行，让用户感知到"测试集还没按功能分组"
