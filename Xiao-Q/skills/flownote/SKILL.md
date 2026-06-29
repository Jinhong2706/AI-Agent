---
name: flownote
description: 对话式笔记系统，通过自然对话完成灵感记录、主题管理、智能检索与关联发现；当用户说"记一下"、"查之前记的"、"整理笔记"时自动触发
dependency:
  python:
    - python-dateutil>=2.8.0
---

# FlowNote - 对话式笔记系统

## 任务目标
- 本 Skill 用于：通过自然对话完成笔记记录、检索和整理，实现"零摩擦"的知识管理
- 能力包含：灵感记录、主题卡片管理、智能检索、关联发现、内容整理
- 触发条件：用户说"记一下"/"保存这个观点"、"帮我查之前记的"/"找一下关于XX的笔记"、"整理一下XX主题"

## 前置准备
- 依赖说明：scripts 脚本所需的依赖包
  ```
  python-dateutil>=2.8.0
  ```
- 笔记库初始化：首次使用前，调用初始化脚本创建目录结构
  ```bash
  python scripts/init_notes.py --notes-root ./notes
  ```

## 操作步骤

### 1. 记录笔记

**智能体职责**：
1. 分析用户对话，识别记录意图和内容类型（idea/topic/draft）
2. 提取核心内容、自动生成标题、推荐标签、识别来源
3. 发现与已有笔记的关联关系

**脚本调用**：
```bash
python scripts/save_note.py \
  --notes-root ./notes \
  --type <idea|topic|draft> \
  --title "<标题>" \
  --content "<内容>" \
  --tags "<标签1>,<标签2>" \
  --source "<来源>" \
  --relations "<关联ID1>,<关联ID2>"
```

**格式规范**：详见 [references/format-spec.md](references/format-spec.md)

### 2. 检索笔记

**智能体职责**：
1. 理解用户查询意图，确定检索模式和关键词
2. 对检索结果进行整理、排序和呈现
3. 根据上下文补充相关笔记

**脚本调用**：
```bash
python scripts/search_notes.py \
  --notes-root ./notes \
  --query "<检索词>" \
  --mode <keyword|tag|time> \
  --limit 10
```

**检索模式说明**：
- `keyword`：全文关键词搜索
- `tag`：按标签搜索
- `time`：按时间范围搜索

### 3. 整理笔记

**智能体职责**：
1. 分析整理需求，确定整理范围和目标
2. 调用检索脚本获取相关笔记
3. 将碎片化内容整理成结构化输出
4. 更新或创建主题卡片

**整理输出示例**：
- 主题卡片：将同主题的碎片整理成 `topics/{主题名}.md`
- 时间线整理：按时间顺序汇总某段时间的记录
- 草稿生成：将相关笔记整合成文章草稿

### 4. 关联发现

**智能体职责**：
1. 分析笔记内容，发现语义关联
2. 基于标签、引用、时间等因素判断关联强度
3. 更新笔记的关联关系

**关联类型**：
- 标签关联：共享相同标签
- 引用关联：明确的 wiki-link 引用
- 语义关联：讨论相同主题
- 时间关联：同一时间段记录

### 5. 获取统计

**脚本调用**：
```bash
python scripts/get_stats.py --notes-root ./notes
```

**返回信息**：
- 笔记总数、主题数量
- 标签分布
- 最近活动

## 资源索引

### 必要脚本
| 脚本 | 用途 | 关键参数 |
|------|------|---------|
| [scripts/init_notes.py](scripts/init_notes.py) | 初始化笔记库目录结构 | `--notes-root` |
| [scripts/save_note.py](scripts/save_note.py) | 保存笔记到文件系统 | `--type`, `--title`, `--content`, `--tags` |
| [scripts/search_notes.py](scripts/search_notes.py) | 检索笔记内容 | `--query`, `--mode`, `--limit` |
| [scripts/get_stats.py](scripts/get_stats.py) | 获取笔记库统计信息 | `--notes-root` |

### 参考文档
| 文档 | 内容 | 何时读取 |
|------|------|---------|
| [references/format-spec.md](references/format-spec.md) | Markdown 文件格式规范、index.json 数据结构 | 保存笔记前，确保格式正确 |
| [references/intent-rules.md](references/intent-rules.md) | 意图识别规则、触发词列表、分类决策逻辑 | 分析用户意图时 |

## 注意事项

### 意图识别
- 显式记录："记一下"、"保存"、"这个观点"等触发词
- 隐式记录：对话中包含有价值洞察时，主动询问是否记录
- 查询意图："查一下"、"之前记过"、"找一下"等
- 整理意图："整理"、"汇总"、"生成草稿"等

### 内容提取
- 标题：从内容中提炼核心观点，不超过 20 字
- 标签：推荐 2-5 个相关标签，格式为中文短语
- 来源：识别信息来源（人名、书名、文章名等）
- 关联：查找已有笔记中的相关主题

### 格式一致性
- ideas 文件按周聚合，文件名格式 `YYYY-WXX.md`
- topics 文件按主题命名，使用英文小写和连字符
- 时间戳格式：`YYYY-MM-DD HH:MM`
- 标签格式：`#标签内容`

### 索引维护
- 每次保存笔记后自动更新 `index.json`
- 索引包含：笔记 ID、类型、标题、标签、来源、创建时间、关联
- 删除笔记时需同步更新索引

## 使用示例

### 示例 1：快速记录灵感
```
用户：记一下，今天看到小强说"笔记应该是流动的生产资料"
智能体分析：意图=note，类型=idea，提取内容、标签、来源
调用脚本：save_note.py --type idea --title "关于笔记的本质" --content "笔记应该是流动的生产资料" --tags "笔记方法,知识管理" --source "小强奇谭"
输出：已记录到 ideas/2026-W13.md，标签：#笔记方法 #知识管理
```

### 示例 2：查询历史笔记
```
用户：帮我查一下之前记的关于知识管理的内容
智能体分析：意图=query，关键词="知识管理"
调用脚本：search_notes.py --query "知识管理" --mode keyword --limit 10
智能体整理结果并呈现
```

### 示例 3：整理主题
```
用户：帮我把这周关于笔记方法的思考整理一下
智能体分析：意图=organize，范围=本周，主题=笔记方法
调用脚本：search_notes.py --query "笔记方法" --mode tag --limit 20
智能体整理内容，生成主题卡片
调用脚本：save_note.py --type topic --title "笔记方法" --content "<整理后的内容>"
输出：已整理到 topics/note-taking-methods.md
```
