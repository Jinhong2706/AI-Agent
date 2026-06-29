# 数据结构定义（v3.0）

本文档定义了深度阅读辅助工具 v3.0 使用的所有数据结构。

## 目录

- [书籍档案结构](#书籍档案结构)
- [五维摘录卡片](#五维摘录卡片)
- [章节框架](#章节框架)
- [六大知识结构模块](#六大知识结构模块)
- [当前在读信息](#当前在读信息)
- [完整示例](#完整示例)
- [版本兼容性](#版本兼容性)

## 书籍档案结构

每本书的档案存储在独立的 JSON 文件中，路径为 `./reading-notes/books/{书名}.json`。

### 数据模型（v3.0）

```json
{
  "book_info": {
    "title": "string (必需) - 书名",
    "author": "string (可选) - 作者",
    "status": "string (必需) - 阅读状态：reading | completed | archived",
    "reading_stage": "string (必需) - 阅读阶段：inspection | interpretation | review | output",
    "created_at": "string (必需) - 创建日期，格式：YYYY-MM-DD",
    "completed_at": "string (可选) - 完成日期，格式：YYYY-MM-DD",
    "tags": "array (可选) - 书籍级别的标签",
    "cover": "string (可选) - 封面图片URL或路径",
    "total_chapters": "number (可选) - 总章节数",
    "total_excerpts": "number (可选) - 总摘录数",
    "version": "string (必需) - 数据版本：v3.0"
  },
  "chapter_framework": {
    "chapters": [
      {
        "chapter_id": "string (必需) - 章节唯一标识",
        "chapter_name": "string (必需) - 章节名称",
        "summary": "string (可选) - 章节摘要",
        "key_points": "array (可选) - 关键要点",
        "excerpt_count": "number (可选) - 摘录数量"
      }
    ],
    "created_at": "string (必需) - 创建时间",
    "updated_at": "string (必需) - 更新时间"
  },
  "excerpts": [
    {
      "id": "string (必需) - 摘录唯一标识",
      "content": "string (必需) - 原文（第一维）",
      "tags": "array (可选) - 标签（第二维）",
      "deep_meaning": "string (可选) - 深层含义（第三维）",
      "application": "string (可选) - 应用（第四维）",
      "question": "string (可选) - 提问（第五维）",
      "chapter_id": "string (可选) - 所属章节ID",
      "chapter_name": "string (可选) - 所属章节名称",
      "created_at": "string (必需) - 创建时间，格式：YYYY-MM-DD HH:MM:SS",
      "source": "string (可选) - 来源：wechat | kindle | manual | import"
    }
  ],
  "knowledge_structure": {
    "concept_index": {
      "concepts": [
        {
          "name": "string (必需) - 概念名称",
          "definition": "string (可选) - 概念定义",
          "first_appearance": "string (可选) - 首次出现章节ID",
          "occurrences": "array (可选) - 出现位置列表"
        }
      ],
      "updated_at": "string - 更新时间"
    },
    "concept_connections": {
      "connections": [
        {
          "from": "string (必需) - 起始概念",
          "to": "string (必需) - 目标概念",
          "relationship": "string (可选) - 关系描述",
          "source_excerpt": "string (可选) - 来源摘录ID"
        }
      ],
      "updated_at": "string - 更新时间"
    },
    "questions": {
      "pending": [
        {
          "id": "string (必需) - 问题ID",
          "question": "string (必需) - 问题内容",
          "source_excerpt": "string (可选) - 来源摘录ID",
          "created_at": "string - 创建时间"
        }
      ],
      "answered": [
        {
          "id": "string (必需) - 问题ID",
          "question": "string (必需) - 问题内容",
          "answer": "string (必需) - 回答内容",
          "answered_at": "string - 回答时间"
        }
      ],
      "updated_at": "string - 更新时间"
    },
    "experiments": {
      "items": [
        {
          "name": "string (必需) - 实验/研究名称",
          "description": "string (可选) - 实验描述",
          "researcher": "string (可选) - 研究者",
          "year": "string (可选) - 年份",
          "source_excerpt": "string (可选) - 来源摘录ID"
        }
      ],
      "updated_at": "string - 更新时间"
    },
    "cross_chapter_links": {
      "links": [
        {
          "chapter_a": "string (必需) - 章节A",
          "chapter_b": "string (必需) - 章节B",
          "relationship": "string (可选) - 关系描述",
          "examples": "array (可选) - 示例列表"
        }
      ],
      "updated_at": "string - 更新时间"
    },
    "reading_output": {
      "summary": "string (可选) - 核心观点总结",
      "applications": "array (可选) - 应用场景列表",
      "knowledge_connections": "array (可选) - 知识关联列表",
      "created_at": "string (可选) - 输出创建时间"
    }
  }
}
```

## 五维摘录卡片

每条摘录包含五个核心要素，构成完整的知识卡片。

### 五维结构说明

| 维度 | 字段 | 说明 | 生成方式 |
|------|------|------|----------|
| 第一维 | content | 原文 | 用户输入，自动识别 |
| 第二维 | tags | 标签 | 智能体分析提取 |
| 第三维 | deep_meaning | 深层含义 | 智能体分析生成 |
| 第四维 | application | 应用 | 智能体分析生成 |
| 第五维 | question | 提问 | 智能体分析生成 |

### 字段说明

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| id | string | 是 | 摘录唯一标识，格式：exc_YYYYMMDDHHMMSS_序号 |
| content | string | 是 | 原文内容 |
| tags | array | 否 | 关键词标签，3-5个 |
| deep_meaning | string | 否 | 深层含义分析 |
| application | string | 否 | 应用建议 |
| question | string | 否 | 延伸提问 |
| chapter_id | string | 否 | 所属章节ID |
| chapter_name | string | 否 | 所属章节名称 |
| created_at | string | 是 | 创建时间，格式：YYYY-MM-DD HH:MM:SS |
| source | string | 否 | 来源：wechat、kindle、manual、import |

## 章节框架

章节框架在检视阅读阶段自动生成，指导后续摘录归位。

### 数据模型

```json
{
  "chapters": [
    {
      "chapter_id": "ch_001",
      "chapter_name": "学而第一",
      "summary": "本篇主要论述学习和修身的重要性",
      "key_points": ["学而时习之", "有朋自远方来", "人不知而不愠"],
      "excerpt_count": 5
    }
  ],
  "created_at": "2024-01-01 10:00:00",
  "updated_at": "2024-01-01 10:00:00"
}
```

### 框架生成规则

1. **自动识别**：基于书籍结构识别章节
2. **智能生成**：为每个章节生成摘要和关键要点
3. **动态更新**：摘录增加时自动更新摘录数量

## 六大知识结构模块

### 1. 核心概念索引（concept_index）

记录书中所有核心概念的索引信息。

```json
{
  "concepts": [
    {
      "name": "仁",
      "definition": "儒家核心思想，指人与人之间相亲相爱的道德规范",
      "first_appearance": "ch_001",
      "occurrences": ["exc_001", "exc_005", "exc_012"]
    }
  ],
  "updated_at": "2024-01-15 10:00:00"
}
```

### 2. 概念联结图（concept_connections）

记录概念之间的关联关系。

```json
{
  "connections": [
    {
      "from": "仁",
      "to": "礼",
      "relationship": "仁是礼的内在精神，礼是仁的外在表现",
      "source_excerpt": "exc_003"
    }
  ],
  "updated_at": "2024-01-15 10:00:00"
}
```

### 3. 待思考问题（questions）

记录需要进一步思考的问题。

```json
{
  "pending": [
    {
      "id": "q_001",
      "question": "仁的不同表现形式之间有何内在联系？",
      "source_excerpt": "exc_001",
      "created_at": "2024-01-10 10:00:00"
    }
  ],
  "answered": [
    {
      "id": "q_002",
      "question": "为什么说仁是儒家的核心思想？",
      "answer": "因为仁贯穿《论语》全书，是其他所有思想的基础...",
      "answered_at": "2024-01-12 14:30:00"
    }
  ],
  "updated_at": "2024-01-15 10:00:00"
}
```

### 4. 关键实验/研究（experiments）

记录书中引用的重要实验或研究。

```json
{
  "items": [
    {
      "name": "棉花糖实验",
      "description": "斯坦福大学Walter Mischel的延迟满足实验",
      "researcher": "Walter Mischel",
      "year": "1972",
      "source_excerpt": "exc_015"
    }
  ],
  "updated_at": "2024-01-15 10:00:00"
}
```

### 5. 跨章联结表（cross_chapter_links）

记录不同章节之间的逻辑关联。

```json
{
  "links": [
    {
      "chapter_a": "ch_001",
      "chapter_b": "ch_005",
      "relationship": "第1章提出的'学习'主题在第5章得到深化",
      "examples": ["exc_001提到了学而时习", "exc_025论述了温故知新"]
    }
  ],
  "updated_at": "2024-01-15 10:00:00"
}
```

### 6. 阅读输出（reading_output）

记录阅读完成后的总结输出。

```json
{
  "summary": "《论语》的核心思想是仁...（300字以上）",
  "applications": [
    "在教育中的应用：因材施教、有教无类",
    "在管理中的应用：以德服人、以身作则"
  ],
  "knowledge_connections": [
    "与《孟子》的关系：孟子继承并发展了孔子的仁政思想",
    "与《大学》的关系：明明德、亲民、止于至善是对仁的扩展"
  ],
  "created_at": "2024-01-20 10:00:00"
}
```

## 当前在读信息

`current.json` 文件记录当前正在阅读的书籍。

### 数据模型

```json
{
  "current_book": "string - 当前在读的书名",
  "current_chapter": "string - 当前阅读章节ID",
  "updated_at": "string - 更新时间，格式：YYYY-MM-DD HH:MM:SS"
}
```

### 示例

```json
{
  "current_book": "论语",
  "current_chapter": "ch_001",
  "updated_at": "2024-01-15 10:30:00"
}
```

## 完整示例（以《论语》为例）

```json
{
  "book_info": {
    "title": "论语",
    "author": "孔子及其弟子",
    "status": "reading",
    "reading_stage": "interpretation",
    "created_at": "2024-01-01",
    "tags": ["儒家思想", "古典文学", "哲学经典"],
    "total_chapters": 20,
    "total_excerpts": 25,
    "version": "v3.0"
  },
  "chapter_framework": {
    "chapters": [
      {
        "chapter_id": "ch_001",
        "chapter_name": "学而第一",
        "summary": "本篇主要论述学习和修身的重要性，包含为人、交友、处世的道理",
        "key_points": ["学而时习之", "有朋自远方来", "人不知而不愠"],
        "excerpt_count": 5
      },
      {
        "chapter_id": "ch_002",
        "chapter_name": "为政第二",
        "summary": "本篇主要论述为政以德的道理",
        "key_points": ["为政以德", "思而不学则殆", "知之为知之"],
        "excerpt_count": 3
      }
    ],
    "created_at": "2024-01-01 10:00:00",
    "updated_at": "2024-01-10 15:30:00"
  },
  "excerpts": [
    {
      "id": "exc_20240101100000_0",
      "content": "子曰：'学而时习之，不亦说乎？有朋自远方来，不亦乐乎？人不知而不愠，不亦君子乎？'",
      "tags": ["学习", "实践", "交友", "君子"],
      "deep_meaning": "孔子提出学习、交友和为人处世的三个境界，强调实践的重要性、珍惜志同道合的朋友、以及君子应有的修养。",
      "application": "在学习中要注重实践和应用，珍惜志同道合的朋友，修炼自己的心胸和修养。",
      "question": "为什么孔子将学习放在第一位，而不是其他？",
      "chapter_id": "ch_001",
      "chapter_name": "学而第一",
      "created_at": "2024-01-01 10:00:00",
      "source": "manual"
    }
  ],
  "knowledge_structure": {
    "concept_index": {
      "concepts": [
        {
          "name": "仁",
          "definition": "儒家核心思想，指人与人之间相亲相爱的道德规范",
          "first_appearance": "ch_001",
          "occurrences": ["exc_20240101100000_0"]
        },
        {
          "name": "君子",
          "definition": "理想的人格典范，具有高尚品德的人",
          "first_appearance": "ch_001",
          "occurrences": ["exc_20240101100000_0"]
        }
      ],
      "updated_at": "2024-01-10 15:30:00"
    },
    "concept_connections": {
      "connections": [
        {
          "from": "学习",
          "to": "实践",
          "relationship": "学习需要通过实践来巩固",
          "source_excerpt": "exc_20240101100000_0"
        }
      ],
      "updated_at": "2024-01-10 15:30:00"
    },
    "questions": {
      "pending": [
        {
          "id": "q_001",
          "question": "为什么孔子将学习放在第一位，而不是其他？",
          "source_excerpt": "exc_20240101100000_0",
          "created_at": "2024-01-01 10:00:00"
        }
      ],
      "answered": [],
      "updated_at": "2024-01-01 10:00:00"
    },
    "experiments": {
      "items": [],
      "updated_at": "2024-01-01 10:00:00"
    },
    "cross_chapter_links": {
      "links": [],
      "updated_at": "2024-01-01 10:00:00"
    },
    "reading_output": null
  }
}
```

## 版本兼容性

### v3.0 向下兼容

v3.0 保持对 v2.0 和 v1.0 数据的兼容性。

### 兼容性规则

#### v2.0 → v3.0 自动升级

| v2.0 字段 | v3.0 映射 | 说明 |
|-----------|-----------|------|
| book_info.status | book_info.status | 直接映射 |
| book_info.reading_stage | book_info.reading_stage | 直接映射 |
| book_info.tags | book_info.tags | 直接映射 |
| excerpts[].content | excerpts[].content | 直接映射 |
| excerpts[].tags | excerpts[].tags | 直接映射 |
| excerpts[].deep_meaning | excerpts[].deep_meaning | 直接映射 |
| excerpts[].application | excerpts[].application | 直接映射 |
| inspection_questions | knowledge_structure.questions.pending | 映射为待思考问题 |

#### 自动补全

| 字段 | 补全方式 |
|------|----------|
| version | 自动设置为 "v3.0" |
| chapter_framework | 自动从 excerpts 分析生成 |
| concept_index | 自动从 excerpts 分析生成 |
| concept_connections | 自动从 excerpts 分析生成 |
| question | 自动从摘录内容生成 |

#### 反向构建（从旧数据生成新结构）

当导入 v1.0/v2.0 数据时，系统自动：

1. 扫描所有摘录，分析生成章节框架
2. 提取核心概念，构建概念索引
3. 分析概念关系，生成概念联结图
4. 从摘录内容生成待思考问题

### 数据验证规则

#### ID 格式

- 摘录 ID：`exc_YYYYMMDDHHMMSS_序号`
- 问题 ID：`q_YYYYMMDDHHMMSS_序号`
- 章节 ID：`ch_XXX`（自动生成）

#### 时间格式

- 日期：`YYYY-MM-DD`
- 时间：`YYYY-MM-DD HH:MM:SS`

#### 状态值

- `reading`：在读
- `completed`：已完成
- `archived`：已归档

#### 阅读阶段值

- `inspection`：检视阅读（生成框架）
- `interpretation`：诠释阅读（创建五维卡片）
- `review`：章节复盘（更新联结）
- `output`：阅读输出（导出知识结构）

## 数据迁移指南

### 从 v2.0 升级

1. 打开 v2.0 格式的书籍档案
2. 系统自动检测版本号
3. 自动添加缺失字段：
   - `chapter_framework`：从摘录分析生成
   - `knowledge_structure`：从摘录分析生成
   - `question`：为每个摘录生成提问
4. 将版本号更新为 "v3.0"

### 从 v1.0 升级

1. 打开 v1.0 格式的书籍档案
2. 系统自动检测版本号
3. 自动添加所有 v3.0 新增字段
4. 基于摘录数据反向构建知识结构
5. 将版本号更新为 "v3.0"

### 导出兼容性

导出功能支持：

- 完整导出（包含所有六模块）
- 精简导出（仅摘录和框架）
- 自定义导出（选择导出内容）
