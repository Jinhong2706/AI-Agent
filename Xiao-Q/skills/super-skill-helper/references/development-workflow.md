# 技能开发完整流程

本指南提供从零开始创建技能的完整开发流程。

## 流程概览

```
1. 理解需求 → 2. 规划内容 → 3. 初始化 → 4. 编辑 → 5. 测试 → 6. 评估 → 7. 优化 → 8. 打包
```

---

## 步骤 1：理解需求

### 目标

清楚理解技能应该做什么，以及如何使用。

### 活动

**用户访谈**（如果为用户创建）：
- "这个技能应该支持什么功能？"
- "你能给出一些使用示例吗？"
- "用户会说什么来触发这个技能？"
- "期望的输出格式是什么？"

**需求分析**（如果是通用技能）：
- 目标用户是谁？
- 解决什么痛点？
- 现有解决方案的不足？
- 成功标准是什么？

### 输出

- 功能列表
- 使用场景（3-5 个）
- 触发短语示例
- 输出格式定义

### 示例

**场景**：创建 PDF 处理技能

**功能列表**：
- PDF 格式转换（→Word, Excel, 图片）
- 文本提取
- 合并/分割
- 旋转/裁剪
- 压缩

**使用场景**：
1. "帮我把这个 PDF 转成 Word"
2. "提取这个 PDF 的所有文字"
3. "合并这 10 个 PDF 文件"

**触发短语**：
- "PDF 转换"
- "提取 PDF 文本"
- "合并 PDF"

**输出格式**：
- 转换后的文件
- 提取的文本文件

---

## 步骤 2：规划内容

### 目标

确定技能需要哪些资源（脚本、参考资料、资产）。

### 活动

**分析每个使用场景**：
1. 如何从头执行这个任务？
2. 什么脚本会有帮助？
3. 什么参考资料会有帮助？
4. 什么资产会有帮助？

**分类到 4 类型**：
- Tool（工具型）：需要脚本
- Workflow（工作流型）：需要流程指南
- Capability（能力型）：需要领域知识
- Scenario（场景型）：需要沟通指南

### 输出

资源清单：
```
scripts/:
  - convert_pdf.py
  - extract_text.py
  - merge_pdfs.py

references/:
  - pdf-formats.md
  - api-reference.md

assets/:
  - templates/
    - conversion-config.json
```

---

## 步骤 3：初始化

### 目标

创建技能目录结构和模板。

### 命令

```bash
python scripts/init_skill.py pdf-processor \
  --path skills/public \
  --resources scripts,references,assets \
  --examples
```

### 输出

```
pdf-processor/
├── SKILL.md (模板)
├── scripts/
│   └── example.py (示例)
├── references/
│   └── example.md (示例)
├── assets/
│   └── template.txt (示例)
└── evals/
    └── evals.json (模板)
```

---

## 步骤 4：编辑

### 目标

实现技能的核心功能。

### 活动

**1. 实现脚本**

替换示例脚本为实际功能：
```python
# scripts/convert_pdf.py
import fitz  # PyMuPDF

def convert_pdf_to_images(pdf_path, output_dir):
    """将 PDF 转换为图片"""
    doc = fitz.open(pdf_path)
    for page_num in range(len(doc)):
        page = doc[page_num]
        pix = page.get_pixmap()
        output_path = f"{output_dir}/page_{page_num+1}.png"
        pix.save(output_path)
    doc.close()
    return True
```

**2. 编写 SKILL.md**

填充模板内容：
```markdown
# PDF Processor

## 何时使用

当需要处理 PDF 文件时使用，包括：
- 格式转换
- 文本提取
- 合并/分割
- 旋转/裁剪

## 工作流程

### 转换流程

1. 确认输入文件格式
2. 选择目标格式
3. 配置转换参数
4. 执行转换
5. 验证输出

### 输出格式

[定义输出格式]
```

**3. 添加参考资料**

创建详细文档：
```markdown
# PDF 格式参考

## 支持的格式

### 输入格式
- PDF 1.4+
- 扫描版 PDF
- 加密 PDF

### 输出格式
- Word (.docx)
- Excel (.xlsx)
- 图片 (.png, .jpg)
```

---

## 步骤 5：测试

### 目标

验证技能按预期工作。

### 活动

**1. 创建测试用例**

编辑 `evals/evals.json`：
```json
{
  "evals": [
    {
      "id": 1,
      "eval_name": "PDF 转 Word",
      "prompt": "帮我把这个 PDF 转换成 Word 文档",
      "expected_output": "生成 .docx 文件，保持格式",
      "files": ["sample.pdf"],
      "assertions": [
        {
          "name": "生成 Word 文件",
          "type": "file_exists",
          "expected": "output.docx"
        }
      ]
    }
  ]
}
```

**2. 手动测试**

```bash
# 运行技能
python -c "
from scripts.convert_pdf import convert_pdf_to_word
convert_pdf_to_word('sample.pdf', 'output.docx')
"

# 验证输出
ls -la output.docx
```

**3. 记录问题**

创建 `testing-notes.md`：
```markdown
# 测试笔记

## 问题

1. 大文件（>50MB）转换失败
2. 扫描版 PDF 需要 OCR

## 待改进

- 添加文件大小检查
- 集成 OCR 功能
```

---

## 步骤 6：评估

### 目标

量化评估技能性能。

### 活动

**1. 运行测试用例**

```bash
# 为每个测试用例生成子代理
# （使用 sessions_spawn 或手动运行）
```

**2. 评分结果**

使用 `agents/grader.md` 指南：
```bash
# 为每个运行创建 grading.json
{
  "eval_id": 1,
  "expectations": [
    {
      "text": "生成 Word 文件",
      "passed": true,
      "evidence": "找到文件：output.docx"
    }
  ]
}
```

**3. 聚合结果**

```bash
python scripts/aggregate_benchmark.py \
  workspace/iteration-1 \
  --skill-name pdf-processor
```

**4. 生成查看器**

```bash
python eval-viewer/generate_review.py \
  workspace/iteration-1 \
  --skill-name pdf-processor \
  --benchmark workspace/iteration-1/benchmark.json
```

---

## 步骤 7：优化

### 目标

基于评估结果改进技能。

### 活动

**1. 分析失败用例**

阅读 `benchmark.md`：
```markdown
## 分析洞察

❌ 技能未显示改进

**最差表现**: PDF 转 Word (0% 通过率)

原因：
- 脚本未处理复杂格式
- 缺少字体映射
```

**2. 阅读用户反馈**

```bash
cat workspace/iteration-1/feedback.json
```

```json
{
  "reviews": [
    {
      "run_id": "eval-1-with_skill",
      "feedback": "表格格式丢失了"
    }
  ]
}
```

**3. 实施改进**

```python
# 改进脚本
def convert_pdf_to_word(pdf_path, output_path):
    # 添加字体映射
    font_map = load_font_map()
    
    # 添加表格处理
    tables = extract_tables(pdf_path)
    
    # ... 其他改进
```

**4. 迭代**

重复步骤 5-7 直到满意。

---

## 步骤 8：优化描述

### 目标

提高技能触发准确性。

### 活动

**1. 创建触发评估集**

```json
[
  {"query": "帮我把 PDF 转成 Word", "should_trigger": true},
  {"query": "创建一个 PDF 文件", "should_trigger": false}
]
```

**2. 运行优化循环**

```bash
python scripts/run_loop.py \
  --eval-set evals/trigger-eval.json \
  --skill-path skills/pdf-processor \
  --max-iterations 5
```

**3. 应用最佳描述**

自动更新 SKILL.md frontmatter。

---

## 步骤 9：打包

### 目标

创建可分发的 .skill 文件。

### 活动

**1. 验证技能**

```bash
python scripts/package_skill.py skills/pdf-processor
```

**输出**：
```
🔍 验证技能：skills/pdf-processor
============================================================
✓ 找到必需文件：SKILL.md
✓ 技能名称：pdf-processor
✓ 技能描述：180 字符
✓ 找到 3 个 Python 脚本
✓ 找到 2 个参考文档
✓ 找到 5 个测试用例

============================================================
✅ 验证通过
```

**2. 打包**

```bash
python scripts/package_skill.py skills/pdf-processor --output ./dist
```

**输出**：
```
📦 打包技能：pdf-processor
输出文件：./dist/pdf-processor.skill
  ✓ 添加：SKILL.md
  ✓ 添加：scripts/convert_pdf.py
  ✓ 添加：scripts/extract_text.py
  ...

✅ 打包成功!
文件：./dist/pdf-processor.skill
大小：125.50 KB
```

---

## 完整时间线

| 步骤 | 预计时间 | 关键输出 |
|------|---------|---------|
| 1. 理解需求 | 1-2 小时 | 功能列表、使用场景 |
| 2. 规划内容 | 1 小时 | 资源清单 |
| 3. 初始化 | 10 分钟 | 目录结构 |
| 4. 编辑 | 4-8 小时 | 工作技能 |
| 5. 测试 | 2-4 小时 | 测试用例、问题列表 |
| 6. 评估 | 2-4 小时 | benchmark.json、用户反馈 |
| 7. 优化 | 2-4 小时 | 改进版本 |
| 8. 优化描述 | 1-2 小时 | 优化后的 description |
| 9. 打包 | 30 分钟 | .skill 文件 |

**总计**：15-30 小时（取决于复杂度）

---

## 质量检查清单

### 发布前检查

- [ ] 所有测试用例通过（>80% 通过率）
- [ ] 用户反馈积极（无严重问题）
- [ ] SKILL.md <500 行
- [ ] 描述优化完成（触发率 >90%）
- [ ] 无验证错误
- [ ] 文档完整（README、示例）
- [ ] 错误处理完善
- [ ] 性能可接受（响应时间 <30s）

---

## 常见陷阱

### ❌ 陷阱 1：跳过测试

**问题**：直接发布未测试的技能

**解决**：始终运行至少 3 个测试用例

### ❌ 陷阱 2：忽视用户反馈

**问题**：只关注定量指标

**解决**：仔细阅读每条用户反馈

### ❌ 陷阱 3：过度优化

**问题**：为 1% 改进花费 10 小时

**解决**：设定边际收益阈值（如<5% 改进则停止）

### ❌ 陷阱 4：描述过短

**问题**：description <50 字符

**解决**：目标 100-300 字符，覆盖足够场景

---

## 参考资源

- [skill-classification.md](skill-classification.md) - 技能分类
- [progressive-disclosure.md](progressive-disclosure.md) - 渐进式披露
- [trigger-design-guide.md](trigger-design-guide.md) - 触发条件设计
- [schemas.md](schemas.md) - JSON 架构定义
