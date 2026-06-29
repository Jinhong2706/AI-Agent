# COSMIC 脚本 API 参考

> **版本**：v1.0.0
> **配套 scripts/**：`extract_requirements.py` / `generate_cosmic.py` / `validate_cosmic.py`

---

## 1. extract_requirements.py

### 功能
从 .docx 概要设计说明书中提取需求矩阵与功能描述，输出为 JSON。

### 用法
```bash
python extract_requirements.py <docx_path> [--output <json_path>]
```

### 参数
| 参数 | 必需 | 说明 |
|:-----|:-----|:-----|
| `docx_path` | 是 | 概要设计说明书 .docx 文件路径 |
| `--output` / `-o` | 否 | 输出 JSON 文件路径，不传则打印到 stdout |

### 输出 JSON 结构
```json
{
  "document": "/path/to/spec.docx",
  "requirements_matrix": {
    "一级需求": "宽带开户装机流程优化需求",
    "二级需求": {"一级需求": "二级需求1"},
    "三级需求": {"二级需求1": ["三级功能点1", "三级功能点2"]}
  },
  "function_descriptions": {
    "三级功能点1": ["段落1", "段落2", "..."]
  }
}
```

### 依赖
- python-docx >= 1.0

### 示例
```bash
python scripts/extract_requirements.py "C:/Desktop/概要设计.docx" -o extracted.json
```

---

## 2. generate_cosmic.py

### 功能
端到端从 .docx 生成 COSMIC .xlsx 表格。**v1.0 提供骨架**：包含 .xlsx 写入、配比规划、合并、ΣCFP 计算等基础设施；子过程拆解（F/G/H/I 列填充）由 LLM 辅助完成。

### 用法
```bash
python generate_cosmic.py <docx_path> <output_xlsx_path>
```

### 参数
| 参数 | 必需 | 说明 |
|:-----|:-----|:-----|
| `docx_path` | 是 | 概要设计说明书 .docx 路径 |
| `output_xlsx_path` | 是 | 输出 .xlsx 路径 |
| `--intermediate` | 否 | 中间提取结果 JSON 路径 |

### 内部 API（供编程调用）

#### `classify_data_movement(desc: str) -> str`
根据子过程描述字符串判定 G 列数据移动类型（E/R/W/X）。

```python
from scripts.generate_cosmic import classify_data_movement
classify_data_movement("解析装维APP退单接口入参")  # → 'E'
classify_data_movement("通过字典编码查询退单原因表")  # → 'R'
classify_data_movement("保存退单信息至回访表")  # → 'W'
classify_data_movement("反馈退单结果至装维APP")  # → 'X'
```

#### `allocate_reuse(n: int) -> list`
按 2:7:1 配比规划 n 行的复用度分配。

```python
from scripts.generate_cosmic import allocate_reuse
allocate_reuse(35)  # → ['新增', ..., '复用', ..., '利旧', ...]
```

#### `write_xlsx(output_path, data_rows, level1_name) -> float`
将业务数据行写入 .xlsx 文件，返回 ΣCFP。

```python
from scripts.generate_cosmic import write_xlsx
data_rows = [
    {
        'A': '宽带开户装机流程优化需求',
        'B': '发起者：业务服务接口；接收者：装维APP',
        'C': '新增扩容工单装维退单流程',
        'D': '接口调用',
        'E': '查询扩容工单装维退单原因',
        'F': '获取扩容工单装维退单原因查询入参',
        'G': 'E',
        'H': '退单原因查询入参',
        'I': '字典编码、版本号、查询条件',
        'J': '利旧',
        'K': 0,
    },
    # ...更多行
]
sum_cfp = write_xlsx('output.xlsx', data_rows, '宽带开户装机流程优化需求')
print(f'ΣCFP = {sum_cfp}')
```

### 依赖
- python-docx >= 1.0
- openpyxl >= 3.1

---

## 3. validate_cosmic.py

### 功能
对生成的 COSMIC .xlsx 表格执行 15 项合规性校验，输出校验报告。

### 用法
```bash
python validate_cosmic.py <xlsx_path> [--source <docx_path>] [--output <report.json>]
```

### 参数
| 参数 | 必需 | 说明 |
|:-----|:-----|:-----|
| `xlsx_path` | 是 | COSMIC 表格 .xlsx 路径 |
| `--source` / `-s` | 否 | 原始 .docx 路径（用于原文一致性校验） |
| `--output` / `-o` | 否 | 校验报告 JSON 路径 |

### 15 项校验清单
| # | 名称 | 检查内容 | 强约束级别 |
|:-:|:-----|:---------|:-----------|
| 0 | check_step0_fenodian | 前置分点扫描 | 🔴 |
| 1 | check_step1_yuanwen | 原文一致性 | 🔴 |
| 2 | check_step2_jiegou | 结构合规性 | 🔴 |
| 3 | check_step3_gongneng | 功能匹配 | 🔴 |
| 4 | check_step4_duliang | 度量规则（G/J/K/D） | 🔴 |
| 5 | check_step5_shuzhi | 数值准确性（ΣCFP） | 🔴 |
| 6 | check_step6_bitian | 必填项 | 🔴 |
| 7 | check_step7_zifuchuan | 字符长度（F/H/I ≤ 30） | 🔴 |
| 8 | check_step8_fengxianci | 风险词/禁用过程 | 🔴 |
| 9 | check_step9_shujuyidong | 数据移动类型 | 🔴 |
| 10 | check_step10_fuyongdu | 复用度占比 | 🔴 |
| 11 | check_step11_hebing | 单元格合并 | 🟡 |
| 12 | check_step12_shujuzu | 数据组唯一性 | 🔴 |
| 13 | check_step13_shujushuxing | 数据属性 | 🔴 |
| 14 | check_step14_pingxing | 平行判定穷尽 | 🔴 |

### 输出报告 JSON 结构
```json
{
  "xlsx_path": "C:/Desktop/cosmic.xlsx",
  "row_count": 35,
  "checks": [
    {
      "name": "check_step0_fenodian",
      "passed": true,
      "errors": [],
      "note": "需对照原文手动确认"
    },
    {
      "name": "check_step10_fuyongdu",
      "passed": false,
      "errors": ["新增占比 16.7% 不在 20%~25% 区间"],
      "counts": {"新增": 7, "复用": 26, "利旧": 9},
      "new_ratio": 0.167
    }
  ],
  "overall_passed": false
}
```

### 示例
```bash
python scripts/validate_cosmic.py "C:/Desktop/cosmic.xlsx" --source "C:/Desktop/spec.docx" -o report.json
```

### 返回码
- `0`：所有校验通过
- `1`：存在错误

---

## 4. 端到端工作流示例

```bash
# Step 1: 提取需求
python scripts/extract_requirements.py "C:/Desktop/概要设计.docx" -o extracted.json

# Step 2: LLM 拆解（人工/AI 辅助）
# 读取 extracted.json，按 cosmic-rules.md 拆分子过程，得到 data_rows.json
# data_rows.json 格式: [{"A": "...", "B": "...", ...}, ...]

# Step 3: 生成 .xlsx
python -c "
import json
from scripts.generate_cosmic import write_xlsx
data = json.load(open('data_rows.json', encoding='utf-8'))
write_xlsx('output.xlsx', data, '宽带开户装机流程优化需求')
"

# Step 4: 校验
python scripts/validate_cosmic.py "output.xlsx" --source "C:/Desktop/概要设计.docx" -o report.json

# 查看报告
cat report.json
```
