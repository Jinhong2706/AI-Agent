# 触发条件设计指南

技能的 `description` 字段是主要触发机制。本指南帮助你设计高效的触发条件。

## 触发机制原理

### 工作原理

1. **技能列表**：技能出现在 AI 的 `available_skills` 列表中
2. **描述匹配**：AI 根据 `name` + `description` 决定是否咨询技能
3. **任务复杂度**：AI 只为无法轻松单独处理的任务咨询技能

### 关键洞察

**重要**：简单查询如"读取这个 PDF"可能不触发技能，即使描述匹配。

**原因**：AI 可以直接用基本工具处理简单任务。

**启示**：
- 评估查询应足够实质性
- 描述应强调复杂/专业化场景
- 不要期望简单查询触发技能

---

## 描述结构

### 推荐结构

```yaml
description: [技能做什么]。当 [触发条件 1]、[触发条件 2]、[触发条件 3] 时使用。
包括 [额外场景 1]、[额外场景 2]。
```

### 元素分解

| 元素 | 说明 | 示例 |
|------|------|------|
| **技能做什么** | 核心功能概述 | "PDF 文件处理技能" |
| **触发条件** | 具体使用场景 | "当需要转换 PDF 格式、提取文本时" |
| **额外场景** | 边缘但重要的情况 | "包括批量处理、自定义参数" |

### 完整示例

```yaml
name: pdf-processor
description: PDF 文件处理技能。当需要转换 PDF 格式（PDF→Word/Excel/图片）、
提取 PDF 文本或元数据、合并多个 PDF、分割 PDF 为多个文件、旋转或裁剪页面、
压缩 PDF 减小文件大小、添加水印或页眉页脚时使用。支持批量处理和自定义参数配置。
```

---

## 触发查询设计

### 评估集构建

创建 20 个评估查询（60% 应触发，40% 不应触发）。

#### 应触发查询（8-10 个）

**覆盖范围**：
- 不同措辞的相同意图
- 正式和随意表达
- 明确和不明确的请求
- 常见和边缘场景

**示例**（PDF 技能）：
```json
[
  {
    "query": "帮我把这个 PDF 转换成 Word 文档，保持格式不变",
    "should_trigger": true
  },
  {
    "query": "ok 所以我有这个 PDF 文件（在我的下载里，叫'Q4 报告.pdf'），
    我需要提取里面的所有文本然后保存为 txt 文件",
    "should_trigger": true
  },
  {
    "query": "我有 50 个 PDF 文件需要批量转换成 PNG 图片，
    每个页面一张图，怎么处理最快？",
    "should_trigger": true
  },
  {
    "query": "这个 PDF 扫描版完全无法复制文字，有什么办法提取内容吗？",
    "should_trigger": true
  }
]
```

#### 不应触发查询（8-10 个）

**设计原则**：
- **接近错过**：共享关键词但实际需要不同东西
- **相邻领域**：相关但不需要此技能
- **模糊请求**：太简单或太宽泛
- **其他工具更合适**：有其他更好的技能

**示例**（PDF 技能）：
```json
[
  {
    "query": "帮我创建一个 PDF 文件，里面写'Hello World'",
    "should_trigger": false,
    "reason": "应该触发文档创建技能，而非处理技能"
  },
  {
    "query": "PDF 是什么格式？",
    "should_trigger": false,
    "reason": "知识问答，不需要操作"
  },
  {
    "query": "打开这个 PDF 文件",
    "should_trigger": false,
    "reason": "简单查看，不需要处理"
  },
  {
    "query": "帮我写一个 Python 脚本来处理 PDF",
    "should_trigger": false,
    "reason": "代码生成请求，不是直接处理"
  }
]
```

---

## 描述优化技巧

### 技巧 1：包含同义词

用户用不同词汇表达相同需求。

**示例**：
```yaml
# 不好
description: 转换 PDF 格式的技能。

# 好
description: PDF 格式转换技能。支持 PDF 转 Word、PDF 转 Excel、PDF 转图片
（PNG/JPG）、PDF 转 HTML、PDF 转文本等多种格式互转。
```

### 技巧 2：明确触发场景

使用"当...时"结构。

**示例**：
```yaml
# 不好
description: 处理财务数据的技能。

# 好
description: 财务分析技能。当需要分析公司财务报表、计算财务比率、
进行财务预测、评估投资价值或解释财务指标时使用。
```

### 技巧 3：包含边缘情况

用户可能用意想不到的方式请求。

**示例**：
```yaml
description: ... 包括处理扫描版 PDF、加密 PDF、大型 PDF（>100MB）、
损坏或不完全的 PDF 文件。
```

### 技巧 4：强调复杂性

区分简单操作和复杂工作流。

**示例**：
```yaml
# 不好
description: 处理 PDF 的技能。

# 好
description: 复杂 PDF 处理工作流。当需要多步骤处理（如：提取→转换→合并）、
条件逻辑（根据内容决定操作）、批量处理（>10 个文件）或自定义参数配置时使用。
```

### 技巧 5：避免过度泛化

太宽泛的描述导致错误触发。

**示例**：
```yaml
# 不好（太宽泛）
description: 处理各种文件的技能。

# 好（具体）
description: 专门处理 PDF 文件的技能。不支持 Word、Excel 或其他格式。
```

---

## 常见触发问题

### 问题 1：触发不足（Under-triggering）

**症状**：应该触发时未触发

**可能原因**：
- 描述太狭窄
- 缺少同义词
- 未覆盖边缘情况

**解决方案**：
```yaml
# 添加同义词
原：转换 PDF 格式
改：转换 PDF 格式、PDF 格式转换、PDF 转 X、X 转 PDF

# 添加场景
原：当需要处理 PDF 时
改：当需要处理 PDF、操作 PDF、对 PDF 进行操作、PDF 相关任务时
```

### 问题 2：过度触发（Over-triggering）

**症状**：不应该触发时触发

**可能原因**：
- 描述太宽泛
- 缺少边界说明
- 关键词过于通用

**解决方案**：
```yaml
# 添加边界
原：处理文件的技能
改：专门处理 PDF 文件。不处理 Word、Excel、图片等其他格式。

# 添加排除
原：当需要创建文档时
改：当需要创建 PDF 文档时。Word 文档创建请使用 docx-creator 技能。
```

### 问题 3：竞争激烈

**症状**：多个技能都可能触发

**可能原因**：
- 技能边界模糊
- 描述重叠

**解决方案**：
```yaml
# 明确分工
技能 A：当需要快速简单处理时使用（<5 个文件，基本操作）
技能 B：当需要复杂工作流时使用（多步骤、条件逻辑、批量处理）
```

---

## 优化流程

### 步骤 1：创建初始描述

基于技能分类和功能列表。

### 步骤 2：构建评估集

20 个查询（12 个应触发，8 个不应触发）。

### 步骤 3：基线测试

测试当前描述的触发率。

### 步骤 4：迭代优化

使用 `run_loop.py` 自动优化：
```bash
python scripts/run_loop.py \
  --eval-set evals/trigger-eval.json \
  --skill-path skills/my-skill \
  --max-iterations 5
```

### 步骤 5：人工审查

审查优化结果，确保语义正确。

### 步骤 6：A/B 测试

在真实使用中比较新旧描述。

---

## 评估指标

### 触发率（Trigger Rate）

**应触发查询的触发比例**：
```
触发率 = 正确触发数 / 应触发查询总数
目标：>90%
```

### 精确率（Precision）

**触发查询中正确触发的比例**：
```
精确率 = 正确触发数 / 总触发数
目标：>85%
```

### F1 分数

**触发率和精确率的调和平均**：
```
F1 = 2 * (触发率 * 精确率) / (触发率 + 精确率)
目标：>0.85
```

---

## 工具支持

### 触发评估集格式

```json
[
  {
    "query": "用户查询",
    "should_trigger": true,
    "notes": "为什么应该触发"
  }
]
```

### 优化脚本

```bash
# 运行优化循环
python scripts/run_loop.py --eval-set evals/trigger-eval.json --skill-path skills/my-skill

# 输出：
# - 每次迭代的触发率/精确率
# - 最佳描述
# - 优化报告
```

### 查看器

```bash
# 生成评估审查 HTML
python -c "
import json
from assets import eval_review_template

with open('evals/trigger-eval.json') as f:
    evals = json.load(f)

html = eval_review_template.render(evals=evals, skill_name='my-skill')
with open('/tmp/eval_review.html', 'w') as f:
    f.write(html)
"
```

---

## 最佳实践清单

### 描述设计

- [ ] 包含核心功能概述
- [ ] 使用"当...时"结构
- [ ] 列出 3-5 个具体触发场景
- [ ] 包含同义词和变体
- [ ] 说明边界和排除情况
- [ ] 长度 100-300 字符
- [ ] 避免技术术语（除非目标用户专业）

### 评估集设计

- [ ] 至少 20 个查询
- [ ] 60% 应触发，40% 不应触发
- [ ] 包含正式和随意表达
- [ ] 包含边缘情况
- [ ] 不应触发查询是"接近错过"
- [ ] 覆盖不同长度和复杂度

### 优化流程

- [ ] 运行至少 3 次迭代
- [ ] 监控训练集和测试集分数
- [ ] 防止过拟合（测试集分数下降时停止）
- [ ] 人工审查最终描述
- [ ] 在真实使用场景测试

---

## 参考资源

- [skill-classification.md](skill-classification.md) - 技能分类
- [progressive-disclosure.md](progressive-disclosure.md) - 渐进式披露
- [development-workflow.md](development-workflow.md) - 开发流程
