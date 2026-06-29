---
name: knowledge-safe-merge
description: "当用户要更新、导入、合并或迁移知识库/内容库 JSON 数据，并且需要保留历史文章、防止整包覆盖时使用。适用于带有 articles 数组的内容站、知识库站点、静态 CMS 或简易后台。"
---

# Knowledge Safe Merge

## 适用场景
当用户提出以下需求时，应优先使用本 Skill：

- “把新的知识库 JSON 合并进去，不要覆盖旧文章”
- “导入一批新文章，但历史数据必须保留”
- “更新 content/articles 数据源，先预演再落盘”
- “把旧站内容迁到新站，避免重复或误覆盖”
- “做一个安全的 JSON 导入/更新 SOP”

本 Skill 主要面向这类数据结构：

```json
{
  "categories": [],
  "articles": []
}
```

其中 `articles` 是核心，`categories` 可选。

---

## 核心原则

1. **先识别正式数据源**：先找出唯一 authoritative file，再动手。
2. **默认 incoming JSON 可能只是增量**：除非已明确验证是全量，否则禁止直接覆盖。
3. **先 dry-run，后正式写入**：先看新增/更新/未变化/合并后总数。
4. **先备份，再落盘**：正式写入前保留可回滚版本。
5. **保留历史文章优先**：合并的默认目标是“旧文章不丢”。
6. **上线后必须校验**：验证 JSON 接口和页面都正常。

---

## 标准工作流

### 第一步：识别文件角色
先明确这几个概念：

- **正式数据源**：站点或系统真正读取的 JSON 文件
- **镜像文件**：同步副本、人工备份、导出快照
- **incoming 文件**：这次新收到、准备导入的 JSON

如果用户没有说清楚，先查项目代码或配置，确认谁才是正式数据源。

### 第二步：检查数据结构
至少确认：

- 根对象是否为 JSON object
- 是否存在 `articles` 数组
- 每篇文章是否具备最基本的 `title` 和 `content`
- `id` 是否稳定可用
- 是否存在 `date`、`catId` 等辅助字段

如果结构差异很大，不要强行合并，先给出适配方案。

### 第三步：优先使用项目现有脚本
如果项目里已经有稳定的合并脚本、后台导入逻辑或数据管道，**优先复用项目已有方案**。

只有在项目没有现成方案，或用户明确希望快速落地一个通用方案时，才使用本 Skill 自带脚本：

```bash
py -3 scripts/merge_knowledge_json.py --current "正式数据源.json" --incoming "新数据.json" --dry-run
```

### 第四步：确认合并规则
默认规则：

1. 优先按 `id` 匹配
2. 如果 `id` 不同，再按“`title + date`”匹配
3. 未匹配到的文章追加为新文章
4. 合并结果按日期倒序、再按 `id` 排序

### 第五步：正式写入前备份
正式写入前必须备份当前正式文件。

如果使用自带脚本，可通过 `--backup-dir` 指定备份目录；未指定时会自动备份到正式数据源同级目录下的 `.knowledge-backups/`。

### 第六步：正式执行
典型命令：

```bash
py -3 scripts/merge_knowledge_json.py --current "public/knowledge-data.json" --incoming "new.json" --mirror "knowledge-data.json"
```

如需显式输出到另一个文件：

```bash
py -3 scripts/merge_knowledge_json.py --current "current.json" --incoming "incoming.json" --output "merged.json"
```

### 第七步：写入后校验
至少确认：

- 最终文章总数符合预期
- 新文章能查到
- 关键旧文章仍存在
- 如果涉及网站上线，校验线上 JSON 接口和内容页

---

## 推荐命令模板

### 仅预演
```bash
py -3 scripts/merge_knowledge_json.py --current "current.json" --incoming "incoming.json" --dry-run
```

### 正式覆盖正式数据源
```bash
py -3 scripts/merge_knowledge_json.py --current "public/knowledge-data.json" --incoming "incoming.json"
```

### 正式写入并同步镜像文件
```bash
py -3 scripts/merge_knowledge_json.py --current "public/knowledge-data.json" --incoming "incoming.json" --mirror "knowledge-data.json"
```

### 写入自定义输出文件
```bash
py -3 scripts/merge_knowledge_json.py --current "current.json" --incoming "incoming.json" --output "merged.json"
```

---

## 严格禁止

- 禁止把来源不明、数量明显偏少的 JSON 直接覆盖正式数据源
- 禁止把镜像文件、导出文件、测试文件误当成正式数据源
- 禁止跳过 dry-run 就直接上线，除非用户明确接受风险
- 禁止在没有备份的情况下覆盖生产内容数据
- 禁止只看“新文章出现了”就结束，必须确认“旧文章还在”

---

## 产出要求
处理完后，至少要给出：

1. 本次识别出的正式数据源路径
2. incoming 文件路径
3. dry-run 或正式执行统计：新增 / 更新 / 未变化 / 合并后总数
4. 是否已备份
5. 是否同步镜像
6. 是否完成线上校验（若有）

---

## 资源
- 详细安装与分享说明：`references/install-and-share.md`
- 通用合并脚本：`scripts/merge_knowledge_json.py`
- 对外介绍文档：`README.md`
