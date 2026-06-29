# test-prompts 设计与确认（共用模块）

> 将 `inspect.md` D.0 与 `diagnose.md` Step 0 中**几乎完全相同**的"测试集定位 + 展示 + 丰富度诊断 + 用户确认"抽出来共用，避免双份维护错配。

---

## 谁会引用这个文件

| 引用方 | 触发时机 | 调用形态 |
|---|---|---|
| `modules/inspect.md` D.0 | 进入 dynamic / hybrid / blind_hybrid 评测前 | "走 `references/test-prompts-design.md` 完成测试集准备" |
| `modules/diagnose.md` Step 0 | 棘轮迭代开始前（任何 eval_mode） | 同上 |

> **关键**：用户从 inspect 跳进 diagnose（点 `[1] 进入棘轮`）时，inspect 阶段已确认过的测试集**不应再让用户确认一遍**——见下方「同会话跳过」逻辑。

---

## 完整流程（5 步，强 STOP × 1）

```
Step P.1  定位测试集     → workspace 优先 → skill 目录兼容 → 不存在则进入设计
Step P.2  展示内容       → 把每条 prompt + judgements 完整列出
Step P.3  丰富度诊断     → 自动跑覆盖率/category/判别力检查
Step P.4  STOP 用户确认  → [1] 直接用 / [2] 追加场景 / [3] 优化 judgement / [4] 重写
Step P.5  写回 + 落 hash → workspace/test-prompts.json + 当前会话 manifest
```

> **同会话跳过**：调用方在调用本流程前传入 `last_confirm_hash`（manifest 记录的上次确认时的 SHA-256）。若本次计算的 hash 与 last_confirm_hash 一致，**跳过 Step P.2-P.4**，直接进入 P.5（仅刷新时间戳）。

---

## Step P.1 — 定位测试集

按以下优先级查找，**找到即停**：

| 优先级 | 查找位置 | 处理 |
|:-:|---|---|
| 1（标准位置）| `<workspace>/test-prompts.json` | 进入 P.2 |
| 2（旧位置兼容）| `<skill_dir>/test-prompts.json` | 提示「建议迁移到 workspace」，迁移后进入 P.2 |
| 3（不存在）| — | 走自动设计模式（[auto-judgement-generator.md](./auto-judgement-generator.md) 7 阶段流程）或手动模式，写入 workspace 后进入 P.2 |

> 用户提供文本片段（非目录）时，动态评测无法跑——降级为 `eval_mode=structure_only`，跳过 P.2-P.5。

---

## Step P.2 — 展示内容（**必须完整列出**）

```
📋 即将使用以下测试集运行评测 — 共 {N} 条 prompt（覆盖 {M} 个功能模块 × {K} 类场景）

  #1 [{functional_module} · {scenario} · {priority}] "{prompt 前 60 字}..."
     Judgements（{count} 条 · 含 {category 分布}）：
     · A 加载  ─ {judgement-A1}
     · B 工作流 ─ {judgement-B1}
     · C 输出   ─ {judgement-C1}
     · E 准则   ─ {judgement-E1}
     Negative judgements（{count} 条）：
     · {negative-1}

  #2 ...（逐条展示，不截断）

──────────────────────────────────────────────
📊 覆盖矩阵概览：

| 功能模块 | happy | complex | edge | negative | error | 命中 category |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| ... 详见下方 ...

──────────────────────────────────────────────
🔍 丰富度诊断结果：{充分 ✅ / 不足 ⚠️，列出不足项}
```

---

## Step P.3 — 丰富度诊断（自动跑，结果嵌在 P.2 输出）

> 复用 [auto-judgement-generator.md Phase 3.5](./auto-judgement-generator.md) 的完整性 checklist 同款标准。

### 检查项一览

| # | 检查项 | 最低标准 | 推荐标准 | 不通过的标注 |
|:-:|---|---|---|---|
| 1 | 功能覆盖率 | 100%（每个 module 至少 1 条 prompt） | — | `⚠️ 缺 {module} 模块覆盖` |
| 2 | P0 场景覆盖率 | ≥ 95% | 100% | `⚠️ 缺 {N} 个 P0 单元格` |
| 3 | 场景类型分布 | happy + complex 各 ≥ 1 | 5 类至少 3 类有覆盖 | `⚠️ 缺 {scenario} 场景` |
| 4 | Prompt 数量 | ≥ 2 | ≥ 3 | `⚠️ 条数偏少` |
| 5 | 每条 P0 prompt 的 judgement 数 | ≥ 4 | ≥ 5 | `⚠️ #{id} judgement 过少` |
| 6 | Judgement 具体性 | 无「输出是否合理」类通用判断 | 每条指向可观测行为 | `⚠️ #{id} judgement 过于通用` |
| 7 | 判别力 | 每条至少 1 条 skill 专属 | 每条 ≥ 2 条专属 | `⚠️ #{id} 缺 skill 专属检查` |
| 8 | Negative judgements | 至少 1 条 P0 prompt 有 | 每个 scope 都有 | `⚠️ 缺 negative 防偏置` |
| 9 | **必填字段完整性** | 每条用例同时含 `functional_module`（非空）/ `scenario`（5 类枚举之一）/ `priority`（P0/P1/P2）/ `prompt`（完整文本） | — | `⚠️ #{id} 缺 functional_module` / `⚠️ #{id} scenario 值不合法` ↳ **后果**：`generate-full-report.mjs` 覆盖矩阵显示 `unassigned`，每个 eval-card 显示"无 prompt 记录"，且 `promptByScenario` 查找失效导致 `functional_module` 标签丢失 |

> **注 #9**：此检查在 `auto-judgement-generator.md` Phase 5 写入时已内建，但**手动编写 test-prompts.json** 时没有自动保障，因此在 P.3 中强制检查。`scenario` 合法值：`happy_path` / `complex` / `edge` / `negative` / `error`（与脚本 `SCENARIOS` 枚举一致）。

### 不通过时的标注样式

把不足项汇总后追加到 P.4 菜单的 [1] 选项旁：

```
  [1] 直接使用，开始评测  ⚠️ 测试集存在以下不足，棘轮决策可信度偏低：
      · 仅 {N} 条 prompt（建议 ≥ 3）
      · 缺 install/edge 场景覆盖
      · #3 prompt 仅有 2 条 judgement（建议 ≥ 4）
      → 建议先选 [2] 或 [3] 补充后再继续；选 [1] 可接受风险直接继续
```

> 用户选 [1]（含警告）后，在后续报告与 results.tsv 中持续标注 `test_set_quality=insufficient({不足项 1-3 条})`。

---

## Step P.4 — STOP 用户确认（**强制，不可跳过**）

```
接下来如何处理这份测试集？

  [1] 直接使用，开始评测（默认）{若有 ⚠️ 标注追加风险提示}
  [2] 追加新场景（AI 分析 SKILL.md 后生成补充 prompt，按覆盖矩阵的缺位置补 P0 优先）
  [3] 优化现有 judgements（改写泛化判断为具体可观测检查）
  [4] 完全重写（保留旧版备份后重新设计）
```

> **STOP**：等用户明确选 [1]/[2]/[3]/[4] 后才继续，不得默认选 [1] 自动进入下一阶段。

| 选项 | 行为 |
|:-:|---|
| [1] | 进入 P.5 |
| [2] | 调 [auto-judgement-generator.md](./auto-judgement-generator.md) Phase 2.5 单格补全模式：用户告知补哪个 (功能, 场景) 单元格，AI 生成 prompt + judgements，再次 STOP 等用户确认后 merge 写入 |
| [3] | 调 Grader critique evals（`agents/grader.md` §critique 模式）：逐条标"太宽松/太严苛/缺位置指引"，用户逐条 approve/reject 重写 |
| [4] | 备份旧版到 `test-prompts.bak.{ts}.json`，从 0 走 `auto-judgement-generator.md` 7 阶段流程 |

---

## Step P.5 — 写回 + 落 hash

```python
import hashlib, json, datetime

def confirm_test_prompts(workspace, test_prompts):
    # 1. 写回标准位置
    target = workspace / "test-prompts.json"
    target.write_text(json.dumps(test_prompts, indent=2, ensure_ascii=False))

    # 2. 计算内容 hash
    content = target.read_bytes()
    sha = hashlib.sha256(content).hexdigest()[:16]

    # 3. 写入 manifest（让下次同会话调用可以跳过 P.2-P.4）
    manifest = read_manifest(workspace)
    manifest["test_prompts_confirmation"] = {
        "hash": sha,
        "confirmed_at": datetime.datetime.utcnow().isoformat() + "Z",
        "scenario_count": len(test_prompts),
        "p0_count": sum(1 for p in test_prompts if p.get("priority") == "P0"),
        "completeness_pass": True,    # 由 P.3 决定
    }
    write_manifest_atomic(workspace, manifest)
    return sha
```

---

## 同会话跳过逻辑

### 触发条件（**必须全部满足**才能跳过 P.2-P.4）

| # | 条件 | 检查方式 |
|:-:|---|---|
| 1 | manifest 中存在 `test_prompts_confirmation.hash` | 读 manifest |
| 2 | 当前 `test-prompts.json` 内容 hash 与 `manifest.test_prompts_confirmation.hash` 一致 | sha256 计算 |
| 3 | 上次确认时间 < 当前 session 启动时间 | 同会话内连续调用 |
| 4 | 调用方与上次相同 OR 上次为 inspect 当前为 diagnose（"评测后进诊断"链路）| 比对 manifest.last_caller |

### 跳过时的简化输出

```
✓ 测试集与本会话上次确认一致（hash {prefix}），跳过重复展示
  · {N} 条 prompt · 覆盖 {M} 个功能模块 × {K} 类场景 · 上次确认于 {ts}
  · 如需重新审查测试集，输入 "review test-prompts" 强制重展
```

> 用户输入 "review test-prompts" / "查看测试集" 等关键词时，**强制走完整 P.2-P.4**，忽略 hash 一致。

### 不能跳过的情况（即使 hash 一致）

- 跨会话调用（manifest 中的 confirmation timestamp 早于 session_lock.acquired_at）
- test-prompts.json 内容被外部修改（hash 不一致）
- 用户输入显式要求重新审查
- inspect → diagnose 之间用户做过 Step 0 自动模式生成新 prompt（hash 必然变）

---

## NEVER

- **NEVER 跳过 P.2 直接进 P.5** — 即使是同会话跳过分支，也要打印简化的"测试集已确认"提示，让用户随时能要求重展
- **NEVER 让 inspect 和 diagnose 各自维护一份测试集展示模板** — 必须引用本文件，否则两边不一致会让用户困惑
- **NEVER 把测试集 hash 写到 test-prompts.json 自身** — hash 是评测元数据，应在 manifest.yaml 中维护
- **NEVER 在 hash 一致时跳过丰富度诊断** — 即使 hash 一致，也要把 P.3 的诊断结果一行式简报展示出来（让用户感知风险）
- **NEVER 把跳过逻辑藏成"静默降级"** — 跳过时输出明确的"✓ 测试集已确认"行，不能闷声进入下一步
