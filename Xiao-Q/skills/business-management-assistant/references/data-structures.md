# 数据结构规范

## 目录
- [流程文件 (workflow.md)](#流程文件-workflowmd)
- [业务框架文件 (business_framework.md)](#业务框架文件-business_frameworkmd)
- [路径文件 (paths/*.md)](#路径文件-pathsmd)
- [任务文件 (tasks.md)](#任务文件-tasksmd)
- [信号日志文件 (signals/*.md)](#信号日志文件-signalsmd)
- [决策日志 (decisions.log)](#决策日志-decisionslog)
- [配置文件 (config.yaml)](#配置文件-configyaml)
- [验证规则与约束](#验证规则与约束)

## 概览
本文档定义了对话式业务管理工具（BMA）所有数据文件的格式规范。所有文件采用 Markdown + YAML Frontmatter 结构，便于 AI 读写和人工编辑。

## 流程文件 (workflow.md)

### 格式定义
```yaml
---
name: onboarding_workflow
version: 1.0
created: YYYY-MM-DD
last_updated: YYYY-MM-DD
total_progress: 0%  # 整体完成百分比
---

# 使用流程

## 阶段一：[阶段名称]
- **状态**: pending/in-progress/completed/skipped
- **进度**: [已完成数]/[总步骤数] 步骤
- **预计时间**: [时间描述]

### 步骤 1.1：[步骤名称]
- **状态**: pending/in-progress/completed/skipped
- **描述**: [步骤描述]
- **操作**: [操作内容或命令]
- **提示**: [执行提示]
- **对话示例**:
  ```
  [对话示例]
  ```
- **检查条件**: [检查条件，验证是否完成]
- **关联文件**: [相关文件路径，可选]

### 步骤 1.2：[步骤名称]
...
```

### 完整示例
```yaml
---
name: onboarding_workflow
version: 1.0
created: 2026-04-12
last_updated: 2026-04-12
total_progress: 0%
---

# 使用流程

## 阶段一：系统初始化
- **状态**: pending
- **进度**: 0/2 步骤
- **预计时间**: 5分钟

### 步骤 1.1：创建数据目录
- **状态**: pending
- **描述**: 创建 sdp_data 数据目录结构
- **操作**: mkdir -p ./sdp_data/paths ./sdp_data/signals
- **提示**: 此步骤将在当前工作目录创建数据存储目录
- **对话示例**:
  ```
  智能体：正在创建数据目录...

  ✅ 已创建目录：
  - ./sdp_data/
  - ./sdp_data/paths/
  - ./sdp_data/signals/
  ```
- **检查条件**: 检查 ./sdp_data 目录是否存在
- **关联文件**: ./sdp_data/

### 步骤 1.2：初始化核心文件
- **状态**: pending
- **描述**: 创建配置文件和日志文件
- **操作**: 创建 config.yaml、decisions.log、tasks.md
- **提示**: 这些文件存储系统配置和决策记录
- **对话示例**:
  ```
  智能体：正在初始化核心文件...

  💡 提示: 此步骤将创建以下配置文件：
  - config.yaml: 系统配置文件
  - decisions.log: 决策记录日志
  - tasks.md: 任务管理文件

  ✅ 已完成：创建所有核心文件
  ```
- **检查条件**: 检查 ./sdp_data/config.yaml 是否存在
- **关联文件**: ./sdp_data/config.yaml

## 阶段二：构建初始业务框架
- **状态**: pending
- **进度**: 0/4 步骤
- **预计时间**: 15-30分钟

### 步骤 2.1：描述业务背景
- **状态**: pending
- **描述**: 描述你的业务背景和核心目标
- **操作**: 对话引导，收集业务信息
- **提示**: 清晰的业务背景有助于后续规划
- **对话示例**:
  ```
  智能体：请描述你的业务背景和核心目标？

  用户：我们要做面向个人用户的对话式H5生成工具，目标是成为该领域的首选方案

  智能体：✅ 已记录业务背景
  ```
- **检查条件**: business_framework.md 包含业务目标描述
- **关联文件**: ./sdp_data/business_framework.md

### 步骤 2.2：定义差异化价值
- **状态**: pending
- **描述**: 定义业务的核心差异化价值
- **操作**: 对话引导，收集价值主张
- **提示**: 差异化价值是竞争的关键
- **对话示例**:
  ```
  智能体：请定义该业务的核心差异化价值？

  用户：无需专业设计能力，通过自然语言生成可直接使用的H5页面

  智能体：✅ 已记录差异化价值
  ```
- **检查条件**: business_framework.md 包含预期价值字段
- **关联文件**: ./sdp_data/business_framework.md

### 步骤 2.3：设定成功指标
- **状态**: pending
- **描述**: 设定量化的成功指标
- **操作**: 对话引导，收集指标信息
- **提示**: 具体的指标有助于跟踪进度
- **对话示例**:
  ```
  智能体：请设定成功指标（如用户量、营收、市场份额）？

  用户：6个月内达到10万注册用户，月活30%，付费转化率5%

  智能体：✅ 已记录成功指标
  ```
- **检查条件**: business_framework.md 包含成功指标字段
- **关联文件**: ./sdp_data/business_framework.md

### 步骤 2.4：配置监控关键词
- **状态**: pending
- **描述**: 配置外部信号监控关键词
- **操作**: 对话引导，收集关键词列表
- **提示**: 关键词用于搜索相关的外部信号
- **对话示例**:
  ```
  智能体：请提供需要监控的外部信号关键词？

  用户：AI生成、H5工具、低代码、个人开发者、竞品动态

  智能体：✅ 已配置监控关键词
  ```
- **检查条件**: config.yaml 包含关键词配置
- **关联文件**: ./sdp_data/config.yaml
```

### 验证规则
- YAML 前言必须包含：name、version、created、last_updated、total_progress
- 阶段状态值必须是：pending、in-progress、completed、skipped 之一
- 步骤状态值必须是：pending、in-progress、completed、skipped 之一
- total_progress 必须是 0-100 的百分比
- 每个阶段必须包含：状态、进度、预计时间
- 每个步骤必须包含：状态、描述、操作、提示、检查条件

### 流程状态更新规则
- 开始阶段：将阶段状态改为 in-progress
- 完成阶段：将阶段状态改为 completed，更新 total_progress
- 跳过阶段：将阶段状态改为 skipped
- 开始步骤：将步骤状态改为 in-progress
- 完成步骤：将步骤状态改为 completed，更新阶段进度
- 跳过步骤：将步骤状态改为 skipped

## 业务框架文件 (business_framework.md)

### 格式定义
```yaml
---
last_updated: YYYY-MM-DD
---

# 业务目标：[目标描述]

## 方向 D[编号]：[方向名称]
- **状态**: active/paused/closed
- **背景**: [业务背景描述]
- **预期价值**: [价值主张]
- **成功指标**: [量化指标]
- **外部信号关键词**: [关键词1, 关键词2, ...]
- **关联路径**: P[编号], P[编号], ...
- **创建时间**: YYYY-MM-DD
- **更新时间**: YYYY-MM-DD
```

### 完整示例
```yaml
---
last_updated: 2026-04-12
---

# 业务目标：成为对话式H5生成工具的首选个人方案

## 方向 D001：对话式界面生成
- **状态**: active
- **背景**: 针对非技术用户，通过自然语言描述生成H5页面
- **预期价值**: 降低H5开发门槛，提升创作效率10倍
- **成功指标**: 3个外部用户完成H5生成，用户满意度>4.5/5
- **外部信号关键词**: 百度秒哒, 对话式应用开发, LLM UI生成
- **关联路径**: P001, P003
- **创建时间**: 2026-04-01
- **更新时间**: 2026-04-12

## 方向 D002：自然语言UI设计研究
- **状态**: paused
- **背景**: 研究基于自然语言的UI设计方法
- **预期价值**: 探索下一代交互范式
- **成功指标**: 产出3个设计原型，获得2个外部反馈
- **外部信号关键词**: NLWeb, 微软NLUI, 自然语言界面
- **关联路径**: P002
- **创建时间**: 2026-03-20
- **更新时间**: 2026-04-10
```

### 验证规则
- `last_updated` 必须为 YYYY-MM-DD 格式
- 每个方向必须包含所有必需字段（状态、背景、预期价值、成功指标、关键词、关联路径、创建时间）
- 状态值必须是：active、paused、closed 之一
- 方向编号格式：D001, D002, ...（3位数字，从001开始）
- 关联路径必须以逗号+空格分隔

## 路径文件 (paths/*.md)

### 格式定义
```yaml
---
id: P[编号]
name: [路径名称]
direction_id: D[编号]
status: exploring/in-progress/paused/closed
owner: [负责人姓名]
start_date: YYYY-MM-DD
end_date: YYYY-MM-DD
priority: high/medium/low
last_updated: YYYY-MM-DD
---

# [路径名称]

## 概览
- **所属方向**: D[编号]
- **负责人**: [负责人]
- **时间范围**: [开始日期] - [结束日期]
- **优先级**: [优先级]

## 背景
[路径背景描述]

## 里程碑
### M1: [里程碑名称]
- **截止日期**: YYYY-MM-DD
- **状态**: pending/in-progress/completed/failed
- **完成时间**: YYYY-MM-DD（若已完成）

### M2: [里程碑名称]
...

## 依赖关系
- **前置路径**: P[编号], P[编号], ...
- **后置路径**: P[编号], P[编号], ...

## 关键决策点
### [日期] Go/No-Go 决策
- **决策结果**: Go/No-Go
- **背景**: [决策背景]
- **理由**: [决策理由]
- **后续行动**: [行动项]

## 经验教训
- [记录的经验教训、风险、改进建议]

## 关联任务
T[编号], T[编号], ...
```

### 完整示例
```yaml
---
id: P001
name: 对话式UI生成
direction_id: D001
status: in-progress
owner: 张三
start_date: 2026-04-01
end_date: 2026-06-30
priority: high
last_updated: 2026-04-12
---

# 对话式UI生成

## 概览
- **所属方向**: D001
- **负责人**: 张三
- **时间范围**: 2026-04-01 - 2026-06-30
- **优先级**: high

## 背景
开发基于LLM的对话式UI生成引擎，支持用户通过自然语言描述生成H5页面。

## 里程碑
### M1: 原型验证
- **截止日期**: 2026-04-15
- **状态**: completed
- **完成时间**: 2026-04-14

### M2: 核心功能开发
- **截止日期**: 2026-05-30
- **状态**: in-progress

### M3: 用户测试
- **截止日期**: 2026-06-20
- **状态**: pending

## 依赖关系
- **前置路径**: 无
- **后置路径**: P003

## 关键决策点
### 2026-04-10 技术选型决策
- **决策结果**: Go
- **背景**: 选择LLM模型和UI框架
- **理由**: GPT-4 API性能稳定，Vue3生态成熟
- **后续行动**: 基于GPT-4+Vue3开发原型

## 经验教训
- 初期对LLM响应时间预估不足，需要增加流式渲染
- UI组件库选择需要考虑移动端适配

## 关联任务
T001, T002, T003, T004
```

### 验证规则
- YAML 前言必须包含所有必需字段（id、name、direction_id、status、owner、start_date、end_date、priority、last_updated）
- 路径编号格式：P001, P002, ...（3位数字，从001开始）
- 状态值必须是：exploring、in-progress、paused、closed 之一
- 优先级值必须是：high、medium、low 之一
- 日期格式必须为 YYYY-MM-DD

## 任务文件 (tasks.md)

### 格式定义
```yaml
---
last_updated: YYYY-MM-DD
---

# 任务清单

## 待处理任务 (pending)
### T[编号]: [任务名称]
- **所属路径**: P[编号]
- **描述**: [任务描述]
- **负责人**: [负责人]
- **截止日期**: YYYY-MM-DD
- **优先级**: high/medium/low
- **状态**: pending

## 进行中任务 (in-progress)
...

## 已完成任务 (completed)
...

## 阻塞任务 (blocked)
...
```

### 完整示例
```yaml
---
last_updated: 2026-04-12
---

# 任务清单

## 待处理任务 (pending)
### T005: 集成流式渲染
- **所属路径**: P001
- **描述**: 为LLM响应添加流式渲染功能，提升用户体验
- **负责人**: 李四
- **截止日期**: 2026-04-20
- **优先级**: high
- **状态**: pending

## 进行中任务 (in-progress)
### T003: 开发UI组件库
- **所属路径**: P001
- **描述**: 开发移动端适配的UI组件库
- **负责人**: 李四
- **截止日期**: 2026-05-10
- **优先级**: medium
- **状态**: in-progress

### T006: 测试原型功能
- **所属路径**: P002
- **描述**: 对NLUI原型进行功能测试
- **负责人**: 王五
- **截止日期**: 2026-04-15
- **优先级**: medium
- **状态**: in-progress

## 已完成任务 (completed)
### T001: 技术选型研究
- **所属路径**: P001
- **描述**: 调研LLM模型和UI框架，输出选型报告
- **负责人**: 张三
- **截止日期**: 2026-04-05
- **优先级**: high
- **状态**: completed
- **完成时间**: 2026-04-04

### T002: 搭建开发环境
- **所属路径**: P001
- **描述**: 配置开发环境、初始化项目
- **负责人**: 张三
- **截止日期**: 2026-04-07
- **优先级**: medium
- **状态**: completed
- **完成时间**: 2026-04-06

## 阻塞任务 (blocked)
### T007: 集成第三方支付
- **所属路径**: P004
- **描述**: 集成支付宝支付SDK
- **负责人**: 赵六
- **截止日期**: 2026-04-18
- **优先级**: high
- **状态**: blocked
- **阻塞原因**: 等待支付审核通过
```

### 验证规则
- 任务按状态分组：pending、in-progress、completed、blocked
- 任务编号格式：T001, T002, ...（3位数字，从001开始）
- 每个任务必须包含：所属路径、描述、负责人、截止日期、优先级、状态
- 状态值必须与分组一致

## 信号日志文件 (signals/*.md)

### 格式定义
```yaml
---
date: YYYY-MM-DD
total_signals: [信号总数]
high_relevance: [高关联度数量]
---

# 外部信号日志 - [日期]

## 高关联度信号
### 信号 [编号]
- **来源**: [来源网站/渠道]
- **发布时间**: YYYY-MM-DD
- **关键词**: [匹配的关键词]
- **关联方向**: D[编号], D[编号], ...
- **摘要**: [信号内容摘要]
- **影响评估**: [影响分析]
- **建议行动**: [建议的响应措施]

## 中关联度信号
...

## 低关联度信号
...
```

### 完整示例
```yaml
---
date: 2026-04-12
total_signals: 5
high_relevance: 2
---

# 外部信号日志 - 2026-04-12

## 高关联度信号
### 信号 001
- **来源**: 百度AI官网
- **发布时间**: 2026-04-11
- **关键词**: 百度秒哒
- **关联方向**: D001
- **摘要**: 百度秒哒发布企业级API，支持对话式应用开发
- **影响评估**: 直接竞品发布新功能，可能影响D001的市场定位
- **建议行动**: 1) 进行竞品功能对比分析；2) 暂缓路径P001的下个里程碑；3) 评估是否需要调整产品策略

### 信号 002
- **来源**: OpenAI Blog
- **发布时间**: 2026-04-10
- **关键词**: LLM UI生成
- **关联方向**: D001
- **摘要**: OpenAI发布新的UI生成模型，支持更复杂的界面设计
- **影响评估**: 技术方向变化，P001的技术选型可能需要调整
- **建议行动**: 评估新模型是否更适合当前需求

## 中关联度信号
### 信号 003
- **来源**: TechCrunch
- **发布时间**: 2026-04-11
- **关键词**: 对话式应用开发
- **关联方向**: D001
- **摘要**: 行业报告显示对话式应用需求增长30%
- **影响评估**: 市场趋势利好，验证了业务方向的合理性
- **建议行动**: 无需立即行动，继续观察

## 低关联度信号
### 信号 004
- **来源**: 36Kr
- **发布时间**: 2026-04-10
- **关键词**: AI工具
- **摘要**: AI工具市场整体增长
- **影响评估**: 间接影响，作为背景信息
- **建议行动**: 记录即可

### 信号 005
- **来源**: Hacker News
- **发布时间**: 2026-04-09
- **关键词**: UI生成
- **摘要**: 开源UI生成工具讨论热度上升
- **影响评估**: 低关联度，作为参考
- **建议行动**: 记录即可
```

### 验证规则
- 文件命名格式：YYYY-MM-DD_signal_log.md
- 信号必须按关联度分组：高、中、低
- 每个信号必须包含：来源、发布时间、关键词、关联方向、摘要、影响评估、建议行动

## 决策日志 (decisions.log)

### 格式定义
```
[时间戳] | [决策类型] | [背景] | [决策内容] | [预期结果] | [影响范围]
```

### 完整示例
```
2026-04-12 09:30:00 | PATH_STATUS_CHANGE | 百度秒哒发布企业级API，直接竞品升级 | 将P001状态从in-progress改为paused，暂停下一步开发 | 避免资源浪费，等待竞品分析完成 | 路径P001及其关联任务T003-T005
2026-04-12 10:15:00 | PATH_CREATE | 评估百度秒哒的竞争威胁 | 创建新路径P005用于竞品分析，负责人王五，优先级high | 2周内完成竞品分析，支持后续决策 | 新增路径P005，关联方向D001
2026-04-10 14:20:00 | MILESTONE_GO | P001里程碑M1原型验证通过，用户反馈良好 | 执行Go决策，进入里程碑M2核心功能开发 | 6月30日前完成核心功能开发 | 路径P001，任务T003-T007
2026-04-08 11:00:00 | TASK_REASSIGN | 李四因其他项目繁忙，无法按时完成T006 | 将T006从李四转派给王五，截止日期延长3天 | 确保测试工作按时完成 | 任务T006，路径P002
2026-04-05 16:45:00 | DIRECTION_CREATE | 市场调研显示自然语言UI设计需求增长 | 创建新方向D002：自然语言UI设计研究 | 探索下一代交互范式，为产品长期发展做准备 | 新增方向D002，创建路径P002
```

### 决策类型分类
- `DIRECTION_CREATE`: 创建业务方向
- `DIRECTION_STATUS_CHANGE`: 修改方向状态
- `DIRECTION_CLOSE`: 关闭业务方向
- `PATH_CREATE`: 创建实现路径
- `PATH_STATUS_CHANGE`: 修改路径状态
- `PATH_MERGE`: 合并路径
- `PATH_SPLIT`: 拆分路径
- `PATH_CLOSE`: 关闭路径
- `MILESTONE_GO`: 里程碑Go决策
- `MILESTONE_NO_GO`: 里程碑No-Go决策
- `TASK_REASSIGN`: 任务重新指派
- `TASK_PRIORITY_CHANGE`: 任务优先级调整

### 验证规则
- 每行一个决策，使用竖线分隔字段
- 时间戳格式：YYYY-MM-DD HH:MM:SS
- 决策类型必须使用预定义的分类
- 所有字段不能为空

## 配置文件 (config.yaml)

### 格式定义
```yaml
# 监控配置
monitoring:
  enabled: true
  frequency: daily  # daily/weekly
  sources:
    - name: [来源名称]
      type: [类型：web_search/rss/manual]
      keywords: [关键词列表]
      url: [URL，如果是RSS]
  global_keywords: [全局关键词]

# 业务框架配置
framework:
  review_cycle: weekly  # daily/weekly/biweekly
  active_directions_limit: 5  # 同时激活的方向数量限制

# 通知配置
notifications:
  high_relevance_alert: true
  milestone_due_reminder: 3  # 提前几天提醒
  task_overdue_alert: true

# 数据保留
retention:
  signal_logs_days: 90  # 信号日志保留天数
  decision_logs_keep: true  # 是否永久保留决策日志
```

### 完整示例
```yaml
# 监控配置
monitoring:
  enabled: true
  frequency: daily
  sources:
    - name: 百度动态
      type: web_search
      keywords:
        - 百度秒哒
        - 百度AI
    - name: OpenAI Blog
      type: web_search
      keywords:
        - GPT
        - ChatGPT
        - OpenAI
    - name: 行业新闻
      type: web_search
      keywords:
        - 对话式应用
        - AI工具
        - H5生成
  global_keywords:
    - AI
    - 人工智能
    - 对话式

# 业务框架配置
framework:
  review_cycle: weekly
  active_directions_limit: 5

# 通知配置
notifications:
  high_relevance_alert: true
  milestone_due_reminder: 3
  task_overdue_alert: true

# 数据保留
retention:
  signal_logs_days: 90
  decision_logs_keep: true
```

### 验证规则
- 必须包含所有顶级配置节（monitoring、framework、notifications、retention）
- frequency 值必须是：daily、weekly、biweekly 之一
- review_cycle 值必须是：daily、weekly、biweekly 之一

## 验证规则与约束

### 通用约束
1. **日期格式**：所有日期必须使用 YYYY-MM-DD 格式
2. **时间戳格式**：日志文件的时间戳必须使用 YYYY-MM-DD HH:MM:SS 格式
3. **编号规则**：
   - 方向编号：D001, D002, ...（3位数字）
   - 路径编号：P001, P002, ...（3位数字）
   - 任务编号：T001, T002, ...（3位数字）
4. **状态枚举**：
   - 方向状态：active、paused、closed
   - 路径状态：exploring、in-progress、paused、closed
   - 任务状态：pending、in-progress、completed、blocked
   - 里程碑状态：pending、in-progress、completed、failed
5. **优先级枚举**：high、medium、low

### 文件一致性约束
1. **业务框架与路径一致性**：
   - business_framework.md 中的关联路径必须实际存在于 paths/ 目录
   - 路径文件中的 direction_id 必须在 business_framework.md 中定义
2. **路径与任务一致性**：
   - 路径文件中列出的关联任务必须在 tasks.md 中存在
   - 任务文件中的所属路径必须在 paths/ 目录中存在
3. **依赖关系一致性**：
   - 路径的前置/后置路径必须实际存在
   - 不允许循环依赖（需要智能体检测）

### 操作约束
1. **原子化操作**：所有写操作必须遵循"读取→修改→写回"流程
2. **时间戳更新**：每次修改文件必须更新 last_updated 字段为当前日期
3. **决策记录**：重大操作（创建/关闭方向或路径、状态变更）必须记录到 decisions.log
4. **版本兼容性**：所有文件格式向前兼容，新增字段可选

### 数据完整性约束
1. **必填字段**：
   - business_framework.md：每个方向必须包含所有必需字段
   - paths/*.md：YAML 前言的所有字段必填
   - tasks.md：每个任务必须包含所有必需字段
   - signals/*.md：每个信号必须包含所有必需字段
2. **引用完整性**：
   - 所有 ID 引用（方向ID、路径ID、任务ID）必须有效
   - 删除实体前必须检查依赖关系
3. **逻辑一致性**：
   - 路径状态为 closed 时，其关联任务不应有 in-progress 状态
   - 方向状态为 closed 时，其关联路径不应有 in-progress 状态
