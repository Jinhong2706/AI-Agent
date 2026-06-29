# Knowledge Safe Merge

一个可公开分享的 WorkBuddy Skill，用来处理“知识库 / 内容库 JSON 增量更新时，既要导入新文章，又不能覆盖历史文章”的场景。

## 这个 Skill 解决什么问题

很多内容站、知识库站或轻量 CMS 都会把文章存成 JSON。
最常见的事故不是“导不进去”，而是：

- 新 JSON 只有 1 篇或几篇文章
- 操作者误以为它是全量数据
- 结果直接覆盖正式数据源
- 历史文章被冲掉

这个 Skill 的目标就是：

- 先分清正式数据源和镜像文件
- 先 dry-run 再正式落盘
- 默认保留历史文章
- 用稳定规则做合并而不是整包覆盖
- 在需要时同步镜像和备份

## 适用项目

适合这类 JSON 结构：

```json
{
  "categories": [],
  "articles": []
}
```

尤其适合：

- 知识库站点
- 内容聚合站
- 静态 JSON 驱动的网站
- 简易内容后台
- 需要定期导入文章数据的个人站/团队站

## 安装方式

### 方式 1：项目级安装
把整个文件夹放到：

```text
项目目录/.workbuddy/skills/knowledge-safe-merge/
```

### 方式 2：用户级安装
把整个文件夹放到：

```text
~/.workbuddy/skills/knowledge-safe-merge/
```

## 目录结构

```text
knowledge-safe-merge/
├── SKILL.md
├── README.md
├── references/
│   └── install-and-share.md
└── scripts/
    └── merge_knowledge_json.py
```

## 最常见的使用方式

### 先预演
```bash
py -3 scripts/merge_knowledge_json.py --current "current.json" --incoming "incoming.json" --dry-run
```

### 再正式合并
```bash
py -3 scripts/merge_knowledge_json.py --current "public/knowledge-data.json" --incoming "incoming.json"
```

### 同步镜像文件
```bash
py -3 scripts/merge_knowledge_json.py --current "public/knowledge-data.json" --incoming "incoming.json" --mirror "knowledge-data.json"
```

## 默认合并规则

1. 优先按 `id` 匹配
2. 如果 `id` 不同，再按“标题 + 日期”匹配
3. 未匹配的文章追加为新文章
4. 正式写入前自动备份旧数据
5. 合并完成后输出统计信息

## 分享给别人怎么做

最简单的方式：

1. 把 `knowledge-safe-merge` 文件夹整体打包
2. 生成 `.skill` 或 `.zip`
3. 发给别人
4. 对方放进自己的 `.workbuddy/skills/` 或某个项目的 `.workbuddy/skills/` 即可

## 公开发布建议

如果你要发到 GitHub 或社群，建议附带：

- 一个最小示例 JSON
- 一段“典型事故说明”
- 一段“安装步骤”
- 一段“3 条使用守则”

## 3 条使用守则

1. 不确认正式数据源前，不要写文件
2. 不跑 dry-run 前，不要覆盖文件
3. 不确认旧文章还在前，不要宣布完成
