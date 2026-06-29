# SKILL.md 30 项自检清单

> 对应 inspect 模块 D0-D10 维度的精简扫读版。每项一行，可在交付前 5 分钟过完。
>
> 详细评分规则见 [quality-dimensions.md](quality-dimensions.md)；官方 best practices 见 [anthropic-best-practices.md](anthropic-best-practices.md)。

---

## 目录

- [Tier 1：Frontmatter（10 项）](#tier-1frontmatter10-项)
- [Tier 2：Body 结构（8 项）](#tier-2body-结构8-项)
- [Tier 3：内容质量（7 项）](#tier-3内容质量7-项)
- [Tier 4：脚本与资源（5 项）](#tier-4脚本与资源5-项)
- [使用方式](#使用方式)

---

## Tier 1：Frontmatter（12 项）

| # | 检查项 | 通过标准 | 对应维度 |
|---|---|---|---|
| 1 | `name` 长度 | ≤ 64 字符 | D1.1 |
| 2 | `name` 格式 | 仅 `[a-z0-9-]`；不含 `anthropic`/`claude` 保留词 | D1.1 |
| 3 | `name` 与目录一致 | frontmatter `name` 完全等于父目录名 | D1.1 |
| 4 | `description` 长度 | ≥ 80 且 ≤ 1024 字符 | D1.9 |
| 5 | `description` 第三人称 | 不含 "I can…"、"You can…"、"Help you…" | D1.13 |
| 6 | `description` 含 **WHAT** | 1-2 句具体功能描述 | D1.2 |
| 7 | `description` 含 **WHEN** | 显式 "Use when..." / "当用户...时" + 触发词列表 | D1.3 |
| 8 | `description` 含 **NEGATIVE BOUNDARIES** ⭐ | 显式 "Do NOT use for..." / "不要用于..." 划反向边界 | D1.10 |
| 9 | `description` **语言匹配** ⭐ | 主体语言匹配用户主流提问语言；多语言场景含双语 trigger words；技术术语保留英文 | D1.14 |
| 10 | `description` **Trigger Words 边界** ⭐ | 只列主入口动作（用户冷启动会单独说的话）；派生菜单动作（收藏 / 导出 / 重搜等）放路由表 | D1.15 |
| 11 | 推荐字段命中 ≥ 1 | `compatibility` / `allowed-tools` 至少 1 项（开源场景再加 `license`） | D1.12 |
| 12 | 命名是动名词或可接受替代 | 优先 `processing-x`；可接受 `x-processing` / `process-x`；避免 `helper`/`utils`/`tools` | D1.11 |

---

## Tier 2：Body 结构（8 项）

| # | 检查项 | 通过标准 | 对应维度 |
|---|---|---|---|
| 11 | Body 行数 | ≤ 500 行硬上限（≤ 300 理想） | D7.1 |
| 12 | 渐进式拆分 | 详细内容拆到 references/ | D7.2 |
| 13 | 加载触发器 | references 有明确加载条件（"see X.md when..."） | D7.3 |
| 14 | 引用深度 = 1 ⭐ | SKILL.md → ref（一层），ref 内不再嵌套引用其他 ref | D7.7（新增） |
| 15 | Long ref 含 TOC | 任何 > 100 行的 ref 文件首部含 Contents 段 | D7.4 |
| 16 | 文档自洽 | 所有交叉引用的文件实际存在 | D7.5 |
| 17 | 配套脚本 | CPU 擅长的逻辑放 scripts/，body 不复述 | D7.6 |
| 18 | 路径分隔符 | 全用正斜杠（`scripts/x.py`），不用反斜杠 | D6.1 |

---

## Tier 3：内容质量（7 项）

| # | 检查项 | 通过标准 | 对应维度 |
|---|---|---|---|
| 19 | 知识增量 | Expert 知识占比 ≥ 60%（无大段基础概念解释） | D0.1 |
| 20 | 无时效性硬编码 | 日期/版本号用 `<details>` 折叠到 "Old patterns" | D6 |
| 21 | 术语一致 | 全文一种说法（不混用 endpoint/URL/route） | D6 |
| 22 | 具体示例 ≥ 3 | 真实 input/output 例子，非 placeholder | D4.6 |
| 23 | 反模式具体 | NEVER 列表每条含 WHY + 失败示例（不是泛泛警告） | D5.2 / D5.3 |
| 24 | Workflow 含 checklist | 多步操作有 `- [ ]` 进度框可勾选 | D3 |
| 25 | Validation loop | 关键操作有"do → validate → fix → retry"循环 | D3.6 |

---

## Tier 4：脚本与资源（5 项）

| # | 检查项 | 通过标准 | 对应维度 |
|---|---|---|---|
| 26 | Script 解决而非 punt | try/except + 默认值，不让 Claude 猜 | D6.1 |
| 27 | 无 voodoo constants | 所有常量含注释说明依据 | D6 |
| 28 | 显式声明依赖 | "Install required: `pip install x`" 而非假设已装 | D6.6 |
| 29 | Error message 自解释 | 错误信息含修复指引（"Add `# Your Name` at top"） | D3.6 |
| 30 | Script 输出结构化 | 返回 JSON / 表格而非自然语言 | D4.1 |

---

## 使用方式

### 方式 A：自检（5 分钟）

```bash
# 直接打开本文件，逐项 ✅/❌ 标注，命中 ≥ 25 项达官方 baseline
```

### 方式 B：调 inspect 跑量化评分

```
"检查这个 skill 质量" → 路由到 modules/inspect.md → 自动跑 D0-D10 维度评分
```

### 方式 C：作为 PR review checklist

任何新 skill 进 registry 前，PR description 贴本 checklist 链接，reviewer 逐项确认。

### 通过线（结合 inspect 评分）

> 总项数 32 项（Tier 1 = 12 + Tier 2 = 8 + Tier 3 = 7 + Tier 4 = 5）

| 状态 | 通过项数 | 含义 | 行动 |
|---|---|---|---|
| **A：可直接交付** | 30-32 | 达官方 best practice baseline | 直接合入 |
| **B：小幅改进** | 26-29 | 有 1-3 项可优化 | reviewer 列出后再合 |
| **C：需补充关键项** | 19-25 | 缺关键 frontmatter 字段 / body 超长 | 作者修复后再 review |
| **D/F：需大幅修改** | < 19 | 多个 Tier 1-2 项失败 | 建议返回 modules/create.md 重做 |

### 与 modules/inspect.md 的关系

| 用途 | 工具 | 耗时 |
|---|---|---|
| 快速自检（人脑跑） | 本 checklist | 5 min |
| 深度量化（自动跑） | `modules/inspect.md` D0-D10 评分 | 1-15 min |
| 触发率/输出质量实测 | `modules/inspect.md` eval_mode=hybrid | 5-15 min |

> 自检通过 ≠ 实际有效。Tier 1-4 都过的 skill 仍要跑 D10.1（test-prompts 实测）确认"加载它真的让 LLM 变好"。
