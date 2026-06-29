# 渐进式披露设计原则

渐进式披露（Progressive Disclosure）是一种信息设计策略，通过分层加载信息来优化上下文使用效率。

## 三层加载系统

### 第 1 层：元数据（始终在上下文）

**内容**：
- `name`：技能名称
- `description`：技能描述（触发机制）

**特点**：
- 约 100-200 字
- 始终加载到上下文
- 决定技能是否触发
- **最关键的设计点**

**设计原则**：
1. 清晰描述技能功能
2. 明确触发条件
3. 包含常见使用场景
4. 避免模糊或过于宽泛

**示例**：
```yaml
name: pdf-processor
description: PDF 文件处理技能。当需要转换 PDF 格式、提取 PDF 文本、合并/分割 PDF、
旋转页面、压缩文件或添加水印时使用。支持批量处理和自定义参数。
```

---

### 第 2 层：SKILL.md 正文（触发后加载）

**内容**：
- 核心工作流程
- 使用指南
- 输出格式
- 最佳实践

**特点**：
- <500 行（约 5k 字）
- 技能触发后加载
- 指导 AI 如何执行任务

**设计原则**：
1. 保持简洁，只包含 essentials
2. 使用清晰的章节结构
3. 提供具体示例
4. 引用参考资料而非复制内容

**组织结构**：
```markdown
# 技能名称

## 何时使用
[触发条件]

## 核心功能
[功能列表]

## 工作流程
[步骤指南]

## 输出格式
[格式规范]

## 参考资料
[链接到第 3 层]
```

---

### 第 3 层：捆绑资源（按需加载）

**内容**：
- `scripts/`：可执行代码
- `references/`：详细文档
- `assets/`：模板和资源文件

**特点**：
- 无大小限制
- AI 判断需要时加载
- 脚本可不加载直接执行

**设计原则**：
1. 在 SKILL.md 中清晰引用
2. 说明何时加载每个文件
3. 避免深度嵌套（一层最佳）
4. 大文件包含目录结构

---

## 设计模式

### 模式 1：高级指南 + 详细参考

**适用**：复杂主题，详细信息不总是需要

**结构**：
```markdown
# 主题

## 快速开始
[基本用法，20% 常见场景]

## 高级功能
- **功能 A**：参见 [advanced-a.md](advanced-a.md)
- **功能 B**：参见 [advanced-b.md](advanced-b.md)
```

**示例**：
```markdown
# PDF 处理

## 快速开始

提取文本：
```python
from pdf_processor import extract_text
text = extract_text("file.pdf")
```

## 高级功能

- **表单填写**：参见 [forms.md](forms.md)
- **数字签名**：参见 [signatures.md](signatures.md)
- **OCR 识别**：参见 [ocr.md](ocr.md)
```

---

### 模式 2：领域特定组织

**适用**：多领域/多框架/多平台支持

**结构**：
```
skill/
├── SKILL.md（概述 + 选择指南）
└── references/
    ├── domain-a.md
    ├── domain-b.md
    └── domain-c.md
```

**SKILL.md 中的导航**：
```markdown
## 选择领域

根据你的需求选择对应领域：

- **财务数据**：读取 [finance.md](references/finance.md)
- **销售数据**：读取 [sales.md](references/sales.md)
- **产品数据**：读取 [product.md](references/product.md)
```

**示例**：云部署技能
```
cloud-deploy/
├── SKILL.md
└── references/
    ├── aws.md
    ├── gcp.md
    └── azure.md
```

---

### 模式 3：条件细节

**适用**：基本功能简单，高级功能复杂

**结构**：
```markdown
# 技能

## 基本用法
[简单场景，80% 使用情况]

## 高级场景

### 场景 A
[描述]
**详细指南**：参见 [scenario-a.md](scenario-a.md)

### 场景 B
[描述]
**详细指南**：参见 [scenario-b.md](scenario-b.md)
```

**示例**：
```markdown
# DOCX 处理

## 基本用法

创建文档：
```python
from docx import Document
doc = Document()
doc.add_paragraph("Hello")
doc.save("output.docx")
```

## 高级场景

### 跟踪更改

**详细指南**：参见 [redlining.md](redlining.md)

### 复杂格式

**详细指南**：参见 [formatting.md](formatting.md)
```

---

## 最佳实践

### ✅ 应该做的

1. **保持 SKILL.md 简洁**
   - 目标：<500 行
   - 只包含核心工作流
   - 详细信息移至参考资料

2. **清晰引用参考资料**
   ```markdown
   - **详细 API**：参见 [api-reference.md](api-reference.md)
   - **示例集合**：参见 [examples.md](examples.md)
   ```

3. **说明何时加载**
   ```markdown
   当用户询问 [具体场景] 时，读取 [文件.md](文件.md)
   ```

4. **使用一致的命名**
   - 文件名清晰描述内容
   - 避免通用名称如 `info.md`
   - 使用 `topic-subtopic.md` 格式

5. **提供目录（大文件）**
   ```markdown
   # 主题
   
   ## 目录
   1. [章节 1](#章节 1)
   2. [章节 2](#章节 2)
   3. [章节 3](#章节 3)
   ```

### ❌ 避免做的

1. **避免深度嵌套**
   - ❌ SKILL.md → ref1.md → ref2.md → ref3.md
   - ✅ SKILL.md → ref1.md, ref2.md, ref3.md

2. **避免重复内容**
   - ❌ SKILL.md 和 references 都有相同内容
   - ✅ 信息只在一个地方，其他地方引用

3. **避免模糊引用**
   - ❌ "参见其他文档"
   - ✅ "参见 [api-reference.md](api-reference.md) 第 3 节"

4. **避免过大文件**
   - ❌ 单个文件 >10k 字
   - ✅ 拆分为多个主题文件

---

## 文件大小指南

| 文件类型 | 建议大小 | 最大大小 | 超大型处理 |
|---------|---------|---------|-----------|
| SKILL.md | <500 行 | <1000 行 | 拆分章节 |
| references/*.md | <300 行 | <500 行 | 拆分子主题 |
| scripts/*.py | <200 行 | <500 行 | 模块化 |

---

## 上下文效率计算

### 示例计算

**场景**：财务分析技能

**方案 A（无渐进式披露）**：
```
SKILL.md: 10000 字（包含所有细节）
每次触发消耗：10000 tokens
```

**方案 B（渐进式披露）**：
```
SKILL.md: 2000 字（核心流程）
references/ 平均加载：3000 字（按需）
每次触发消耗：2000-5000 tokens（节省 50-80%）
```

**节省**：
- 简单查询：80% token 节省
- 中等查询：50% token 节省
- 复杂查询：0% token 节省（但组织更清晰）

---

## 测试渐进式披露

### 检查清单

- [ ] SKILL.md <500 行
- [ ] 参考资料清晰引用
- [ ] 说明何时加载每个文件
- [ ] 无深度嵌套引用
- [ ] 无重复内容
- [ ] 大文件有目录

### 用户测试

1. **触发准确性**：技能是否在正确场景触发？
2. **导航清晰度**：AI 能否找到需要的信息？
3. **输出质量**：输出是否准确完整？
4. **Token 效率**：是否浪费上下文？

---

## 工具支持

### 验证脚本

使用 `package_skill.py` 自动检查：
- SKILL.md 行数
- 引用文件存在性
- 循环引用检测

### 分析工具

```bash
# 分析技能结构
python scripts/analyze_skill.py skill-name/

# 输出：
# - SKILL.md: 350 行 ✓
# - references: 5 个文件 ✓
# - 循环引用：无 ✓
```

---

## 参考资源

- [skill-classification.md](skill-classification.md) - 技能分类
- [trigger-design-guide.md](trigger-design-guide.md) - 触发条件设计
- [development-workflow.md](development-workflow.md) - 开发流程
