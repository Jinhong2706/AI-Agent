# Skill 改造清单（已有 Skill 升级用）

> **本文档定位**：已有 Skill 的快速改造速查表，针对中文项目环境的"实用补丁集"。
>
> **权威指南**请阅读 [anthropic-best-practices.md](anthropic-best-practices.md)（5 篇官方资料的精华汇总）。
> **30 项自检清单**请用 [skill-md-checklist.md](skill-md-checklist.md)。
> **反模式细节**请查 [anti-patterns.md](anti-patterns.md)。

---

## 何时用本文档

- ✅ 你已经有一个跑得起来的 Skill，要做"小幅升级"或"补差"
- ✅ 你在 inspect 报告里看到 D1/D7 维度扣分，想快速对标修复
- ❌ 从零创建 Skill → 走 `modules/create.md` 完整流程
- ❌ 全面诊断重构 → 走 `modules/diagnose.md` 棘轮迭代

---

## 改造清单（按优先级排序）

### 🔴 P0 — 影响触发率（不修 Skill 永远激活不了）

| 修复项 | 检查方式 | 修复动作 |
|---|---|---|
| description 超 1024 字符 | `wc -c` frontmatter description 段 | 删冗余技术细节、精简关键词列表 |
| description 第一人称（"I can…"） | grep 检查 | 改为 "Processes…"、"Generates…" 第三人称 |
| description 缺 negative boundaries | 搜 "Do NOT use for" / "不要用于" 是否存在 | 加 "Do NOT use for: [3-5 个易混场景]" / "不要用于：..." |
| description 缺 trigger words | 数列出的具体 keyword | 列 5-10 个用户可能用的具体说法 |
| **中文用户场景用全英文 description** ⭐ | 看用户主流提问语言 vs description 语言 | 主体改中文，trigger 词中英双语，技术术语（PDF/OOXML 等）保留英文 |

### 🟡 P1 — 影响维护与扩展（不修后续会越来越难改）

| 修复项 | 检查方式 | 修复动作 |
|---|---|---|
| SKILL.md body > 500 行 | `wc -l SKILL.md` | 拆分到 references/，body 只留路由和原则 |
| reference 嵌套引用（ref → ref） | grep references/ 内的 `[xxx](xxx.md)` | 把 ref 内的引用全部上提到 SKILL.md |
| 长 ref（> 100 行）缺 TOC | 检查文件首部 | 加 `## Contents` 段落 |
| 术语混用（API endpoint / URL / route） | grep 全文 | 选一个词全文替换 |
| 时效性硬编码（"在 2025-08 之前用 v1"） | grep 日期 | 用 `<details>` 折叠到"Old patterns"段 |

### 🟢 P2 — 提升信任 / 复用性

| 修复项 | 检查方式 | 修复动作 |
|---|---|---|
| frontmatter 缺 `compatibility` | grep | 加 `compatibility: Requires Python 3.10+...` |
| frontmatter 缺 `allowed-tools` | grep | 列实际用到的工具白名单 |
| frontmatter 缺 `license`（**仅开源场景**） | grep | 公开发布到 skill 市场的加 SPDX 标识符；内部 / 项目级 skill 省略 |
| 命名是模糊词（helper/utils/tools） | 检查目录名 | 改为动名词 + 领域词（如 `processing-pdfs`） |
| 缺 Gotchas 段 | 看 SKILL.md 章节 | 列 3-5 条"Agent 自己摸不到的坑"|

---

## description 改造示例库

| 场景 | description（精简后）|
|------|------------|
| PDF 处理 | Extracts text and tables from PDF files, fills forms, merges documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction. Do NOT use for: image OCR, scanned documents requiring vision, or generating new PDFs from scratch. |
| 代码审查 | Reviews code for bugs, security issues, and best practices. Use when reviewing pull requests, checking code quality, or performing security audits. Do NOT use for: code generation, refactoring suggestions, or test case authoring. |
| Azure 部署 | Builds and deploys Azure infrastructure using Bicep templates. Use when creating Azure resources, managing environments, or writing infrastructure-as-code. Do NOT use for: AWS/GCP deployment, Kubernetes manifests, or local Docker setup. |
| 数据分析 | Analyzes Excel spreadsheets, creates pivot tables, generates charts. Use when analyzing tabular data, .xlsx files, or generating data reports. Do NOT use for: real-time data streaming, SQL database queries, or PDF-formatted data extraction. |

---

## Skill 类型与自由度对照

| Skill 类型 | 自由度 | SKILL.md 侧重 | scripts/ 侧重 |
|-----------|--------|--------------|--------------|
| 执行型（pdf-editor） | 低 | 极简，指向脚本 | 核心逻辑全在此 |
| 流程型（deploy-tool） | 中 | 分支判断、异常处理 | 确定性步骤 |
| 规范型（code-style） | 高 | 标准和约束（核心价值） | 验证脚本 |
| 认知型（architecture-guide） | 高 | 设计哲学（核心价值） | 几乎不需要 |

详细自由度匹配规则见 [anthropic-best-practices.md §自由度三档校准](anthropic-best-practices.md#自由度三档校准)。

---

## 改造完成后的验证

```
1. 调 inspect.md → eval_mode=static → 看 D1/D7/D0 是否全 ≥ 70
2. 调 inspect.md → eval_mode=hybrid → 看 D10.1 实测有没有提升
3. 用 [skill-md-checklist.md](skill-md-checklist.md) 30 项自检 → 通过 ≥ 25 项达 baseline
```
